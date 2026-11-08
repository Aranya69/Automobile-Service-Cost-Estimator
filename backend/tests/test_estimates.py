from datetime import date

import pytest

from app.ai import agent
from app.ai.schemas import AgentDecision
from app.extensions import db
from app.models import Estimate, Part, PartPrice
from scripts.import_prices import load_mapping, sync_catalogue

from .conftest import csrf_headers, register


class FakeModel:
    """Stands in for Gemini. Returns the queued decisions in order."""

    def __init__(self, *decisions, error=None):
        self.decisions = list(decisions)
        self.error = error
        self.calls = []

    def with_structured_output(self, schema):
        assert schema is AgentDecision
        return self

    def invoke(self, messages):
        self.calls.append(messages)
        if self.error:
            raise self.error
        return self.decisions.pop(0)


@pytest.fixture
def use_model(monkeypatch):
    def install(model):
        monkeypatch.setattr(agent, "get_chat_model", lambda: model)
        return model

    return install


@pytest.fixture
def car(logged_in, app):
    parts = sync_catalogue(load_mapping())
    for value in (2500, 3200, 4000, 4600, 6400):
        db.session.add(PartPrice(
            part_id=parts["Front brake pads (set)"].id, car_model="Axio", quality_tier="oem",
            price_bdt=value, source="garage", collected_on=date(2026, 10, 12), verified=True,
        ))
    db.session.commit()
    res = logged_in.post(
        "/api/vehicles",
        json={"model": "Axio", "year": 2016, "engine_cc": 1500, "odometer_km": 84000},
        headers=csrf_headers(logged_in),
    )
    return res.get_json()["vehicle"]


def estimate(client, car, **body):
    payload = {"vehicle_id": car["id"], "problem_text": "brake e awaj kore", "garage_tier": "workshop"}
    payload.update(body)
    return client.post("/api/estimates", json=payload, headers=csrf_headers(client))


def test_ai_estimate_is_priced_and_saved(logged_in, car, use_model):
    use_model(FakeModel(AgentDecision(
        action="estimate", job_codes=["BRAKE_PADS_F", "MADE_UP_JOB"],
        explanation="Brake pad khoye geche.", safety_warnings=["Brake check korun."],
    )))
    res = estimate(logged_in, car)
    assert res.status_code == 201
    data = res.get_json()["estimate"]

    assert data["method"] == "ai"
    assert [j["code"] for j in data["jobs"]] == ["BRAKE_PADS_F"]  # unknown code dropped
    assert data["total_min"] == 2500 + 700
    assert data["total_max"] == 6400 + 1200
    assert data["confidence"] == "high"
    assert data["explanation"] == "Brake pad khoye geche."
    assert data["warnings"][0] == "Brake check korun."
    assert any("affects safety" in w for w in data["warnings"])  # added by us, not the AI
    assert db.session.get(Estimate, data["id"]).user_id is not None


def test_agent_asks_a_question_first(logged_in, car, use_model):
    model = use_model(FakeModel(
        AgentDecision(action="ask", question="Awaj ki brake chaple hoy?"),
        AgentDecision(action="estimate", job_codes=["BRAKE_PADS_F"], explanation="Pads."),
    ))
    first = estimate(logged_in, car).get_json()
    assert first == {
        "status": "question", "question": "Awaj ki brake chaple hoy?",
        "questions_asked": 0, "max_questions": 3,
    }
    assert db.session.execute(db.select(Estimate)).first() is None

    second = estimate(logged_in, car, answers=[{"question": first["question"], "answer": "ha"}])
    assert second.status_code == 201
    # the answer was passed back to the model as conversation
    assert model.calls[1][-1].content == "ha"


def test_question_limit_forces_an_answer(logged_in, car, use_model):
    use_model(FakeModel(AgentDecision(action="ask", question="Aro kichu?", job_codes=["BRAKE_PADS_F"])))
    answers = [{"question": f"Q{i}", "answer": "ha"} for i in range(3)]
    res = estimate(logged_in, car, answers=answers)
    assert res.status_code == 201
    assert res.get_json()["status"] == "done"


def test_more_than_three_answers_rejected(logged_in, car):
    answers = [{"question": "Q", "answer": "A"}] * 4
    assert estimate(logged_in, car, answers=answers).status_code == 422


def test_no_matching_job(logged_in, car, use_model):
    use_model(FakeModel(AgentDecision(action="estimate", job_codes=[], explanation="Sunroof is not covered.")))
    data = estimate(logged_in, car, problem_text="sunroof khole na").get_json()
    assert data["status"] == "no_match"
    assert "Sunroof" in data["explanation"]


def test_ai_failure_offers_manual_choice(logged_in, car, use_model):
    use_model(FakeModel(error=TimeoutError("Gemini timed out")))
    res = estimate(logged_in, car)
    assert res.status_code == 503
    data = res.get_json()
    assert data["status"] == "ai_unavailable"
    assert "BRAKE_PADS_F" in data["suggested"]


def test_missing_api_key_offers_manual_choice(logged_in, car, app):
    app.config["GOOGLE_API_KEY"] = None
    assert estimate(logged_in, car).get_json()["status"] == "ai_unavailable"


def test_manual_job_selection_skips_ai(logged_in, car, use_model):
    model = use_model(FakeModel())
    res = estimate(logged_in, car, job_codes=["BRAKE_PADS_F", "CV_JOINT"])
    assert res.status_code == 201
    data = res.get_json()["estimate"]
    assert data["method"] == "manual"
    assert model.calls == []
    # no CV joint prices for this Axio in the test data
    assert data["confidence"] == "insufficient"
    assert any("Not enough price data" in w for w in data["warnings"])


def test_manual_unknown_job_rejected(logged_in, car):
    res = estimate(logged_in, car, job_codes=["NOPE"])
    assert res.status_code == 422


@pytest.mark.parametrize(
    "body, field",
    [
        ({"problem_text": "abc"}, "problem_text"),
        ({"problem_text": "x" * 1001}, "problem_text"),
        ({"garage_tier": "palace"}, "garage_tier"),
        ({"vehicle_id": "1"}, "vehicle_id"),
        ({"job_codes": []}, "job_codes"),
    ],
)
def test_validation(logged_in, car, body, field):
    res = estimate(logged_in, car, **body)
    assert res.status_code == 422
    assert field in res.get_json()["fields"]


def test_cannot_estimate_someone_elses_car(app, car, use_model):
    use_model(FakeModel())
    stranger = app.test_client()
    register(stranger, email="stranger@example.com")
    assert estimate(stranger, car).status_code == 404


def test_job_catalogue_with_suggestions(logged_in, car):
    data = logged_in.get("/api/estimates/jobs?q=ac thanda hoy na").get_json()
    assert len(data["jobs"]) == 20
    assert data["suggested"][0] == "AC_SERVICE"
    assert data["garage_tiers"] == ["local", "workshop", "dealer"]


def test_prompt_contains_car_and_catalogue(app, car):
    from app.models import Vehicle

    vehicle = db.session.get(Vehicle, car["id"])
    messages = agent.build_messages("brake e awaj", vehicle, [])
    system = messages[0].content
    assert "Toyota Axio 2016" in system
    assert "BRAKE_PADS_F" in system
    assert "84,000 km" in system
    assert db.session.execute(db.select(Part)).first() is not None


@pytest.mark.parametrize(
    "text, script",
    [("AC thanda hoy na", "latin"), ("The AC is weak", "latin"), ("এসি ঠান্ডা হয় না", "bangla")],
)
def test_reply_script_follows_the_owner(text, script):
    assert agent.owner_script(text, []) == script

from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, jwt_required

from ..ai.agent import MAX_QUESTIONS, AgentUnavailable, run_agent
from ..ai.calculator import EstimateInputError, calculate_estimate
from ..ai.tools import find_service_jobs
from ..errors import APIError
from ..extensions import db, limiter
from ..models import Estimate, EstimateItem
from ..models.price import GARAGE_TIERS
from .vehicles import get_own_vehicle

bp = Blueprint("estimates", __name__, url_prefix="/api/estimates")

PROBLEM_MIN = 5
PROBLEM_MAX = 1000
ANSWER_MAX = 300

SAFETY_WARNING = (
    "{job} affects safety. Avoid long drives and have a mechanic check it soon. / "
    "{job_bn} নিরাপত্তার সাথে জড়িত। দ্রুত মেকানিক দেখান।"
)
NO_DATA_NOTE = "Not enough price data for: {parts}. These parts are left out of the total."


def _parse_request(data):
    if not isinstance(data, dict):
        raise APIError("Send the request as JSON.", 400)
    errors = {}

    vehicle_id = data.get("vehicle_id")
    if isinstance(vehicle_id, bool) or not isinstance(vehicle_id, int):
        errors["vehicle_id"] = "Choose one of your cars."

    problem = data.get("problem_text")
    problem = " ".join(problem.split()) if isinstance(problem, str) else ""
    if not PROBLEM_MIN <= len(problem) <= PROBLEM_MAX:
        errors["problem_text"] = (
            f"Describe the problem in {PROBLEM_MIN} to {PROBLEM_MAX} characters."
        )

    tier = data.get("garage_tier", "workshop")
    if tier not in GARAGE_TIERS:
        errors["garage_tier"] = "Choose a garage type: " + ", ".join(GARAGE_TIERS) + "."

    answers = data.get("answers") or []
    clean_answers = []
    if not isinstance(answers, list) or len(answers) > MAX_QUESTIONS:
        errors["answers"] = f"At most {MAX_QUESTIONS} answers."
    else:
        for turn in answers:
            q = turn.get("question") if isinstance(turn, dict) else None
            a = turn.get("answer") if isinstance(turn, dict) else None
            if not isinstance(q, str) or not isinstance(a, str) or not a.strip():
                errors["answers"] = "Please answer the question."
                break
            clean_answers.append({"question": q.strip()[:ANSWER_MAX], "answer": a.strip()[:ANSWER_MAX]})

    job_codes = data.get("job_codes")
    if job_codes is not None:
        if not isinstance(job_codes, list) or not all(isinstance(c, str) for c in job_codes):
            errors["job_codes"] = "Choose the repair jobs from the list."
        elif not job_codes:
            errors["job_codes"] = "Choose at least one repair job."

    if errors:
        raise APIError("Please fix the highlighted fields.", 422, errors)

    return {
        "vehicle_id": vehicle_id,
        "problem_text": problem,
        "garage_tier": tier,
        "answers": clean_answers,
        "job_codes": job_codes,
    }


def _save(vehicle, req, result, explanation, ai_warnings, method):
    warnings = list(ai_warnings)
    for job in result["jobs"]:
        if job["safety_critical"]:
            warnings.append(SAFETY_WARNING.format(job=job["name_en"], job_bn=job["name_bn"]))
    if result["missing_parts"]:
        warnings.append(NO_DATA_NOTE.format(parts=", ".join(result["missing_parts"])))

    estimate = Estimate(
        user_id=current_user.id,
        vehicle_id=vehicle.id,
        vehicle_label=vehicle.label,
        problem_text=req["problem_text"],
        garage_tier=req["garage_tier"],
        total_min=result["total_min"],
        total_likely=result["total_likely"],
        total_max=result["total_max"],
        confidence=result["confidence"],
        explanation=explanation,
        warnings=warnings,
        method=method,
        items=[
            EstimateItem(
                job_code=item["job_code"],
                kind=item["kind"],
                description=item["description"],
                quantity=item["quantity"],
                price_min=item["price_min"],
                price_max=item["price_max"],
                price_count=item["price_count"],
            )
            for item in result["items"]
        ],
    )
    db.session.add(estimate)
    db.session.commit()

    data = estimate.to_dict(with_items=True)
    # Per-item "likely" values are shown right after estimating; history keeps min/max.
    for saved, calc in zip(data["items"], result["items"]):
        saved["price_likely"] = calc["price_likely"]
        saved["description_bn"] = calc["description_bn"]
    data["jobs"] = result["jobs"]
    return data


# Landing page: "Common repairs" tiles and sample job cards, priced from real data.
HIGHLIGHT_TILES = [
    ("brakes", "Brakes", "BRAKE_PADS_F"),
    ("ac", "AC", "AC_SERVICE"),
    ("battery", "Battery", "BATTERY"),
    ("suspension", "Suspension", "STAB_LINKS"),
    ("servicing", "Servicing", "OIL_SERVICE"),
    ("cooling", "Overheating", "COOLING_SERVICE"),
]
HIGHLIGHT_SAMPLES = [
    ("Axio", 2016, "BRAKE_PADS_F", "local"),
    ("Premio", 2014, "AC_SERVICE", "workshop"),
    ("Noah", 2012, "BATTERY", "local"),
]


def _try_estimate(job_code, model, tier):
    try:
        result = calculate_estimate([job_code], model, tier)
    except EstimateInputError:
        return None
    return None if result["confidence"] == "insufficient" else result


@bp.get("/highlights")
def highlights():
    """Public: starting prices per repair type and three sample estimates."""
    from ..models.price import CAR_MODELS

    tiles = []
    for key, name, code in HIGHLIGHT_TILES:
        results = [r for r in (_try_estimate(code, m, "local") for m in CAR_MODELS) if r]
        if results:
            tiles.append({"key": key, "name": name, "job_code": code,
                          "from": min(r["total_min"] for r in results)})

    samples = []
    for model, year, code, tier in HIGHLIGHT_SAMPLES:
        result = _try_estimate(code, model, tier)
        if not result or not result["total_likely"]:
            continue
        parts = sum(i["price_likely"] for i in result["items"]
                    if i["kind"] == "part" and i["price_likely"] is not None)
        parts_share = round(100 * parts / result["total_likely"])
        samples.append({
            "car": f"Toyota {model} {year}",
            "job": result["jobs"][0]["name_en"],
            "garage_tier": tier,
            "total_min": result["total_min"],
            "total_likely": result["total_likely"],
            "total_max": result["total_max"],
            "parts_share": parts_share,
            "labour_share": 100 - parts_share,
        })

    return {"tiles": tiles, "samples": samples}


@bp.get("/jobs")
@jwt_required()
def list_jobs():
    """Catalogue for choosing jobs by hand, optionally ranked by a problem description."""
    text = request.args.get("q", "").strip()[:PROBLEM_MAX]
    all_jobs = find_service_jobs()
    suggested = [j["code"] for j in find_service_jobs(text, limit=3)] if text else []
    return {
        "jobs": [
            {k: j[k] for k in ("code", "name_en", "name_bn", "safety_critical")} for j in all_jobs
        ],
        "suggested": suggested,
        "garage_tiers": GARAGE_TIERS,
    }


@bp.post("")
@jwt_required()
@limiter.limit("30 per hour")
def create_estimate():
    req = _parse_request(request.get_json(silent=True))
    vehicle = get_own_vehicle(req["vehicle_id"])

    # Manual mode: the user picked the jobs, no AI involved.
    if req["job_codes"] is not None:
        try:
            result = calculate_estimate(req["job_codes"], vehicle.model, req["garage_tier"])
        except EstimateInputError as err:
            raise APIError(str(err), 422, {"job_codes": str(err)})
        estimate = _save(vehicle, req, result, "Jobs chosen by hand.", [], "manual")
        return {"status": "done", "estimate": estimate}, 201

    try:
        decision = run_agent(req["problem_text"], vehicle, req["answers"])
    except AgentUnavailable:
        suggestions = [j["code"] for j in find_service_jobs(req["problem_text"], limit=3)]
        return jsonify({
            "status": "ai_unavailable",
            "message": "The AI assistant is not available right now. "
            "You can choose the repair jobs yourself.",
            "suggested": suggestions,
        }), 503

    if decision.action == "ask":
        return {
            "status": "question",
            "question": decision.question,
            "questions_asked": len(req["answers"]),
            "max_questions": MAX_QUESTIONS,
        }

    if not decision.job_codes:
        return {
            "status": "no_match",
            "explanation": decision.explanation
            or "We could not match this problem to a repair job we have prices for.",
            "warnings": decision.safety_warnings,
            "suggested": [j["code"] for j in find_service_jobs(req["problem_text"], limit=3)],
        }

    result = calculate_estimate(decision.job_codes, vehicle.model, req["garage_tier"])
    estimate = _save(
        vehicle, req, result, decision.explanation, decision.safety_warnings, "ai"
    )
    return {"status": "done", "estimate": estimate}, 201

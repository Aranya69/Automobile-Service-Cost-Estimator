from datetime import date

import pytest

from app.ai.calculator import EstimateInputError, calculate_estimate, round50
from app.ai.tools import find_service_jobs, get_labour_rate, get_part_prices
from app.extensions import db
from app.models import Part, PartPrice
from scripts.import_prices import load_mapping, sync_catalogue


@pytest.fixture
def catalogue(app):
    return sync_catalogue(load_mapping())


def add_prices(part, model, *prices, verified=True):
    for i, value in enumerate(prices):
        db.session.add(PartPrice(
            part_id=part.id, car_model=model, quality_tier="oem", price_bdt=value,
            source="garage" if verified else "bikroy", collected_on=date(2026, 10, 1 + i),
            verified=verified,
        ))
    db.session.commit()


def part(name):
    return db.session.execute(db.select(Part).filter_by(name_en=name)).scalar_one()


def test_find_jobs_by_banglish_keywords(catalogue):
    codes = [j["code"] for j in find_service_jobs("brake e awaj kore", limit=3)]
    assert "BRAKE_PADS_F" in codes


def test_find_jobs_by_bangla_keywords(catalogue):
    codes = [j["code"] for j in find_service_jobs("এসি ঠান্ডা হয় না", limit=2)]
    assert codes[0] == "AC_SERVICE"


def test_part_price_summary(catalogue):
    pads = part("Front brake pads (set)")
    add_prices(pads, "Axio", 2400, 4000, 3000)
    summary = get_part_prices(pads.id, "Axio")
    assert summary == {"count": 3, "verified": 3, "min": 2400, "max": 4000, "median": 3000}
    assert get_part_prices(pads.id, "Noah")["count"] == 0


def test_labour_rate_lookup(catalogue):
    assert get_labour_rate("workshop") == {"garage_tier": "workshop", "rate_min": 700, "rate_max": 1200}
    assert get_labour_rate("workshop", on=date(2025, 1, 1)) is None
    assert get_labour_rate("spaceship") is None


def test_brake_pad_estimate(catalogue):
    add_prices(part("Front brake pads (set)"), "Axio", 2400, 3000, 3600, 4000, 6500)
    result = calculate_estimate(["BRAKE_PADS_F"], "Axio", "workshop")

    part_item, labour = result["items"]
    assert (part_item["price_min"], part_item["price_likely"], part_item["price_max"]) == (2400, 3600, 6500)
    # 1.0 h at 700-1200 BDT/h
    assert (labour["price_min"], labour["price_likely"], labour["price_max"]) == (700, 950, 1200)
    assert result["total_min"] == 3100
    assert result["total_likely"] == 4550
    assert result["total_max"] == 7700
    assert result["confidence"] == "high"
    assert result["jobs"][0]["safety_critical"] is True


def test_quantity_multiplies_price(catalogue):
    add_prices(part("Spark plug (iridium)"), "Premio", 1000, 1000)
    result = calculate_estimate(["SPARK_PLUGS"], "Premio", "local")
    assert result["items"][0]["price_min"] == 4000
    assert result["confidence"] == "medium"


def test_shared_part_is_counted_once(catalogue):
    add_prices(part("Front brake pads (set)"), "Axio", 3000)
    add_prices(part("Front brake disc"), "Axio", 5000)
    result = calculate_estimate(["BRAKE_PADS_F", "BRAKE_DISCS_F"], "Axio", "local")
    pad_items = [i for i in result["items"] if i["description"] == "Front brake pads (set)"]
    assert len(pad_items) == 1
    assert result["confidence"] == "low"


def test_missing_prices_mean_insufficient(catalogue):
    result = calculate_estimate(["CV_JOINT"], "Noah", "workshop")
    assert result["confidence"] == "insufficient"
    assert result["missing_parts"] == ["CV joint (outer)"]
    assert result["items"][0]["price_min"] is None
    assert result["total_min"] == round50(1.5 * 700)  # labour only


def test_bad_input(catalogue):
    with pytest.raises(EstimateInputError):
        calculate_estimate([], "Axio", "local")
    with pytest.raises(EstimateInputError, match="Unknown job"):
        calculate_estimate(["FLUX_CAPACITOR"], "Axio", "local")
    with pytest.raises(EstimateInputError, match="labour rate"):
        calculate_estimate(["BATTERY"], "Axio", "spaceship")

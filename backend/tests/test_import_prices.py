import csv
from datetime import date

import pytest

from app.extensions import db
from app.models import JobPart, LabourRate, Part, PartPrice, ServiceJob
from scripts.import_prices import DATA, Matcher, load_mapping, parse_price, run, sync_catalogue

BIKROY_HEADER = ["title", "part", "car_model", "condition", "price", "posted_on"]
GARAGE_HEADER = ["part_name", "car_model", "quality_tier", "price_bdt", "garage", "collected_on"]


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    return path


def count(model):
    return db.session.execute(db.select(db.func.count()).select_from(model)).scalar()


@pytest.fixture
def matcher(app):
    mapping = load_mapping()
    return Matcher(mapping, sync_catalogue(mapping))


def test_catalogue_has_20_jobs_for_5_models(app):
    mapping = load_mapping()
    sync_catalogue(mapping)
    assert count(ServiceJob) == 20
    assert count(Part) == 23
    assert count(LabourRate) == 3
    assert list(mapping["car_models"]) == ["Axio", "Premio", "Allion", "Corolla", "Noah"]
    # every job needs at least one part
    assert count(JobPart) >= 20


def test_catalogue_sync_is_repeatable(app):
    sync_catalogue(load_mapping())
    sync_catalogue(load_mapping())
    assert count(ServiceJob) == 20
    assert count(LabourRate) == 3


@pytest.mark.parametrize(
    "raw, expected",
    [("4500", 4500), ("Tk 4,500", 4500), ("৳৪৫০০", 4500), ("4,500 BDT", 4500),
     ("", None), ("0", None), ("Call for price", None), (None, None)],
)
def test_parse_price(raw, expected):
    assert parse_price(raw) == expected


@pytest.mark.parametrize(
    "text, model",
    [("Corolla Axio", "Axio"), ("Corolla X", "Corolla"), ("Voxy/Noah", "Noah"),
     ("premio", "Premio"), ("Vitz", None)],
)
def test_model_matching(matcher, text, model):
    assert matcher.model(text) == model


@pytest.mark.parametrize(
    "text, tier",
    [("Toyota Genuine", "genuine"), ("Brand new Japan", "oem"), ("China", "aftermarket")],
)
def test_tier_matching(matcher, text, tier):
    assert matcher.tier(text) == tier


@pytest.mark.parametrize(
    "text, part",
    [("Disc pad", "Front brake pads (set)"), ("plug coil", "Ignition coil"),
     ("Iridium plug", "Spark plug (iridium)"), ("mobil filter", "Oil filter"),
     ("mobil 4 liter", "Engine oil 4L (0W-20)"), ("Thermostat", "Thermostat")],
)
def test_part_matching(matcher, text, part):
    assert matcher.part(text).name_en == part


def test_import_skips_bad_rows(app, tmp_path):
    bikroy = write_csv(tmp_path / "b.csv", BIKROY_HEADER, [
        ["Axio brake pad China", "Brake pad front", "Axio", "China", "Tk 2,600", "2026-09-01"],
        ["Axio brake pad China", "Brake pad front", "Axio", "China", "Tk 2,600", "2026-09-01"],  # duplicate
        ["Axio brake pad", "Brake pad front", "Axio", "China", "Call for price", "2026-09-01"],  # no price
        ["Vitz brake pad", "Brake pad front", "Vitz", "China", "2400", "2026-09-01"],  # other model
        ["Axio sunroof", "Sunroof glass", "Axio", "Japan", "9000", "2026-09-01"],  # unknown part
    ])
    garage = write_csv(tmp_path / "g.csv", GARAGE_HEADER, [
        ["Front brake pads (set)", "Axio", "genuine", "6400", "Garage A", "2026-10-12"],
        ["Front brake pads (set)", "Axio", "genuine", "", "Garage B", "2026-10-12"],
    ])

    results = run(bikroy, garage)
    assert results["bikroy"]["added"] == 1
    assert results["bikroy"]["duplicate"] == 1
    assert results["bikroy"]["no_price"] == 1
    assert results["bikroy"]["unknown_model"] == 1
    assert results["bikroy"]["unknown_part"] == 1
    assert results["garage"]["added"] == 1
    assert results["garage"]["no_price"] == 1

    prices = db.session.execute(db.select(PartPrice).order_by(PartPrice.source)).scalars().all()
    assert [(p.source, p.verified, p.price_bdt, p.quality_tier) for p in prices] == [
        ("bikroy", False, 2600, "aftermarket"),
        ("garage", True, 6400, "genuine"),
    ]
    assert prices[1].collected_on == date(2026, 10, 12)


def test_running_twice_adds_nothing_new(app, tmp_path):
    garage = write_csv(tmp_path / "g.csv", GARAGE_HEADER, [
        ["Radiator", "Premio", "oem", "17500", "Garage C", "2026-10-15"],
    ])
    run(garage=garage)
    again = run(garage=garage)
    assert again["garage"]["added"] == 0
    assert again["garage"]["duplicate"] == 1
    assert count(PartPrice) == 1


def test_sample_files_import(app):
    results = run(DATA / "sample_bikroy_listings.csv", DATA / "sample_garage_prices.csv")
    assert results["bikroy"]["added"] > 300
    assert results["garage"]["added"] > 500
    assert results["bikroy"]["unknown_part"] == 0

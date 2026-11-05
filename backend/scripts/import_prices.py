"""Load the job/part catalogue and import part prices.

Usage (from the backend folder):

    python scripts/import_prices.py
    python scripts/import_prices.py --bikroy path/to/listings.csv --garage path/to/garage.csv

Bikroy CSV columns:  title, part, car_model, condition, price, posted_on
Garage CSV columns:  part_name, car_model, quality_tier, price_bdt, garage, collected_on

Rows without a usable price, rows for other car models or unknown parts, and
duplicates (already in the database or repeated in the file) are skipped.
Running the script twice does not add anything the second time.
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
DATA = BACKEND / "data"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.extensions import db  # noqa: E402
from app.models import JobPart, LabourRate, Part, PartPrice, ServiceJob  # noqa: E402

BANGLA_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def load_mapping(path=DATA / "mapping.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---- catalogue -----------------------------------------------------------


def sync_catalogue(mapping):
    """Create or update parts, jobs, job parts and labour rates from the mapping file."""
    parts = {p.name_en: p for p in db.session.execute(db.select(Part)).scalars()}
    for item in mapping["parts"]:
        part = parts.get(item["name_en"])
        if part is None:
            part = Part(name_en=item["name_en"])
            db.session.add(part)
            parts[part.name_en] = part
        part.name_bn = item["name_bn"]
        part.category = item["category"]
    db.session.flush()

    jobs = {j.code: j for j in db.session.execute(db.select(ServiceJob)).scalars()}
    for item in mapping["jobs"]:
        job = jobs.get(item["code"])
        if job is None:
            job = ServiceJob(code=item["code"])
            db.session.add(job)
        job.name_en = item["name_en"]
        job.name_bn = item["name_bn"]
        job.std_labour_hours = item["hours"]
        job.safety_critical = item["safety"]
        job.keywords = item.get("keywords", "")
        job.job_parts = [
            JobPart(part=parts[name], quantity=qty) for name, qty in item["parts"]
        ]

    for item in mapping["labour_rates"]:
        effective = date.fromisoformat(item["effective_from"])
        rate = db.session.execute(
            db.select(LabourRate).filter_by(garage_tier=item["garage_tier"], effective_from=effective)
        ).scalar_one_or_none()
        if rate is None:
            rate = LabourRate(garage_tier=item["garage_tier"], effective_from=effective)
            db.session.add(rate)
        rate.rate_min = item["rate_min"]
        rate.rate_max = item["rate_max"]

    db.session.commit()
    return parts


# ---- matching messy text -------------------------------------------------


class Matcher:
    """Turns free text like 'Corolla Axio' or 'Brand new Japan' into our names."""

    def __init__(self, mapping, parts):
        self.models = self._index(mapping["car_models"])
        self.tiers = self._index(mapping["quality_tiers"])
        self.parts_by_name = {name.lower(): part for name, part in parts.items()}
        self.part_aliases = self._index(
            {p["name_en"]: p["aliases"] for p in mapping["parts"]}
        )
        self.parts = parts

    @staticmethod
    def _index(groups):
        pairs = [(alias.lower(), name) for name, aliases in groups.items() for alias in aliases]
        pairs += [(name.lower(), name) for name in groups]
        # Longest alias first, so "corolla axio" wins over "corolla".
        return sorted(set(pairs), key=lambda pair: -len(pair[0]))

    @staticmethod
    def _find(index, text):
        text = " " + re.sub(r"[^a-z0-9]+", " ", (text or "").lower()) + " "
        for alias, name in index:
            needle = " " + re.sub(r"[^a-z0-9]+", " ", alias).strip() + " "
            if needle in text:
                return name
        return None

    def model(self, text):
        return self._find(self.models, text)

    def tier(self, text):
        return self._find(self.tiers, text)

    def part(self, *texts):
        for text in texts:
            exact = self.parts_by_name.get((text or "").strip().lower())
            if exact is not None:
                return exact
        for text in texts:
            name = self._find(self.part_aliases, text)
            if name:
                return self.parts[name]
        return None


def parse_price(raw):
    """'Tk 4,500', '৳4500', '4500 BDT' -> 4500. Blank, zero or 'Call for price' -> None."""
    if raw is None:
        return None
    digits = re.sub(r"[^\d]", "", str(raw).translate(BANGLA_DIGITS))
    if not digits:
        return None
    value = int(digits)
    return value if value > 0 else None


def parse_date(raw, fallback):
    try:
        return date.fromisoformat(str(raw).strip())
    except ValueError:
        return fallback


# ---- import --------------------------------------------------------------


def _bikroy_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            yield {
                "part_texts": (row.get("part"), row.get("title")),
                "model_text": row.get("car_model") or row.get("title"),
                "tier_text": row.get("condition") or row.get("title"),
                "price": row.get("price"),
                "date": row.get("posted_on"),
            }


def _garage_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            yield {
                "part_texts": (row.get("part_name"),),
                "model_text": row.get("car_model"),
                "tier_text": row.get("quality_tier"),
                "price": row.get("price_bdt"),
                "date": row.get("collected_on"),
            }


def _existing_keys():
    rows = db.session.execute(
        db.select(
            PartPrice.part_id,
            PartPrice.car_model,
            PartPrice.quality_tier,
            PartPrice.price_bdt,
            PartPrice.source,
            PartPrice.collected_on,
        )
    )
    return {tuple(r) for r in rows}


def import_file(rows, source, verified, matcher, seen, today=None):
    today = today or date.today()
    counts = Counter()
    for row in rows:
        counts["read"] += 1
        price = parse_price(row["price"])
        if price is None:
            counts["no_price"] += 1
            continue
        model = matcher.model(row["model_text"])
        if model is None:
            counts["unknown_model"] += 1
            continue
        part = matcher.part(*row["part_texts"])
        if part is None:
            counts["unknown_part"] += 1
            continue
        tier = matcher.tier(row["tier_text"]) or "aftermarket"
        collected = parse_date(row["date"], today)

        key = (part.id, model, tier, price, source, collected)
        if key in seen:
            counts["duplicate"] += 1
            continue
        seen.add(key)

        db.session.add(
            PartPrice(
                part_id=part.id,
                car_model=model,
                quality_tier=tier,
                price_bdt=price,
                source=source,
                collected_on=collected,
                verified=verified,
            )
        )
        counts["added"] += 1

    db.session.commit()
    return counts


def run(bikroy=None, garage=None, mapping_path=DATA / "mapping.json"):
    mapping = load_mapping(mapping_path)
    parts = sync_catalogue(mapping)
    matcher = Matcher(mapping, parts)
    seen = _existing_keys()

    results = {}
    if bikroy:
        results["bikroy"] = import_file(_bikroy_rows(bikroy), "bikroy", False, matcher, seen)
    if garage:
        results["garage"] = import_file(_garage_rows(garage), "garage", True, matcher, seen)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description="Import part prices.")
    parser.add_argument("--bikroy", default=str(DATA / "sample_bikroy_listings.csv"))
    parser.add_argument("--garage", default=str(DATA / "sample_garage_prices.csv"))
    parser.add_argument("--mapping", default=str(DATA / "mapping.json"))
    args = parser.parse_args(argv)

    from app import create_app

    app = create_app()
    with app.app_context():
        results = run(args.bikroy, args.garage, args.mapping)

    for source, counts in results.items():
        skipped = counts["read"] - counts["added"]
        print(
            f"{source:7} read {counts['read']:4}  added {counts['added']:4}  skipped {skipped:4}"
            f"  (no price {counts['no_price']}, duplicate {counts['duplicate']},"
            f" unknown model {counts['unknown_model']}, unknown part {counts['unknown_part']})"
        )


if __name__ == "__main__":
    main()

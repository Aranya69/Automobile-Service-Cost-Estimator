"""Turn a list of job codes into an itemised min / likely / max estimate."""

from .tools import find_service_jobs, get_labour_rate, get_part_prices


class EstimateInputError(ValueError):
    pass


def round50(value):
    return int(round(value / 50.0)) * 50


def _confidence(part_counts, part_verified):
    if not part_counts:
        return "high"  # labour-only job
    if min(part_counts) == 0:
        return "insufficient"
    if min(part_counts) >= 5 and min(part_verified) >= 1:
        return "high"
    if min(part_counts) >= 2:
        return "medium"
    return "low"


def calculate_estimate(job_codes, car_model, garage_tier):
    codes = list(dict.fromkeys(job_codes))  # keep order, drop repeats
    if not codes:
        raise EstimateInputError("Choose at least one repair job.")

    jobs = find_service_jobs(codes=codes)
    found = {j["code"] for j in jobs}
    unknown = [c for c in codes if c not in found]
    if unknown:
        raise EstimateInputError(f"Unknown job code: {', '.join(unknown)}")
    jobs.sort(key=lambda j: codes.index(j["code"]))

    rate = get_labour_rate(garage_tier)
    if rate is None:
        raise EstimateInputError(f"No labour rate for garage tier '{garage_tier}'.")

    items = []
    missing = []
    counts, verified = [], []
    priced_parts = set()  # a part shared by two jobs (e.g. brake pads) is counted once

    for job in jobs:
        for part in job["parts"]:
            if part["part_id"] in priced_parts:
                continue
            priced_parts.add(part["part_id"])

            summary = get_part_prices(part["part_id"], car_model)
            qty = part["quantity"]
            counts.append(summary["count"])
            verified.append(summary["verified"])

            if summary["count"] == 0:
                missing.append(part["name_en"])
                items.append({
                    "job_code": job["code"],
                    "kind": "part",
                    "description": part["name_en"],
                    "description_bn": part["name_bn"],
                    "quantity": qty,
                    "price_min": None,
                    "price_likely": None,
                    "price_max": None,
                    "price_count": 0,
                })
                continue

            items.append({
                "job_code": job["code"],
                "kind": "part",
                "description": part["name_en"],
                "description_bn": part["name_bn"],
                "quantity": qty,
                "price_min": round50(summary["min"] * qty),
                "price_likely": round50(summary["median"] * qty),
                "price_max": round50(summary["max"] * qty),
                "price_count": summary["count"],
            })

        hours = job["std_labour_hours"]
        items.append({
            "job_code": job["code"],
            "kind": "labour",
            "description": f"Labour: {job['name_en']} ({hours:g} h)",
            "description_bn": f"মজুরি: {job['name_bn']}",
            "quantity": hours,
            "price_min": round50(hours * rate["rate_min"]),
            "price_likely": round50(hours * (rate["rate_min"] + rate["rate_max"]) / 2),
            "price_max": round50(hours * rate["rate_max"]),
            "price_count": 1,
        })

    priced = [i for i in items if i["price_min"] is not None]
    return {
        "jobs": [
            {k: j[k] for k in ("code", "name_en", "name_bn", "safety_critical")} for j in jobs
        ],
        "items": items,
        "total_min": sum(i["price_min"] for i in priced),
        "total_likely": sum(i["price_likely"] for i in priced),
        "total_max": sum(i["price_max"] for i in priced),
        "confidence": _confidence(counts, verified),
        "missing_parts": missing,
        "labour_rate": rate,
    }

"""Exact database lookups used by the estimator and by the AI agent.

The AI never invents a price: it only chooses job codes. Every taka figure
comes from these queries.
"""

import re
from datetime import date
from statistics import median

from ..extensions import db
from ..models import LabourRate, Part, PartPrice, ServiceJob

WORD = re.compile(r"[\wঀ-৿]+", re.UNICODE)


def _job_dict(job):
    return {
        "code": job.code,
        "name_en": job.name_en,
        "name_bn": job.name_bn,
        "std_labour_hours": job.std_labour_hours,
        "safety_critical": job.safety_critical,
        "parts": [
            {
                "part_id": jp.part.id,
                "name_en": jp.part.name_en,
                "name_bn": jp.part.name_bn,
                "quantity": jp.quantity,
            }
            for jp in job.job_parts
        ],
    }


def find_service_jobs(text=None, codes=None, limit=None):
    """All jobs, the jobs with the given codes, or the jobs whose keywords best match text."""
    query = db.select(ServiceJob).order_by(ServiceJob.id)
    if codes is not None:
        query = query.where(ServiceJob.code.in_(list(codes)))
    jobs = db.session.execute(query).scalars().all()

    if text:
        words = {w.lower() for w in WORD.findall(text)}
        scored = []
        for job in jobs:
            keywords = {w.lower() for w in WORD.findall(f"{job.keywords} {job.name_en}")}
            score = len(words & keywords)
            if score:
                scored.append((score, job.id, job))
        scored.sort(key=lambda s: (-s[0], s[1]))
        jobs = [job for _, _, job in scored]

    if limit:
        jobs = jobs[:limit]
    return [_job_dict(job) for job in jobs]


def get_part_prices(part_id, car_model, quality_tier=None):
    """Price summary for one part on one car model, from every source we have."""
    query = db.select(PartPrice.price_bdt, PartPrice.verified).where(
        PartPrice.part_id == part_id, PartPrice.car_model == car_model
    )
    if quality_tier:
        query = query.where(PartPrice.quality_tier == quality_tier)
    rows = db.session.execute(query).all()
    prices = [r.price_bdt for r in rows]

    if not prices:
        return {"count": 0, "verified": 0, "min": None, "max": None, "median": None}
    return {
        "count": len(prices),
        "verified": sum(1 for r in rows if r.verified),
        "min": min(prices),
        "max": max(prices),
        "median": int(median(prices)),
    }


def get_labour_rate(garage_tier, on=None):
    """The labour rate in force on a date (today by default), BDT per hour."""
    on = on or date.today()
    rate = db.session.execute(
        db.select(LabourRate)
        .where(LabourRate.garage_tier == garage_tier, LabourRate.effective_from <= on)
        .order_by(LabourRate.effective_from.desc())
        .limit(1)
    ).scalar_one_or_none()
    if rate is None:
        return None
    return {"garage_tier": rate.garage_tier, "rate_min": rate.rate_min, "rate_max": rate.rate_max}


def part_name(part_id):
    part = db.session.get(Part, part_id)
    return part.name_en if part else None

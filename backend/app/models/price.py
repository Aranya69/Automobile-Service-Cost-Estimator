from ..extensions import db

CAR_MODELS = ["Axio", "Premio", "Allion", "Corolla", "Noah"]
QUALITY_TIERS = ["genuine", "oem", "aftermarket"]
GARAGE_TIERS = ["local", "workshop", "dealer"]
SOURCES = ["bikroy", "garage"]


class Part(db.Model):
    __tablename__ = "parts"

    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(80), nullable=False, unique=True)
    name_bn = db.Column(db.String(80), nullable=False)
    category = db.Column(db.String(30), nullable=False)

    prices = db.relationship("PartPrice", back_populates="part", cascade="all, delete-orphan")


class ServiceJob(db.Model):
    __tablename__ = "service_jobs"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), nullable=False, unique=True)
    name_en = db.Column(db.String(100), nullable=False)
    name_bn = db.Column(db.String(100), nullable=False)
    std_labour_hours = db.Column(db.Float, nullable=False)
    safety_critical = db.Column(db.Boolean, nullable=False, default=False)
    # Words people use for the problem, in English, Banglish and Bangla. Space separated.
    keywords = db.Column(db.Text, nullable=False, default="")

    job_parts = db.relationship("JobPart", back_populates="job", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "code": self.code,
            "name_en": self.name_en,
            "name_bn": self.name_bn,
            "std_labour_hours": self.std_labour_hours,
            "safety_critical": self.safety_critical,
        }


class JobPart(db.Model):
    __tablename__ = "job_parts"

    job_id = db.Column(
        db.Integer, db.ForeignKey("service_jobs.id", ondelete="CASCADE"), primary_key=True
    )
    part_id = db.Column(db.Integer, db.ForeignKey("parts.id", ondelete="CASCADE"), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    job = db.relationship("ServiceJob", back_populates="job_parts")
    part = db.relationship("Part")


class PartPrice(db.Model):
    __tablename__ = "part_prices"
    __table_args__ = (
        db.UniqueConstraint(
            "part_id", "car_model", "quality_tier", "price_bdt", "source", "collected_on",
            name="uq_part_price_row",
        ),
        db.Index("ix_part_prices_lookup", "part_id", "car_model"),
    )

    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey("parts.id", ondelete="CASCADE"), nullable=False)
    car_model = db.Column(db.String(30), nullable=False)
    quality_tier = db.Column(db.String(20), nullable=False)
    price_bdt = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(20), nullable=False)
    collected_on = db.Column(db.Date, nullable=False)
    verified = db.Column(db.Boolean, nullable=False, default=False)

    part = db.relationship("Part", back_populates="prices")

    def to_dict(self):
        return {
            "car_model": self.car_model,
            "quality_tier": self.quality_tier,
            "price_bdt": self.price_bdt,
            "source": self.source,
            "collected_on": self.collected_on.isoformat(),
            "verified": self.verified,
        }


class LabourRate(db.Model):
    __tablename__ = "labour_rates"

    id = db.Column(db.Integer, primary_key=True)
    garage_tier = db.Column(db.String(20), nullable=False, index=True)
    rate_min = db.Column(db.Integer, nullable=False)  # BDT per hour
    rate_max = db.Column(db.Integer, nullable=False)
    effective_from = db.Column(db.Date, nullable=False)

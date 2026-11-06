from ..extensions import db
from .common import iso, utcnow

CONFIDENCE_LEVELS = ["high", "medium", "low", "insufficient"]
ITEM_KINDS = ["part", "labour"]


class Estimate(db.Model):
    __tablename__ = "estimates"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Kept when the car is deleted, so old estimates still make sense.
    vehicle_id = db.Column(
        db.Integer, db.ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    vehicle_label = db.Column(db.String(80), nullable=False)
    problem_text = db.Column(db.Text, nullable=False)
    garage_tier = db.Column(db.String(20), nullable=False)
    total_min = db.Column(db.Integer, nullable=False, default=0)
    total_likely = db.Column(db.Integer, nullable=False, default=0)
    total_max = db.Column(db.Integer, nullable=False, default=0)
    confidence = db.Column(db.String(20), nullable=False)
    explanation = db.Column(db.Text, nullable=False, default="")
    warnings = db.Column(db.JSON, nullable=False, default=list)
    method = db.Column(db.String(10), nullable=False, default="ai")  # "ai" or "manual"
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    items = db.relationship(
        "EstimateItem",
        back_populates="estimate",
        cascade="all, delete-orphan",
        order_by="EstimateItem.id",
    )
    owner = db.relationship("User", back_populates="estimates")
    vehicle = db.relationship("Vehicle", back_populates="estimates")

    def to_dict(self, with_items=False):
        data = {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "vehicle_label": self.vehicle_label,
            "problem_text": self.problem_text,
            "garage_tier": self.garage_tier,
            "total_min": self.total_min,
            "total_likely": self.total_likely,
            "total_max": self.total_max,
            "confidence": self.confidence,
            "method": self.method,
            "created_at": iso(self.created_at),
        }
        if with_items:
            data["explanation"] = self.explanation
            data["warnings"] = list(self.warnings or [])
            data["items"] = [item.to_dict() for item in self.items]
        return data


class EstimateItem(db.Model):
    __tablename__ = "estimate_items"

    id = db.Column(db.Integer, primary_key=True)
    estimate_id = db.Column(
        db.Integer, db.ForeignKey("estimates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_code = db.Column(db.String(30), nullable=False)
    kind = db.Column(db.String(10), nullable=False)
    description = db.Column(db.String(160), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1)
    price_min = db.Column(db.Integer, nullable=True)  # None when we have no price data
    price_max = db.Column(db.Integer, nullable=True)
    price_count = db.Column(db.Integer, nullable=False, default=0)

    estimate = db.relationship("Estimate", back_populates="items")

    def to_dict(self):
        return {
            "id": self.id,
            "job_code": self.job_code,
            "kind": self.kind,
            "description": self.description,
            "quantity": self.quantity,
            "price_min": self.price_min,
            "price_max": self.price_max,
            "price_count": self.price_count,
        }

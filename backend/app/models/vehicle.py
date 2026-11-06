from ..extensions import db
from .common import iso, utcnow

MAKE = "Toyota"

# Engine sizes sold in Bangladesh for each supported model (cc).
MODEL_ENGINES = {
    "Axio": [1300, 1500],
    "Premio": [1500, 1800, 2000],
    "Allion": [1500, 1800, 2000],
    "Corolla": [1300, 1500, 1600, 1800],
    "Noah": [1800, 2000],
}

FIRST_YEAR = 1995
ODOMETER_MAX = 999_999


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    make = db.Column(db.String(30), nullable=False, default=MAKE)
    model = db.Column(db.String(30), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    engine_cc = db.Column(db.Integer, nullable=False)
    odometer_km = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    owner = db.relationship("User", back_populates="vehicles")
    estimates = db.relationship("Estimate", back_populates="vehicle", passive_deletes=True)

    @property
    def label(self):
        return f"{self.make} {self.model} {self.year}"

    def to_dict(self):
        return {
            "id": self.id,
            "make": self.make,
            "model": self.model,
            "year": self.year,
            "engine_cc": self.engine_cc,
            "odometer_km": self.odometer_km,
            "label": self.label,
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
        }

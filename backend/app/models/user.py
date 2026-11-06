from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from .common import iso, utcnow


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    vehicles = db.relationship(
        "Vehicle", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True
    )
    estimates = db.relationship(
        "Estimate", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True
    )

    def set_password(self, password):
        # Werkzeug uses scrypt with a random salt by default.
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "created_at": iso(self.created_at),
        }

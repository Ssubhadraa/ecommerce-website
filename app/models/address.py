from app import db


class Address(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    label = db.Column(db.String(50), default="Home")
    line1 = db.Column(db.String(255), nullable=False)
    line2 = db.Column(db.String(255))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    is_default = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="addresses")

    def to_dict(self):
        return {
            "label": self.label,
            "line1": self.line1,
            "line2": self.line2 or "",
            "city": self.city,
            "state": self.state,
            "pincode": self.pincode,
        }

    def formatted(self):
        parts = [self.line1]
        if self.line2:
            parts.append(self.line2)
        parts.append(f"{self.city}, {self.state} {self.pincode}")
        return ", ".join(parts)

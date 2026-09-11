from app import db
from datetime import datetime


class ExpenseList(db.Model):
    __tablename__ = "expense_lists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    receipts = db.relationship("Receipt", backref="expense_list", lazy=True)

    def to_dict(self):
        total = sum((r.total or 0) for r in self.receipts)
        vat = sum((r.vat_amount or 0) for r in self.receipts)
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "count": len(self.receipts),
            "total": round(total, 2),
            "vat": round(vat, 2),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Receipt(db.Model):
    __tablename__ = "receipts"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    merchant = db.Column(db.String(200))
    subtotal = db.Column(db.Float)
    vat_amount = db.Column(db.Float)
    total = db.Column(db.Float)
    vat_included = db.Column(db.Boolean, default=False)
    vat_rate = db.Column(db.Float, default=0.15)
    date = db.Column(db.Date)
    category = db.Column(db.String(50))
    raw_text = db.Column(db.Text)
    notes = db.Column(db.Text)
    list_id = db.Column(db.Integer, db.ForeignKey("expense_lists.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "merchant": self.merchant,
            "subtotal": self.subtotal,
            "vat_amount": self.vat_amount,
            "total": self.total,
            "vat_included": self.vat_included,
            "vat_rate": self.vat_rate,
            "date": self.date.isoformat() if self.date else None,
            "category": self.category,
            "notes": self.notes,
            "list_id": self.list_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

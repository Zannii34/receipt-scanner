from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, send_from_directory
from app import db
from app.models import Receipt, ExpenseList
from app.ocr import process_receipt
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import uuid


main = Blueprint("main", __name__)


@main.route("/")
def index():
    lists = ExpenseList.query.order_by(ExpenseList.created_at.desc()).all()
    active = ExpenseList.query.filter_by(is_active=True).first()
    recent = Receipt.query.order_by(Receipt.created_at.desc()).limit(10).all()
    return render_template("index.html", lists=lists, active_list=active, receipts=recent)


# ---------- Expense Lists ----------

@main.route("/lists", methods=["GET", "POST"])
def manage_lists():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        desc = request.form.get("description", "").strip()
        if name:
            lst = ExpenseList(name=name, description=desc)
            db.session.add(lst)
            db.session.commit()
        return redirect(url_for("main.manage_lists"))
    lists = ExpenseList.query.order_by(ExpenseList.created_at.desc()).all()
    return render_template("lists.html", lists=lists)


@main.route("/lists/<int:list_id>")
def view_list(list_id):
    lst = ExpenseList.query.get_or_404(list_id)
    receipts = Receipt.query.filter_by(list_id=list_id).order_by(Receipt.date.desc()).all()
    totals = {
        "subtotal": round(sum((r.subtotal or 0) for r in receipts), 2),
        "vat": round(sum((r.vat_amount or 0) for r in receipts), 2),
        "total": round(sum((r.total or 0) for r in receipts), 2),
    }
    return render_template("list_detail.html", lst=lst, receipts=receipts, totals=totals)


@main.route("/lists/<int:list_id>/activate", methods=["POST"])
def activate_list(list_id):
    ExpenseList.query.update({"is_active": False})
    lst = ExpenseList.query.get_or_404(list_id)
    lst.is_active = True
    db.session.commit()
    return jsonify({"ok": True})


@main.route("/lists/<int:list_id>", methods=["DELETE"])
def delete_list(list_id):
    lst = ExpenseList.query.get_or_404(list_id)
    for r in lst.receipts:
        fp = Path(current_app.config["UPLOAD_FOLDER"]) / r.filename
        if fp.exists():
            fp.unlink()
    db.session.delete(lst)
    db.session.commit()
    return jsonify({"ok": True})


# ---------- Upload + Receipts ----------

@main.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}:
        return jsonify({"error": "Unsupported file type"}), 400

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    file.save(filepath)

    try:
        result = process_receipt(str(filepath))
    except Exception as e:
        return jsonify({"error": f"OCR failed: {e}"}), 500

    return jsonify({
        "filename": filename,
        "raw_text": result["raw_text"],
        "merchant": result["merchant"],
        "total": result["total"],
        "subtotal": result["subtotal"],
        "vat_amount": result["vat_amount"],
        "vat_included": result["vat_included"],
        "vat_rate": result["vat_rate"],
        "date": result["date"].isoformat() if result["date"] else None,
        "category": result["category"],
    })


@main.route("/receipts", methods=["POST"])
def save_receipt():
    data = request.get_json() or {}
    r = Receipt(
        filename=data.get("filename"),
        merchant=data.get("merchant"),
        subtotal=data.get("subtotal"),
        vat_amount=data.get("vat_amount"),
        total=data.get("total"),
        vat_included=bool(data.get("vat_included")),
        vat_rate=data.get("vat_rate", 0.15),
        category=data.get("category"),
        notes=data.get("notes"),
        raw_text=data.get("raw_text"),
        list_id=data.get("list_id"),
    )
    d = data.get("date")
    if d:
        try:
            r.date = datetime.fromisoformat(d).date()
        except (ValueError, TypeError):
            r.date = None
    db.session.add(r)
    db.session.commit()
    return jsonify(r.to_dict()), 201


@main.route("/receipt/<int:rid>", methods=["DELETE"])
def delete_receipt(rid):
    r = Receipt.query.get_or_404(rid)
    fp = Path(current_app.config["UPLOAD_FOLDER"]) / r.filename
    if fp.exists():
        fp.unlink()
    db.session.delete(r)
    db.session.commit()
    return jsonify({"ok": True})


@main.route("/uploads/<filename>")
def serve_upload(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


# ---------- Dashboard + API ----------

@main.route("/dashboard")
def dashboard():
    lists = ExpenseList.query.all()
    all_receipts = Receipt.query.all()

    by_category = defaultdict(lambda: {"count": 0, "total": 0.0, "vat": 0.0})
    by_month = defaultdict(float)
    for r in all_receipts:
        cat = r.category or "other"
        by_category[cat]["count"] += 1
        by_category[cat]["total"] += r.total or 0
        by_category[cat]["vat"] += r.vat_amount or 0
        if r.date:
            by_month[r.date.strftime("%Y-%m")] += r.total or 0

    return render_template("dashboard.html",
                         categories=dict(by_category),
                         months=dict(sorted(by_month.items())),
                         total=sum(r.total or 0 for r in all_receipts),
                         total_vat=sum(r.vat_amount or 0 for r in all_receipts),
                         count=len(all_receipts),
                         lists=[l.to_dict() for l in lists])


@main.route("/api/receipts")
def api_receipts():
    receipts = Receipt.query.order_by(Receipt.created_at.desc()).all()
    return jsonify([r.to_dict() for r in receipts])


@main.route("/api/lists")
def api_lists():
    return jsonify([l.to_dict() for l in ExpenseList.query.all()])

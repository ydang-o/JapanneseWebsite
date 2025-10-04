from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from ..extensions import db
from ..models import User
from ..phone import normalize_jp_phone

register_bp = Blueprint("register", __name__)


@register_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    # Prefer phone; fallback to email for backward compatibility
    identifier = (payload.get("phone") or payload.get("email") or "").strip()
    password = payload.get("password") or ""
    display_name = (payload.get("displayName") or "").strip() or "ユーザー"

    if not identifier or not password:
        return jsonify({"error": "電話番号 と パスワードを入力してください"}), 400

    normalized = normalize_jp_phone(identifier)
    if not normalized:
        return jsonify({"error": "日本の電話番号の形式が正しくありません"}), 400

    existing = User.query.filter_by(email=normalized).first()
    if existing:
        if existing.status == "pending":
            return jsonify({"error": "この電話番号は審査中です"}), 409
        return jsonify({"error": "この電話番号は既に登録されています"}), 409

    user = User(
        email=normalized,
        password_hash=generate_password_hash(password),
        display_name=display_name,
        status="pending",
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "登録受付：審査中です"}) 
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from ..extensions import db
from ..models import User

register_bp = Blueprint("register", __name__)


@register_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    display_name = (payload.get("displayName") or "").strip() or "ユーザー"

    if not email or not password:
        return jsonify({"error": "メールアドレスとパスワードを入力してください"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "このメールは既に登録されています"}), 409

    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        display_name=display_name,
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "登録完了しました"}) 
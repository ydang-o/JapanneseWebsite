from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from ..extensions import db
from ..models import User
from ..auth import issue_token

login_bp = Blueprint("login", __name__)


@login_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""

    if not email or not password:
        return jsonify({"error": "メールアドレス/ユーザー名 と パスワードを入力してください"}), 400

    # Hardcoded admin for testing: username 'admin' with password '123456'
    if email.lower() == "admin" and password == "123456":
        admin_email = "admin@local"
        user = User.query.filter_by(email=admin_email).first()
        if not user:
            user = User(
                email=admin_email,
                password_hash=generate_password_hash("123456"),
                display_name="管理者",
            )
            db.session.add(user)
            db.session.commit()
        token = issue_token(user.id)
        return jsonify({
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "displayName": user.display_name,
                "points": user.points_balance,
                "role": "admin",
            },
        })

    # Normal email+password flow
    user = User.query.filter_by(email=email.lower()).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "メールアドレスまたはパスワードが正しくありません"}), 401

    token = issue_token(user.id)
    role = "admin" if user.email == "admin@local" else "user"
    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "displayName": user.display_name,
            "points": user.points_balance,
            "role": role,
        },
    }) 
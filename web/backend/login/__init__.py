from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from ..extensions import db
from ..models import User
from ..auth import issue_token, is_login_locked, register_login_failure, reset_login_counters, get_client_ip
from ..phone import normalize_jp_phone
from ..auth_crypto import get_or_create_rsa_keys, decrypt_payload
from ..config import Config
import base64, json, time

login_bp = Blueprint("login", __name__)


@login_bp.get("/pubkey")
def pubkey():
    pub_pem, _ = get_or_create_rsa_keys()
    return jsonify({"alg": "RSA-OAEP-256", "pem": pub_pem.decode("utf-8")})


@login_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    client_ip = get_client_ip()

    encrypted_blob = payload.get("enc") or request.args.get("t_s")

    def _decode_base64(value: str):
        padded = value + "=" * (-len(value) % 4)
        try:
            return base64.urlsafe_b64decode(padded)
        except Exception:
            return base64.b64decode(padded)

    if encrypted_blob:
        try:
            raw = _decode_base64(encrypted_blob)
            dec = decrypt_payload(raw)
            data = json.loads(dec.decode("utf-8"))
            identifier = (
                data.get("phone")
                or data.get("email")
                or data.get("account")
                or ""
            ).strip()
            password = data.get("password") or ""
            ts = int(data.get("ts") or 0)
            if ts <= 0:
                return jsonify({"error": "不正な時刻です"}), 400
            # 2h window tolerance
            now = int(time.time() * 1000)
            if abs(now - ts) > 2 * 60 * 60 * 1000:
                return jsonify({"error": "時刻の有効期限が切れています"}), 401
        except Exception:
            return jsonify({"error": "復号に失敗しました"}), 400
    else:
        # Plain payload fallback
        identifier = (
            payload.get("phone")
            or payload.get("email")
            or request.args.get("account")
            or ""
        ).strip()
        password = payload.get("password") or request.args.get("password") or ""

    if not identifier or not password:
        return jsonify({"error": "電話番号/ユーザー名 と パスワードを入力してください"}), 400

    # Rate-limit: locked?
    if is_login_locked(identifier):
        return jsonify({"error": "試行回数が多すぎます。しばらくしてから再度お試しください"}), 429

    # Hardcoded admin for testing: username 'admin' with password '123456'
    if identifier.lower() == "admin" and password == "123456":
        admin_email = "admin@local"
        user = User.query.filter_by(email=admin_email).first()
        if not user:
            user = User(
                email=admin_email,
                password_hash=generate_password_hash("123456"),
                display_name="管理者",
                status="approved",
            )
            db.session.add(user)
            db.session.commit()
        token = issue_token(user.id)
        reset_login_counters(identifier, client_ip)
        return jsonify({
            "token": token,
            "ttlMs": 2 * 60 * 60 * 1000,
            "user": {
                "id": user.id,
                "email": user.email,
                "displayName": user.display_name,
                "points": user.points_balance,
                "role": "admin",
                "status": user.status,
            },
        })

    # Try Japanese phone normalization first
    normalized = normalize_jp_phone(identifier)
    lookup = (normalized or identifier).lower()

    user = User.query.filter_by(email=lookup).first()
    if not user or not check_password_hash(user.password_hash, password):
        register_login_failure(identifier, client_ip)
        return jsonify({"error": "電話番号/ユーザー名 または パスワードが正しくありません"}), 401

    if user.status != "approved":
        register_login_failure(identifier, client_ip)
        return jsonify({"error": "アカウントは審査中です"}), 403

    token = issue_token(user.id)
    reset_login_counters(identifier, client_ip)
    role = "admin" if user.email == "admin@local" else "user"
    return jsonify({
        "token": token,
        "ttlMs": 2 * 60 * 60 * 1000,
        "user": {
            "id": user.id,
            "email": user.email,
            "displayName": user.display_name,
            "points": user.points_balance,
            "role": role,
            "status": user.status,
        },
    }) 
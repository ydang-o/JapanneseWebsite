from flask import Blueprint, request, jsonify
from ..auth import require_admin
from ..extensions import db
from ..models import User, PointTransaction
from ..db_init import ensure_database_initialized
from werkzeug.security import generate_password_hash
from ..phone import normalize_jp_phone

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/users")
@require_admin
def list_users():
    page = int(request.args.get("page", 1))
    page_size = min(int(request.args.get("pageSize", 20)), 100)
    q = User.query.order_by(User.id.asc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return jsonify({
        "page": page,
        "pageSize": page_size,
        "total": total,
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "displayName": u.display_name,
                "points": u.points_balance,
                "status": u.status,
                "createdAt": (u.created_at.isoformat() if u.created_at else None),
            }
            for u in items
        ],
    })


@admin_bp.post("/users/approve")
@require_admin
def approve_user():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("userId")
    if not user_id:
        return jsonify({"error": "userId を指定してください"}), 400
    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({"error": "ユーザーが見つかりません"}), 404
    user.status = "approved"
    db.session.commit()
    return jsonify({"message": "承認しました"})


@admin_bp.post("/users/reject")
@require_admin
def reject_user():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("userId")
    if not user_id:
        return jsonify({"error": "userId を指定してください"}), 400
    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({"error": "ユーザーが見つかりません"}), 404
    user.status = "rejected"
    db.session.commit()
    return jsonify({"message": "却下しました"})


@admin_bp.post("/users/create")
@require_admin
def create_user():
    payload = request.get_json(silent=True) or {}
    raw_phone = (payload.get("phone") or "").strip()
    phone = normalize_jp_phone(raw_phone)
    display_name = (payload.get("displayName") or "ユーザー").strip()
    password = (payload.get("password") or "123456").strip()
    if not phone:
        return jsonify({"error": "日本の電話番号の形式が正しくありません"}), 400
    if User.query.filter_by(email=phone).first():
        return jsonify({"error": "既に存在します"}), 409
    user = User(email=phone, display_name=display_name, password_hash=generate_password_hash(password), status="approved")
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "作成しました", "userId": user.id})


@admin_bp.post("/points/adjust")
@require_admin
def adjust_points():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("userId")
    delta = int(payload.get("delta") or 0)
    reason = (payload.get("reason") or "調整").strip() or "調整"

    if not user_id or delta == 0:
        return jsonify({"error": "userId と delta を指定してください"}), 400

    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({"error": "ユーザーが見つかりません"}), 404

    user.points_balance = (user.points_balance or 0) + delta
    tx = PointTransaction(user_id=user.id, delta=delta, reason=reason)
    db.session.add(tx)
    db.session.commit()

    return jsonify({"message": "更新しました", "balance": user.points_balance})


@admin_bp.post("/init-db")
@require_admin
def init_db():
    result = ensure_database_initialized(db.get_app())  # type: ignore
    return jsonify({"message": "DB 初期化完了", "result": result}) 
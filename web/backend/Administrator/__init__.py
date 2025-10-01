from flask import Blueprint, request, jsonify
from ..auth import require_admin
from ..extensions import db
from ..models import User, PointTransaction

admin_bp = Blueprint("admin", __name__)


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
    from ..extensions import db as database
    from ..models import User, PointTransaction  # noqa: F401 ensure tables import

    database.create_all()
    return jsonify({"message": "DB 初期化完了"}) 
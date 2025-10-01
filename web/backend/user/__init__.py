from flask import Blueprint, jsonify, g, request
from ..auth import require_auth
from ..extensions import db
from ..models import User, PointTransaction

user_bp = Blueprint("user", __name__)


@user_bp.get("/me")
@require_auth
def me():
    user = db.session.get(User, g.user_id)
    if not user:
        return jsonify({"error": "ユーザーが見つかりません"}), 404
    role = "admin" if user.email == "admin@local" else "user"
    return jsonify({
        "id": user.id,
        "email": user.email,
        "displayName": user.display_name,
        "points": user.points_balance,
        "role": role,
    })


@user_bp.get("/points")
@require_auth
def points():
    user = db.session.get(User, g.user_id)
    if not user:
        return jsonify({"error": "ユーザーが見つかりません"}), 404
    txs = (
        PointTransaction.query.filter_by(user_id=user.id)
        .order_by(PointTransaction.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify({
        "balance": user.points_balance,
        "transactions": [
            {"id": t.id, "delta": t.delta, "reason": t.reason, "createdAt": t.created_at.isoformat()} for t in txs
        ],
    }) 
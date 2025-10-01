import functools
import secrets
from typing import Callable, Optional
from flask import current_app, request, g, jsonify


def issue_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    ttl_seconds = 60 * 60 * 24 * 7  # 7 days
    current_app.redis.set(f"auth:token:{token}", str(user_id), ex=ttl_seconds)
    return token


def get_user_id_from_token(token: str) -> Optional[int]:
    user_id = current_app.redis.get(f"auth:token:{token}")
    if user_id is None:
        return None
    try:
        return int(user_id)
    except ValueError:
        return None


def require_auth(view_func: Callable):
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split()
        token = parts[1] if len(parts) == 2 and parts[0].lower() == "bearer" else None
        if not token:
            return jsonify({"error": "認証が必要です"}), 401
        user_id = get_user_id_from_token(token)
        if not user_id:
            return jsonify({"error": "トークンが無効です"}), 401
        g.user_id = user_id
        return view_func(*args, **kwargs)

    return wrapper


def require_admin(view_func: Callable):
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        admin_key = request.headers.get("X-ADMIN-KEY")
        if not admin_key or admin_key != current_app.config.get("ADMIN_API_KEY"):
            return jsonify({"error": "管理者権限が必要です"}), 403
        return view_func(*args, **kwargs)

    return wrapper 
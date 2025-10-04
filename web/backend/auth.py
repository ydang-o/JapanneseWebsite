import functools
import secrets
import time
from typing import Callable, Optional, Tuple
from flask import current_app, request, g, jsonify


_TOKEN_FALLBACK = {}
_RATE_FALLBACK = {}  # key -> (count, expire_ts)

# Login rate limit policy
_MAX_ATTEMPTS_PER_IP = 20          # per window
_IP_WINDOW_SECS = 10 * 60
_MAX_ATTEMPTS_PER_USER = 5         # per window
_USER_WINDOW_SECS = 15 * 60
_LOCK_DURATION_SECS = 15 * 60


def _now() -> int:
    return int(time.time())


def _fallback_incr(key: str, window_secs: int) -> int:
    now = _now()
    count, exp = _RATE_FALLBACK.get(key, (0, 0))
    if exp <= now:
        count = 0
    count += 1
    _RATE_FALLBACK[key] = (count, now + window_secs)
    return count


def _fallback_get(key: str) -> Optional[int]:
    now = _now()
    val = _RATE_FALLBACK.get(key)
    if not val:
        return None
    count, exp = val
    if exp <= now:
        return None
    return count


def _fallback_setex(key: str, ttl: int, value: str) -> None:
    # store as count, expiry with value encoded in count (not used for reads except existence)
    _RATE_FALLBACK[key] = (1 if value else 0, _now() + ttl)


def _redis_incr_with_exp(key: str, window_secs: int) -> int:
    try:
        pipe = current_app.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_secs)
        res = pipe.execute()
        return int(res[0])
    except Exception:
        return _fallback_incr(key, window_secs)


def _redis_get(key: str) -> Optional[str]:
    try:
        return current_app.redis.get(key)
    except Exception:
        c = _fallback_get(key)
        return "1" if c is not None else None


def _redis_setex(key: str, ttl: int, value: str) -> None:
    try:
        current_app.redis.setex(key, ttl, value)
    except Exception:
        _fallback_setex(key, ttl, value)


def get_client_ip() -> str:
    # honor reverse proxy headers if present
    hdr = request.headers.get("X-Forwarded-For")
    if hdr:
        return hdr.split(",")[0].strip()
    return request.remote_addr or "0.0.0.0"


def is_login_locked(identifier: str) -> bool:
    lock_key = f"login:lock:user:{identifier}"
    return _redis_get(lock_key) is not None


def register_login_failure(identifier: str, ip: str) -> Tuple[int, int]:
    # returns tuple of (user_attempts, ip_attempts)
    user_key = f"login:user:{identifier}"
    ip_key = f"login:ip:{ip}"
    user_attempts = _redis_incr_with_exp(user_key, _USER_WINDOW_SECS)
    ip_attempts = _redis_incr_with_exp(ip_key, _IP_WINDOW_SECS)

    if user_attempts >= _MAX_ATTEMPTS_PER_USER:
        _redis_setex(f"login:lock:user:{identifier}", _LOCK_DURATION_SECS, "1")
    if ip_attempts >= _MAX_ATTEMPTS_PER_IP:
        _redis_setex(f"login:lock:ip:{ip}", _LOCK_DURATION_SECS, "1")
    return user_attempts, ip_attempts


def reset_login_counters(identifier: str, ip: str) -> None:
    # best-effort reset (works only on redis; fallback will expire naturally)
    try:
        current_app.redis.delete(f"login:user:{identifier}")
        current_app.redis.delete(f"login:ip:{ip}")
    except Exception:
        pass


def _set_token(token: str, user_id: int, ttl_seconds: int) -> None:
    try:
        current_app.redis.set(f"auth:token:{token}", str(user_id), ex=ttl_seconds)
    except Exception:
        _TOKEN_FALLBACK[token] = str(user_id)


def _get_user_id(token: str) -> Optional[int]:
    try:
        user_id = current_app.redis.get(f"auth:token:{token}")
    except Exception:
        user_id = _TOKEN_FALLBACK.get(token)
    if user_id is None:
        return None
    try:
        return int(user_id)
    except ValueError:
        return None


def issue_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    ttl_seconds = 60 * 60 * 2  # 2 hours
    _set_token(token, user_id, ttl_seconds)
    return token


def get_user_id_from_token(token: str) -> Optional[int]:
    return _get_user_id(token)


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
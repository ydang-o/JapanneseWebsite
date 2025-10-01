from urllib.parse import urljoin
from flask import Blueprint, request, jsonify, current_app
import requests

home_bp = Blueprint("home", __name__)


@home_bp.get("/proxy")
def mercari_proxy():
    path = request.args.get("path", "/")
    # Prevent scheme/host injection; only allow path starting with '/'
    if not path.startswith("/"):
        return jsonify({"error": "不正なパスです"}), 400

    url = urljoin(current_app.config["MERCARI_BASE"], path)
    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (compatible; JP-Site/1.0)",
            "Accept-Language": "ja-JP,ja;q=0.9",
        })
        return (resp.content, resp.status_code, {"Content-Type": resp.headers.get("Content-Type", "text/html; charset=utf-8")})
    except requests.RequestException as e:
        return jsonify({"error": "外部サービスに接続できません"}), 502 
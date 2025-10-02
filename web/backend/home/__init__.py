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

    base = current_app.config["MERCARI_BASE"]
    url = urljoin(base, path)
    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (compatible; JP-Site/1.0)",
            "Accept-Language": "ja-JP,ja;q=0.9",
        })
        content_type = resp.headers.get("Content-Type", "text/html; charset=utf-8")

        # If HTML, inject <base> to fix relative resource URLs
        if "text/html" in content_type.lower():
            try:
                text = resp.text
                lower = text.lower()
                insert_tag = f"<base href=\"{base}\">"
                if "<head" in lower and "<base" not in lower:
                    # Insert right after the first <head>
                    idx = lower.find("<head")
                    # find closing '>' of <head ...>
                    head_end = text.find('>', idx)
                    if head_end != -1:
                        text = text[:head_end+1] + insert_tag + text[head_end+1:]
                return (text.encode(resp.encoding or "utf-8"), resp.status_code, {"Content-Type": "text/html; charset=utf-8"})
            except Exception:
                # Fallback to raw content
                pass

        return (resp.content, resp.status_code, {"Content-Type": content_type})
    except requests.RequestException:
        return jsonify({"error": "外部サービスに接続できません"}), 502 
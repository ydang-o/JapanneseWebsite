from urllib.parse import urljoin, urlparse, urlencode, parse_qs
from flask import Blueprint, request, jsonify, current_app
import requests
import re
import json
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

home_bp = Blueprint("home", __name__)


MERCARI_API_ENDPOINT = "https://api.mercari.jp/search/index"


def _normalize_path(raw: str) -> str:
    if not raw:
        return "/"
    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urlparse(raw)
        return parsed.path + (f"?{parsed.query}" if parsed.query else "")
    if not raw.startswith("/"):
        return "/" + raw
    return raw


def _to_proxy_path(base: str, url: str) -> str:
    if not url or url.startswith("javascript:") or url.startswith("#"):
        return url
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    base_host = urlparse(base).netloc
    if parsed.scheme in ("http", "https"):
        if parsed.netloc and base_host.split(':')[0] not in parsed.netloc:
            return url
        pathq = parsed.path or "/"
        if parsed.query:
            pathq += "?" + parsed.query
        return f"/api/home/proxy?" + urlencode({"path": pathq})
    if url.startswith("/"):
        return f"/api/home/proxy?" + urlencode({"path": url})
    return url


def _rewrite_html(html: str, base: str) -> str:
    lower = html.lower()
    insert_tag = f"<base href=\"{base}\">"
    if "<head" in lower and "<base" not in lower:
        idx = lower.find("<head")
        head_end = html.find('>', idx)
        if head_end != -1:
            html = html[:head_end+1] + insert_tag + html[head_end+1:]

    def repl_attr(match):
        attr = match.group(1)
        quote = match.group(2)
        val = match.group(3)
        return f"{attr}={quote}{_to_proxy_path(base, val)}{quote}"

    html = re.sub(r"\b(href|src|action)=(['\"])(.*?)(['\"])",
                  lambda m: repl_attr((lambda a=m: a)()),
                  html, flags=re.IGNORECASE)
    return html


def _rewrite_css(text_css: str, base: str) -> str:
    def repl_url(m):
        raw = m.group(1).strip('"\'')
        return f"url({_to_proxy_path(base, raw)})"
    return re.sub(r"url\((.*?)\)", repl_url, text_css, flags=re.IGNORECASE)


def _extract_products_from_json(obj, base, max_items=60):
    results = []
    stack = [obj]
    while stack and len(results) < max_items:
        current = stack.pop()
        if isinstance(current, dict):
            if ("name" in current and ("price" in current or "priceLabel" in current or "price_label" in current)
                    and ("thumbnails" in current or "images" in current or "image" in current)):
                thumb = current.get("thumbnails") or current.get("images") or [current.get("image")]
                if isinstance(thumb, list) and thumb:
                    img = thumb[0]
                    if isinstance(img, dict):
                        img = img.get("url")
                else:
                    img = thumb
                link = current.get("url") or current.get("link") or current.get("itemUrl") or current.get("item_url")
                price_val = current.get("price") or current.get("priceLabel") or current.get("price_label")
                if price_val is not None:
                    price = f"{price_val}円" if isinstance(price_val, (int, float, str)) else str(price_val)
                else:
                    price = ""
                if link and img and current.get("name"):
                    results.append({
                        "title": current.get("name"),
                        "price": price,
                        "image": _to_proxy_path(base, img),
                        "link": _to_proxy_path(base, link),
                    })
                    continue
            for value in current.values():
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
    return results


def _fetch_merch_api(path: str, limit: int):
    query = urlparse(path).query
    params = parse_qs(query)
    payload = {
        "page": 1,
        "limit": limit,
        "sort": params.get("sort", ["category"])[0],
        "order": params.get("order", ["desc"])[0],
    }
    keyword = params.get("keyword", [""])[0]
    if keyword:
        payload["keyword"] = keyword
    if "category_id" in params:
        payload["category_id"] = params["category_id"][0]
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; JP-Site/1.0)",
        "Referer": current_app.config["MERCARI_BASE"],
    }
    try:
        resp = requests.get(MERCARI_API_ENDPOINT, params=payload, timeout=10, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        items = []
        for product in data.get("items", [])[:limit]:
            thumb = product.get("thumbnails") or product.get("images") or []
            img_url = thumb[0].get("url") if thumb and isinstance(thumb[0], dict) else thumb[0] if thumb else ""
            items.append({
                "title": product.get("name", ""),
                "price": f"{product.get('price', '')}円",
                "image": _to_proxy_path(current_app.config["MERCARI_BASE"], img_url or ""),
                "link": _to_proxy_path(current_app.config["MERCARI_BASE"], product.get("url", "")),
            })
        if items:
            return items
    except Exception:
        pass

    try:
        payload2 = {
            "page": 1,
            "limit": limit,
            "status": "on_sale",
            "sort": params.get("sort", ["sort" if keyword else "category"])[0],
            "order": params.get("order", ["desc"])[0],
        }
        if keyword:
            payload2["keyword"] = keyword
        if "category_id" in params:
            payload2["category_id"] = params["category_id"][0]
        resp2 = requests.get("https://www.mercari.com/jp/api/search/items/", params=payload2, timeout=10, headers=headers)
        resp2.raise_for_status()
        data2 = resp2.json()
        items_data = data2.get("items") or data2.get("data", {}).get("items", [])
        items = []
        for product in items_data[:limit]:
            thumb = product.get("thumbnails") or product.get("images") or []
            img_url = thumb[0].get("url") if thumb and isinstance(thumb[0], dict) else thumb[0] if thumb else product.get("image", "")
            link = product.get("url") or product.get("itemUrl") or product.get("item_url") or ""
            items.append({
                "title": product.get("name", product.get("title", "")),
                "price": f"{product.get('price', '')}円" if product.get('price') else product.get('price_label', ''),
                "image": _to_proxy_path(current_app.config["MERCARI_BASE"], img_url or ""),
                "link": _to_proxy_path(current_app.config["MERCARI_BASE"], link),
            })
        if items:
            return items
    except Exception:
        pass

    return []


@home_bp.get("/feed")
def mercari_feed():
    raw_path = request.args.get("path", "/search/")
    path = _normalize_path(raw_path)
    limit = min(int(request.args.get("limit", 24)), 60)
    base = current_app.config["MERCARI_BASE"]
    url = urljoin(base, path)

    items = _fetch_merch_api(path, limit)
    if items:
        return jsonify({"items": items})

    try:
        resp = requests.get(url, timeout=12, headers={
            "User-Agent": request.headers.get("User-Agent", "Mozilla/5.0 (compatible; JP-Site/1.0)"),
            "Accept-Language": request.headers.get("Accept-Language", "ja-JP,ja;q=0.9"),
        })
        resp.raise_for_status()
        text = resp.text
        soup = BeautifulSoup(text, "html.parser")
        items = []
        for a in soup.select('a'):
            img = a.select_one('img')
            price_node = a.find(string=re.compile(r"\d+\s*円"))
            title = (img.get('alt') if img and img.get('alt') else a.get('aria-label') or '').strip()
            href = a.get('href') or ''
            src = (img.get('src') or img.get('data-src') or '') if img else ''
            if title and price_node and href and src:
                items.append({
                    "title": title,
                    "price": re.sub(r"\s+", "", price_node),
                    "image": _to_proxy_path(base, src),
                    "link": _to_proxy_path(base, href),
                })
        seen = set()
        uniq = []
        for it in items:
            if it['link'] in seen:
                continue
            seen.add(it['link'])
            uniq.append(it)

        if not uniq:
            next_script = soup.find('script', id='__NEXT_DATA__')
            if next_script and (next_script.string or next_script.get_text()):
                try:
                    data_json = json.loads(next_script.string or next_script.get_text())
                    extracted = _extract_products_from_json(data_json, base, limit)
                    for it in extracted:
                        if it['link'] in seen:
                            continue
                        seen.add(it['link'])
                        uniq.append(it)
                        if len(uniq) >= limit:
                            break
                except Exception as exc:
                    logger.debug("Parsing __NEXT_DATA__ failed: %s", exc)

        if not uniq:
            for script in soup.find_all('script'):
                content = script.string or script.get_text() or ''
                if not content:
                    continue
                if 'window.__NUXT__' in content:
                    match = re.search(r"window.__NUXT__\s*=\s*(\{.*?\})\s*;", content, flags=re.S)
                    data_json = None
                    if match:
                        try:
                            data_json = json.loads(match.group(1))
                        except Exception as exc:
                            logger.debug("Failed to parse __NUXT__ JSON: %s", exc)
                            data_json = None
                    else:
                        data_json = None
                elif content.strip().startswith('{') or content.strip().startswith('"{'):
                    try:
                        raw = content.strip()
                        if raw.startswith('"') and raw.endswith('"'):
                            raw = raw[1:-1]
                            raw = raw.encode('utf-8').decode('unicode_escape')
                        data_json = json.loads(raw)
                    except Exception as exc:
                        logger.debug("Failed to parse inline JSON: %s", exc)
                        data_json = None
                else:
                    data_json = None

                if data_json:
                    extracted = _extract_products_from_json(data_json, base, limit)
                    for it in extracted:
                        if it['link'] in seen:
                            continue
                        seen.add(it['link'])
                        uniq.append(it)
                        if len(uniq) >= limit:
                            break

        if not uniq:
            match = re.search(r"window.__NUXT__\s*=\s*(\{.*?\})\s*;", text, flags=re.S)
            if match:
                try:
                    data_json = json.loads(match.group(1))
                    extracted = _extract_products_from_json(data_json, base, limit)
                    for it in extracted:
                        if it['link'] in seen:
                            continue
                        seen.add(it['link'])
                        uniq.append(it)
                        if len(uniq) >= limit:
                            break
                except Exception as exc:
                    logger.debug("Parsing NUXT from page failed: %s", exc)

        return jsonify({"items": uniq[:limit]})
    except requests.RequestException:
        return jsonify({"error": "外部サービスに接続できません"}), 502


@home_bp.get("/proxy")
def mercari_proxy():
    raw_path = request.args.get("path", "/")
    path = _normalize_path(raw_path)
    base = current_app.config["MERCARI_BASE"]
    url = urljoin(base, path)
    try:
        fwd_headers = {
            "User-Agent": request.headers.get("User-Agent", "Mozilla/5.0 (compatible; JP-Site/1.0)"),
            "Accept-Language": request.headers.get("Accept-Language", "ja-JP,ja;q=0.9"),
            "Accept": request.headers.get("Accept", "*/*"),
        }
        resp = requests.get(url, timeout=12, headers=fwd_headers)
        content_type = resp.headers.get("Content-Type", "application/octet-stream")

        safe_headers = {}
        for k, v in resp.headers.items():
            lk = k.lower()
            if lk in ("x-frame-options", "content-security-policy"):
                continue
            if lk == "content-type":
                continue
            safe_headers[k] = v

        if "text/html" in content_type.lower():
            try:
                text = resp.text
                text = _rewrite_html(text, base)
                return (text.encode(resp.encoding or "utf-8"), resp.status_code, {"Content-Type": "text/html; charset=utf-8", **safe_headers})
            except Exception:
                pass
        if "text/css" in content_type.lower():
            try:
                text = resp.text
                text = _rewrite_css(text, base)
                return (text.encode(resp.encoding or "utf-8"), resp.status_code, {"Content-Type": "text/css; charset=utf-8", **safe_headers})
            except Exception:
                pass

        return (resp.content, resp.status_code, {"Content-Type": content_type, **safe_headers})
    except requests.RequestException:
        return jsonify({"error": "外部サービスに接続できません"}), 502 
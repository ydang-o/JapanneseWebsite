from urllib.parse import urljoin, urlparse, urlencode, parse_qs
from flask import Blueprint, request, jsonify, current_app
import requests
import re
import json
from bs4 import BeautifulSoup
import logging
from pathlib import Path
from typing import Optional, List, Dict

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


def _load_fallback_items(limit: Optional[int] = None):
    """Load static fallback items from the frontend dataset."""
    data_path = Path(current_app.root_path).parent / "frontend" / "src" / "data" / "mercari_items.json"
    try:
        with data_path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        if not isinstance(data, list):
            return []
        if limit is not None and limit > 0:
            return data[:limit]
        return data
    except FileNotFoundError:
        logger.warning("Fallback items file not found: %s", data_path)
    except Exception as exc:
        logger.warning("Failed to load fallback items: %s", exc)
    return []


def _normalize_brand_key(raw: str) -> str:
    if not raw:
        return ""
    return re.sub(r"[^a-z0-9]+", "-", raw.lower())


def _load_brand_items(brand: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
    """Load brand specific items from static dataset or fallback items filtered by keyword."""
    if not brand:
        return []

    key = _normalize_brand_key(brand)
    data_dir = Path(current_app.root_path).parent / "frontend" / "src" / "data" / "brands"
    data_path = data_dir / f"{key}.json"

    try:
        with data_path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        if isinstance(data, list):
            valid_items = [item for item in data if item and isinstance(item, dict)]
            if limit is not None and limit > 0:
                return valid_items[:limit]
            return valid_items
    except FileNotFoundError:
        logger.info("Brand dataset not found for %s, falling back to keyword filter", brand)
    except Exception as exc:
        logger.warning("Failed to load brand items for %s: %s", brand, exc)

    fallback_items = _load_fallback_items(None)
    if not fallback_items:
        return []

    lowered = brand.lower()
    filtered = [item for item in fallback_items if lowered in (item.get("title", "") or "").lower()]
    if limit is not None and limit > 0:
        return filtered[:limit]
    return filtered


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

    fallback_items = _load_fallback_items(limit)
    if fallback_items:
        return jsonify({"items": fallback_items})
    return jsonify({"items": []})


@home_bp.get("/items")
def mercari_items():
    """获取默认商品列表（别名：feed）"""
    limit = min(int(request.args.get("limit", 24)), 60)
    brand = request.args.get("brand", "").strip()

    if brand:
        items = _load_brand_items(brand, limit)
        if items:
            return jsonify({"items": items})
        # fallthrough to general feed when brand not found / empty

    path = "/search/"
    items = _fetch_merch_api(path, limit)
    if items:
        return jsonify({"items": items})

    fallback_items = _load_fallback_items(limit)
    if fallback_items:
        return jsonify({"items": fallback_items})

    return jsonify({"items": []})


@home_bp.get("/search")
def mercari_search():
    """搜索商品 - 直接访问 Mercari 网站"""
    keyword = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    limit = min(int(request.args.get("limit", 24)), 60)
    
    if not keyword and not category:
        return jsonify({"items": []})
    
    # 构建真实的 Mercari 搜索URL
    base = current_app.config["MERCARI_BASE"]
    search_url = f"{base}/search"
    params = {}
    if keyword:
        params["keyword"] = keyword
    if category:
        params["category_id"] = category
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": base,
        }
        resp = requests.get(search_url, params=params, timeout=15, headers=headers)
        resp.raise_for_status()
        
        # 解析HTML提取商品
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        
        # 尝试从 __NEXT_DATA__ 提取
        next_script = soup.find('script', id='__NEXT_DATA__')
        if next_script and next_script.string:
            try:
                data_json = json.loads(next_script.string)
                extracted = _extract_products_from_json(data_json, base, limit)
                items.extend(extracted[:limit])
            except Exception as e:
                logger.debug("Failed to parse __NEXT_DATA__: %s", e)
        
        # 如果没有足够的商品，尝试DOM解析
        if len(items) < limit:
            for link in soup.select('a[href*="/item/"]'):
                if len(items) >= limit:
                    break
                img = link.select_one('img')
                if not img:
                    continue
                
                price_elem = link.find(string=re.compile(r'¥|円|\d+,?\d*'))
                if not price_elem:
                    price_elem = link.select_one('[class*="price"]')
                    if price_elem:
                        price_elem = price_elem.get_text()
                
                title = img.get('alt', '') or img.get('title', '') or link.get('aria-label', '')
                href = link.get('href', '')
                src = img.get('src', '') or img.get('data-src', '')
                
                if title and href and src:
                    price_text = str(price_elem) if price_elem else ''
                    if price_text and not ('¥' in price_text or '円' in price_text):
                        price_text = f"¥{price_text}"
                    items.append({
                        "title": title,
                        "price": price_text,
                        "image": _to_proxy_path(base, src),
                        "link": _to_proxy_path(base, href),
                    })
                    if len(items) >= limit:
                        break
        
        if len(items) < limit:
            fallback_items = _load_fallback_items(None)
            if fallback_items:
                filtered = fallback_items
                if keyword:
                    lowered_kw = keyword.lower()
                    filtered = [item for item in filtered if lowered_kw in (item.get("title", "") or "").lower()]
                if category:
                    pass
                if filtered:
                    return jsonify({"items": filtered[:limit]})

        return jsonify({"items": items[:limit] if items else []})
    
    except Exception as e:
        logger.error("Search failed: %s", e)
        return jsonify({"items": [], "error": "検索に失敗しました"})


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
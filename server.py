from __future__ import annotations

import json
import mimetypes
import base64
import hashlib
import hmac
import os
import re
import secrets
import socket
import threading
import time
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from scireader_import import (
    ARTICLE_URL_RE,
    CELL_URL_RE,
    SCIENCE_URL_RE,
    article_cache_key,
    canonical_cell_url,
    canonical_science_url,
    cell_cache_key,
    parse_article,
    parse_cell_browser_text_article,
    science_cache_key,
)


ASSETS_DIR = Path("assets")
DATA_DIR = Path("data")
ACCOUNT_DATA_PATH = DATA_DIR / "scireader-data.json"
DATA_LOCK = threading.Lock()
SESSION_MAX_AGE = 60 * 60 * 24 * 30


def safe_attachment_name(name: str, fallback: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", name.strip()).strip("-")
    return stem or fallback


def attachment_filename(attachment: dict, index: int, raw: bytes) -> str:
    url = attachment.get("url") or ""
    path_name = urllib.parse.unquote(Path(urllib.parse.urlparse(url).path).name)
    label = attachment.get("name") or ""
    content_type = (attachment.get("contentType") or "").lower()
    is_pdf = raw[:4] == b"%PDF" or "pdf" in content_type
    is_image = raw[:3] == b"\xff\xd8\xff" or raw[:8] == b"\x89PNG\r\n\x1a\n" or content_type.startswith("image/")
    if is_image and label:
        candidate = label
    else:
        candidate = path_name if path_name.lower().endswith(".pdf") else label
    name = safe_attachment_name(candidate, f"document-s{index}.pdf")
    if is_pdf and not name.lower().endswith(".pdf"):
        name = f"{name}.pdf"
    if is_pdf and index == 1:
        name = "document-s1.pdf"
    if is_image and not re.search(r"\.(?:png|jpe?g|webp)$", name, re.I):
        extension = ".png" if raw[:8] == b"\x89PNG\r\n\x1a\n" else ".jpg"
        name = f"{name}{extension}"
    return name


def sanitize_json_value(value):
    if isinstance(value, str):
        return re.sub(r"[\ud800-\udfff]", "?", value)
    if isinstance(value, list):
        return [sanitize_json_value(item) for item in value]
    if isinstance(value, dict):
        return {
            sanitize_json_value(key) if isinstance(key, str) else key: sanitize_json_value(item)
            for key, item in value.items()
        }
    return value


def json_response(handler: SimpleHTTPRequestHandler, status: int, payload: dict, headers: dict | None = None) -> None:
    body = json.dumps(sanitize_json_value(payload), ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    for key, value in (headers or {}).items():
        handler.send_header(key, value)
    handler.end_headers()
    handler.wfile.write(body)


def now_ms() -> int:
    return int(time.time() * 1000)


def default_account_data() -> dict:
    return {"users": {}, "sessions": {}, "papers": {}, "notes": {}}


def load_account_data() -> dict:
    if not ACCOUNT_DATA_PATH.exists():
        return default_account_data()
    try:
        data = json.loads(ACCOUNT_DATA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return default_account_data()
    baseline = default_account_data()
    baseline.update({key: data.get(key, baseline[key]) for key in baseline})
    return baseline


def save_account_data(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = ACCOUNT_DATA_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(ACCOUNT_DATA_PATH)


def clean_username(value: str) -> str:
    username = re.sub(r"[^A-Za-z0-9_.-]+", "", value.strip())[:40]
    if len(username) < 2:
        raise ValueError("Username must be at least 2 characters.")
    return username


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 120_000)
    return salt, digest.hex()


def verify_password(password: str, salt: str, digest: str) -> bool:
    _, candidate = hash_password(password, salt)
    return hmac.compare_digest(candidate, digest)


def paper_id_for(payload: dict) -> str:
    identity = (payload.get("doi") or payload.get("sourceUrl") or payload.get("url") or payload.get("title") or "").strip()
    if not identity:
        raise ValueError("Paper metadata is missing a stable identifier.")
    return hashlib.sha1(identity.lower().encode("utf-8")).hexdigest()[:16]


def session_cookie(token: str) -> str:
    return f"scireader_session={token}; Path=/; Max-Age={SESSION_MAX_AGE}; HttpOnly; SameSite=Lax"


def clear_session_cookie() -> str:
    return "scireader_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"


def extract_openai_text(payload: dict) -> str:
    if payload.get("output_text"):
        return payload["output_text"]
    chunks: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    return "\n".join(chunks).strip()


def ask_openai(payload: dict) -> dict:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Local AI is not configured. Start the server with OPENAI_API_KEY, or use Copy prompt.")

    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        raise ValueError("No AI prompt was provided.")

    content = [{"type": "input_text", "text": prompt}]
    image_data = ((payload.get("context") or {}).get("imageData") or "").strip()
    if image_data.startswith("data:image/"):
        content.append({"type": "input_image", "image_url": image_data})

    request_payload = {
        "model": os.environ.get("SCIREADER_OPENAI_MODEL", "gpt-5-mini"),
        "input": [{"role": "user", "content": content}],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        response_payload = json.loads(response.read().decode("utf-8"))
    return {"answer": extract_openai_text(response_payload) or "No answer text returned."}


class SciReaderHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def cookie_value(self, name: str) -> str:
        cookie = self.headers.get("Cookie") or ""
        for part in cookie.split(";"):
            key, _, value = part.strip().partition("=")
            if key == name:
                return urllib.parse.unquote(value)
        return ""

    def current_user(self, data: dict | None = None) -> dict | None:
        token = self.cookie_value("scireader_session")
        if not token:
            return None
        data = data or load_account_data()
        session = data.get("sessions", {}).get(token)
        if not session:
            return None
        if now_ms() - int(session.get("createdAt", 0)) > SESSION_MAX_AGE * 1000:
            data.get("sessions", {}).pop(token, None)
            save_account_data(data)
            return None
        user_id = session.get("userId")
        for user in data.get("users", {}).values():
            if user.get("id") == user_id:
                return {"id": user["id"], "username": user["username"]}
        return None

    def require_user(self, data: dict | None = None) -> dict:
        user = self.current_user(data)
        if not user:
            raise PermissionError("Please sign in first.")
        return user

    def do_GET(self) -> None:
        route = urllib.parse.urlparse(self.path).path
        if not route.startswith("/api/"):
            super().do_GET()
            return

        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        try:
            with DATA_LOCK:
                data = load_account_data()
                if route == "/api/auth/me":
                    payload = {"user": self.current_user(data)}
                elif route == "/api/library":
                    user = self.require_user(data)
                    papers = list(data.get("papers", {}).get(user["id"], {}).values())
                    payload = {"papers": sorted(papers, key=lambda item: item.get("savedAt", 0), reverse=True)}
                elif route == "/api/notes":
                    user = self.require_user(data)
                    paper_id = (query.get("paperId") or [""])[0]
                    if not paper_id:
                        raise ValueError("Missing paperId.")
                    payload = {"notes": data.get("notes", {}).get(user["id"], {}).get(paper_id, [])}
                else:
                    self.send_error(404)
                    return
        except PermissionError as exc:
            json_response(self, 401, {"error": str(exc)})
            return
        except Exception as exc:
            json_response(self, 400, {"error": str(exc)})
            return

        json_response(self, 200, payload)

    def do_POST(self) -> None:
        route = urllib.parse.urlparse(self.path).path
        if route not in {
            "/api/import",
            "/api/import-snapshot",
            "/api/upload-supplement",
            "/api/ai",
            "/api/auth/signup",
            "/api/auth/login",
            "/api/auth/logout",
            "/api/library",
            "/api/notes",
            "/api/notes/delete",
        }:
            self.send_error(404)
            return

        length = int(self.headers.get("content-length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")

        try:
            if route.startswith("/api/auth/") or route in {"/api/library", "/api/notes", "/api/notes/delete"}:
                article, headers = self.handle_account_post(route, payload)
                json_response(self, 200, article, headers=headers)
                return
            if route == "/api/ai":
                article = ask_openai(payload)
            elif route == "/api/import-snapshot":
                article = self.import_snapshot(payload)
            elif route == "/api/upload-supplement":
                article = self.upload_supplement(payload)
            else:
                url = (payload.get("url") or "").strip()
                article = parse_article(url)
        except PermissionError as exc:
            json_response(self, 401, {"error": str(exc)})
            return
        except Exception as exc:
            json_response(self, 400, {"error": str(exc)})
            return

        json_response(self, 200, article)

    def handle_account_post(self, route: str, payload: dict) -> tuple[dict, dict]:
        with DATA_LOCK:
            data = load_account_data()
            if route in {"/api/auth/signup", "/api/auth/login"}:
                username = clean_username(payload.get("username") or "")
                password = payload.get("password") or ""
                users = data.setdefault("users", {})

                if route == "/api/auth/signup":
                    if username.lower() in users:
                        raise ValueError("That username already exists.")
                    salt, digest = hash_password(password)
                    user = {
                        "id": secrets.token_hex(8),
                        "username": username,
                        "salt": salt,
                        "passwordHash": digest,
                        "createdAt": now_ms(),
                    }
                    users[username.lower()] = user
                else:
                    user = users.get(username.lower())
                    if not user or not verify_password(password, user.get("salt", ""), user.get("passwordHash", "")):
                        raise PermissionError("Invalid username or password.")

                token = secrets.token_urlsafe(32)
                data.setdefault("sessions", {})[token] = {"userId": user["id"], "createdAt": now_ms()}
                save_account_data(data)
                public_user = {"id": user["id"], "username": user["username"]}
                return {"user": public_user}, {"Set-Cookie": session_cookie(token)}

            if route == "/api/auth/logout":
                token = self.cookie_value("scireader_session")
                if token:
                    data.setdefault("sessions", {}).pop(token, None)
                    save_account_data(data)
                return {"user": None}, {"Set-Cookie": clear_session_cookie()}

            user = self.require_user(data)
            user_papers = data.setdefault("papers", {}).setdefault(user["id"], {})
            user_notes = data.setdefault("notes", {}).setdefault(user["id"], {})

            if route == "/api/library":
                paper = {
                    "id": paper_id_for(payload),
                    "title": (payload.get("title") or "Untitled paper").strip(),
                    "authors": (payload.get("authors") or "").strip(),
                    "journal": (payload.get("journal") or "").strip(),
                    "published": (payload.get("published") or "").strip(),
                    "doi": (payload.get("doi") or "").strip(),
                    "sourceUrl": (payload.get("sourceUrl") or payload.get("url") or "").strip(),
                    "savedAt": user_papers.get(paper_id_for(payload), {}).get("savedAt", now_ms()),
                    "updatedAt": now_ms(),
                }
                user_papers[paper["id"]] = paper
                user_notes.setdefault(paper["id"], [])
                save_account_data(data)
                return {"paper": paper, "papers": list(user_papers.values())}, {}

            if route == "/api/notes":
                paper_id = (payload.get("paperId") or "").strip()
                if not paper_id:
                    raise ValueError("Missing paperId.")
                if paper_id not in user_papers:
                    raise ValueError("Save this paper before adding notes.")
                note = {
                    "id": secrets.token_hex(8),
                    "kind": (payload.get("kind") or "note").strip(),
                    "text": (payload.get("text") or "").strip(),
                    "question": (payload.get("question") or "").strip(),
                    "answer": (payload.get("answer") or "").strip(),
                    "contextTitle": (payload.get("contextTitle") or "").strip(),
                    "anchorType": (payload.get("anchorType") or "").strip(),
                    "paragraphId": (payload.get("paragraphId") or "").strip(),
                    "figureId": (payload.get("figureId") or "").strip(),
                    "anchorLabel": (payload.get("anchorLabel") or "").strip(),
                    "createdAt": now_ms(),
                }
                if not note["text"] and not note["answer"]:
                    raise ValueError("Note is empty.")
                user_notes.setdefault(paper_id, []).insert(0, note)
                save_account_data(data)
                return {"note": note, "notes": user_notes[paper_id]}, {}

            if route == "/api/notes/delete":
                paper_id = (payload.get("paperId") or "").strip()
                note_id = (payload.get("noteId") or "").strip()
                notes = user_notes.get(paper_id, [])
                user_notes[paper_id] = [note for note in notes if note.get("id") != note_id]
                save_account_data(data)
                return {"notes": user_notes[paper_id]}, {}

        raise ValueError("Unsupported account action.")

    def import_snapshot(self, payload: dict) -> dict:
        url = (payload.get("url") or "").strip()
        nature_match = ARTICLE_URL_RE.match(url)
        match = CELL_URL_RE.match(url)
        science_match = SCIENCE_URL_RE.match(url)
        if nature_match:
            cache_key = article_cache_key(url)
            journal = "Nature"
        elif match:
            pii = urllib.parse.unquote(match.group("pii"))
            url = canonical_cell_url(url, pii)
            cache_key = cell_cache_key(url, pii)
            journal = match.group("journal")
        elif science_match:
            url = canonical_science_url(url)
            cache_key = science_cache_key(url)
            journal = "Science"
        else:
            raise ValueError("Browser snapshots currently support Nature-family, Cell Press, and Science article URLs.")

        cache_dir = ASSETS_DIR / "imports" / cache_key
        cache_dir.mkdir(parents=True, exist_ok=True)

        body_text = (payload.get("bodyText") or "").strip()
        if not body_text:
            raise ValueError("The browser snapshot did not include visible article text.")
        (cache_dir / "browser-body.txt").write_text(body_text, encoding="utf-8")
        (cache_dir / "browser-meta.json").write_text(
            json.dumps(
                {
                    "url": url,
                    "title": payload.get("title") or "",
                    "journal": journal,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        links = payload.get("links") or []
        (cache_dir / "browser-links.json").write_text(json.dumps(links, ensure_ascii=False, indent=2), encoding="utf-8")
        html = payload.get("html") or ""
        if html:
            (cache_dir / "browser-page.html").write_text(html, encoding="utf-8", errors="replace")

        attachment_errors = []
        for index, attachment in enumerate(payload.get("attachments") or [], 1):
            data = attachment.get("dataBase64") or ""
            if not data:
                if attachment.get("error"):
                    attachment_errors.append(
                        {
                            "name": attachment.get("name") or "",
                            "url": attachment.get("url") or "",
                            "error": attachment.get("error") or "",
                        }
                    )
                continue
            raw = base64.b64decode(data)
            name = attachment_filename(attachment, index, raw)
            (cache_dir / name).write_bytes(raw)
        if attachment_errors:
            (cache_dir / "attachment-errors.json").write_text(
                json.dumps(attachment_errors, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        if match:
            return parse_cell_browser_text_article(url, pii, cache_dir / "browser-body.txt")
        return parse_article(url)

    def upload_supplement(self, payload: dict) -> dict:
        url = (payload.get("url") or "").strip()
        cache_key = safe_attachment_name(payload.get("cacheKey") or "", "")
        if not url:
            raise ValueError("Load a paper before uploading a supplementary PDF.")
        if not cache_key:
            article = parse_article(url)
            cache_key = safe_attachment_name(article.get("cacheKey") or "", "")
        if not cache_key:
            raise ValueError("Could not resolve this paper cache.")

        cache_dir = (ASSETS_DIR / "imports" / cache_key).resolve()
        imports_dir = (ASSETS_DIR / "imports").resolve()
        if imports_dir not in cache_dir.parents:
            raise ValueError("Invalid paper cache.")
        cache_dir.mkdir(parents=True, exist_ok=True)

        data = payload.get("dataBase64") or ""
        if "," in data:
            data = data.split(",", 1)[1]
        if not data:
            raise ValueError("The uploaded PDF was empty.")
        raw = base64.b64decode(data)
        if raw[:4] != b"%PDF":
            raise ValueError("The uploaded file is not a PDF.")

        name = safe_attachment_name(payload.get("name") or "supplement.pdf", "supplement.pdf")
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        target = cache_dir / name
        stem = target.stem
        suffix = target.suffix
        counter = 2
        while target.exists():
            target = cache_dir / f"{stem}-{counter}{suffix}"
            counter += 1
        target.write_bytes(raw)
        return parse_article(url)


def local_ip_addresses() -> list[str]:
    addresses: set[str] = set()
    try:
        hostname = socket.gethostname()
        for item in socket.getaddrinfo(hostname, None, socket.AF_INET):
            address = item[4][0]
            if not address.startswith("127."):
                addresses.add(address)
    except OSError:
        pass
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            address = sock.getsockname()[0]
            if not address.startswith("127."):
                addresses.add(address)
    except OSError:
        pass
    return sorted(addresses)


def main() -> None:
    mimetypes.add_type("application/javascript", ".js")
    host = os.environ.get("SCIREADER_HOST", "127.0.0.1")
    port = int(os.environ.get("SCIREADER_PORT", "4174"))
    server = ThreadingHTTPServer((host, port), SciReaderHandler)
    print(f"SciReader server running at http://127.0.0.1:{port}/index.html")
    if host in {"0.0.0.0", ""}:
        for address in local_ip_addresses():
            print(f"LAN URL: http://{address}:{port}/index.html")
    server.serve_forever()


if __name__ == "__main__":
    main()

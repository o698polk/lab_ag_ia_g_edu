import json
import urllib.error
import urllib.request

base = "http://127.0.0.1:8000"


def get(path, headers=None):
    req = urllib.request.Request(base + path, headers=headers or {})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, r.read()


def post(path, payload, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(
        base + path, data=json.dumps(payload).encode(), headers=h, method="POST"
    )
    with urllib.request.urlopen(req, timeout=12) as r:
        return r.status, r.read()


def main() -> None:
    status, raw = get("/ui/")
    html = raw.decode("utf-8", "replace")
    print("ui", status, "home", "view-home" in html, "v6", "api.js?v=6" in html)

    try:
        status, raw = post("/api/v1/auth/login", {"username": "admin", "password": "Admin123!"})
    except urllib.error.HTTPError as exc:
        print("login_http", exc.code, exc.read().decode())
        raise
    tok = json.loads(raw)
    tok = json.loads(raw)
    print("login_ok", status, bool(tok.get("access_token")))
    auth = {"Authorization": "Bearer " + tok["access_token"]}
    _, me_raw = get("/api/v1/auth/me", auth)
    print("me", json.loads(me_raw)["username"])

    try:
        post("/api/v1/auth/login", {"username": "admin", "password": "x"})
        print("bad_login FAIL")
    except urllib.error.HTTPError as exc:
        print("bad_login", exc.code, exc.read().decode())

    try:
        get("/api/v1/dashboard")
        print("dash_noauth FAIL")
    except urllib.error.HTTPError as exc:
        print("dash_noauth", exc.code)

    try:
        get("/api/v1/auth/me", {"Authorization": "Bearer dead"})
        print("bad_jwt FAIL")
    except urllib.error.HTTPError as exc:
        print("bad_jwt", exc.code)

    _, appjs = get("/ui/js/app.js?v=6")
    print("router", b"function applyRoute" in appjs)


if __name__ == "__main__":
    main()

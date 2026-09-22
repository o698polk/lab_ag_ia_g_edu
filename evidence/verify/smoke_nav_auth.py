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
    status, raw = get("/ui/pages/home.html")
    html = raw.decode("utf-8", "replace")
    print("home", status, "skip" in html.lower() or "Laboratorio" in html)

    status, raw = post(
        "/api/v1/auth/login", {"username": "admin", "password": "Admin123!"}
    )
    tok = json.loads(raw)
    print("login_ok", status, bool(tok.get("access_token")))
    auth = {"Authorization": "Bearer " + tok["access_token"]}
    _, me_raw = get("/api/v1/auth/me", auth)
    print("me", json.loads(me_raw)["username"])

    try:
        post("/api/v1/auth/login", {"username": "admin", "password": "x"})
        print("bad_login FAIL")
    except urllib.error.HTTPError as exc:
        print("bad_login", exc.code)

    try:
        get("/api/v1/dashboard")
        print("dash_noauth FAIL")
    except urllib.error.HTTPError as exc:
        print("dash_noauth", exc.code)

    _, appjs = get("/ui/js/app.js")
    print("legacy_app_shim", b"DEPRECATED" in appjs)

    _, assets = get("/ui/assets/js/core/api.js")
    print("canonical_api", b"SigaApi" in assets or b"api" in assets)


if __name__ == "__main__":
    main()

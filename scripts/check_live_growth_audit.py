"""Read-only production health probe plus a blocked-target API safety test.

No real third-party websites are scanned. The only POST uses a loopback URL
that the API must reject before network activity. Intended for GitHub Actions.
"""
import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def fetch(base, path, *, method="GET", payload=None, timeout=16):
    url = base.rstrip("/") + path
    headers = {
        "Accept": "application/json" if path.endswith("api") else "text/html, application/json, */*",
        "User-Agent": "GrowthAuditPro-DeploymentCheck/1.0",
        "Cache-Control": "no-cache",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = Request(url, data=payload, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(200_000), resp.headers.get("content-type", ""), resp.geturl()
    except HTTPError as exc:
        return exc.code, exc.read(10_000), exc.headers.get("content-type", ""), exc.geturl()


def verify(base):
    parts = urlsplit(base)
    if parts.scheme != "https" or not parts.netloc or parts.username or parts.password or parts.path not in ("", "/"):
        raise ValueError("BASE must be a single HTTPS origin with no credentials or path")
    checks = []
    status, body, content_type, final_url = fetch(base, "/growth-audit")
    text = body.decode("utf-8", "replace")
    checks.append(("Frontend 200 HTML", status == 200 and "html" in content_type.lower()))
    checks.append(("Audit form rendered", 'id="audit-form"' in text and "GrowthAudit Pro" in text))
    checks.append(("Frontend stayed on origin", urlsplit(final_url).hostname == parts.hostname))

    for asset, marker in (("/growth-audit.js", "normalizedInput"), ("/growth-audit.css", ".finding")):
        status, data, _, final_url = fetch(base, asset)
        checks.append((asset + " 200 and expected content", status == 200 and marker.encode() in data))
        checks.append((asset + " same-origin", urlsplit(final_url).hostname == parts.hostname))

    status, data, content_type, final_url = fetch(base, "/growth-audit-api")
    try:
        api = json.loads(data)
    except ValueError:
        api = {}
    print(f"INFO: API GET status={status}, mime={content_type.split(';')[0]}, json_keys={sorted(api.keys())[:8]}", flush=True)
    checks.append(("API GET returns service JSON", status == 200 and
                   "json" in content_type.lower() and api.get("service") == "GrowthAudit Pro"))
    checks.append(("API route same-origin", urlsplit(final_url).hostname == parts.hostname))

    # Safety contract: the API must reject a loopback target, not fetch it.
    invalid = json.dumps({"url": "http://127.0.0.1/"}).encode()
    status, data, _, _ = fetch(base, "/growth-audit-api", method="POST", payload=invalid)
    try:
        rejected = json.loads(data)
    except ValueError:
        rejected = {}
    print(f"INFO: API POST rejected status={status}, error={rejected.get('error', 'none')}", flush=True)
    checks.append(("Loopback target rejected", status == 400 and
                   rejected.get("error") == "unsafe_or_restricted"))

    for label, good in checks:
        print(("PASS" if good else "FAIL") + ": " + label, flush=True)
    return all(good for _, good in checks)


def main():
    parser = argparse.ArgumentParser(description="Check production GrowthAudit page and API contract")
    parser.add_argument("--base", default="https://www.nextgentechdev.com")
    args = parser.parse_args()
    try:
        ok = verify(args.base)
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        print("FAIL: production probe could not complete: " + str(exc), file=sys.stderr)
        return 1
    print("Production GrowthAudit contract " + ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

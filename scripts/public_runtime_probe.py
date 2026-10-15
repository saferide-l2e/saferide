"""Read-only public HTTP checks. Never post or use live production DB in QA."""
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

VERCEL = "https://saferide-eight.vercel.app"
RENDER = "https://saferide-friday-web.onrender.com"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def probe(url):
    """Preserve redirect status, TLS verification, and exact redirect location."""
    opener = build_opener(NoRedirect())
    request = Request(url, headers={"User-Agent": "SafeRide-public-read-only-release-check"})
    try:
        with opener.open(request, timeout=65) as response:
            return response.status, dict(response.headers.items()), response.read(512)
    except HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read(512)


def checked(url, expected, redirect_host=None, redirect_path=None):
    last = None
    for attempt in range(3):
        try:
            status, headers, body = probe(url)
            location = headers.get("Location") or headers.get("location", "")
            if (status == expected
                and (not redirect_host or urlparse(location).hostname == redirect_host)
                and (not redirect_path or urlparse(location).path == redirect_path)):
                print(f"PASS {status}: {url}" + (f" -> {location}" if location else ""))
                return body
            last = f"HTTP {status}; redirect host {urlparse(location).hostname}"
        except (URLError, TimeoutError, OSError) as exc:
            last = f"{type(exc).__name__}: {exc}"
        if attempt < 2:
            time.sleep(5)
    raise AssertionError(f"FAIL {url}: expected {expected} ({redirect_host}); got {last}")


if __name__ == "__main__":
    checked(VERCEL + "/accounts/register/", 307, redirect_host="saferide-friday-web.onrender.com")
    checked(VERCEL + "/", 307, redirect_host="saferide-friday-web.onrender.com")
    checked(VERCEL + "/accounts/login/", 307, redirect_host="saferide-friday-web.onrender.com")
    health = checked(RENDER + "/health/", 200)
    assert json.loads(health) == {"status": "ok"}
    checked(RENDER + "/", 200)
    checked(RENDER + "/accounts/register/", 200)
    checked(RENDER + "/accounts/login/", 200)
    # An anonymous verification request must never disclose a private form.
    checked(RENDER + "/verification/", 302, redirect_path="/accounts/login/")
    print("PASS: all public read-only release probes completed; no production POSTs or test users.")

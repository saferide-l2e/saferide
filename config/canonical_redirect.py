"""Temporary canonical-host handoff for the SafeRide demo.

Vercel lacks database connectivity and its project redirect configuration is not
taking effect for this Django framework deployment. Redirect only the known,
verified SafeRide Vercel production hostnames to the database-backed Render app.

Safe, reversible: set SAFERIDE_VERCEL_CANONICAL_REDIRECT=false after an isolated,
TLS-connected Vercel PostgreSQL deployment is independently verified.
"""
import os

from django.http import HttpResponse

CANONICAL = "https://saferide-friday-web.onrender.com"
VERCEL_PRODUCTION_HOSTS = frozenset({
    "saferide-eight.vercel.app",
    "saferide-femo1.vercel.app",
    "saferide-git-main-femo1.vercel.app",
})


class VercelDemoCanonicalRedirectMiddleware:
    """Redirect before sessions/auth/database access without leaking POST bodies."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        enabled = os.getenv("SAFERIDE_VERCEL_CANONICAL_REDIRECT", "true").lower() == "true"
        if enabled and request.get_host().split(":", 1)[0].lower() in VERCEL_PRODUCTION_HOSTS:
            destination = CANONICAL + request.get_full_path()
            # Stale Vercel forms must not resend credentials/CSRF tokens to
            # another origin. 303 converts unsafe method to a safe GET.
            status = 307 if request.method in {"GET", "HEAD"} else 303
            response = HttpResponse(status=status)
            response["Location"] = destination
            response["Cache-Control"] = "no-store"
            return response
        return self.get_response(request)

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from apps.accounts.models import Role


def home(request):
    return render(request, "home.html")


def health(request):
    return JsonResponse({"status": "ok"})


@login_required
def dashboard(request):
    """Role-aware landing page after sign-in."""
    context = {"role": request.user.role}
    if request.user.is_staff:
        context["panel"] = "staff"
    elif request.user.role == Role.DRIVER:
        context["panel"] = "driver"
    else:
        context["panel"] = "passenger"
    return render(request, "dashboard.html", context)

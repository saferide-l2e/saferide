from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.audit.services import record

from .forms import EmailAuthenticationForm, RegistrationForm


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        # Eligibility always begins at NOT_SUBMITTED (never self-approved).
        from apps.verification.services import ensure_verification

        ensure_verification(user)
        record(user, "account.registered", user, {"role": user.role})
        login(request, user)
        messages.success(request, "Account created. Submit your demo verification to continue.")
        return redirect("core:dashboard")
    return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        record(form.get_user(), "account.login", form.get_user())
        return redirect("core:dashboard")
    return render(request, "accounts/login.html", {"form": form})


@require_http_methods(["POST", "GET"])
def logout_view(request):
    if request.user.is_authenticated:
        record(request.user, "account.logout", request.user)
        logout(request)
        messages.info(request, "You have been signed out.")
    return redirect("core:home")


@login_required
def profile(request):
    return render(request, "accounts/profile.html", {"profile_user": request.user})

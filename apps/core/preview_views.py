"""Internal-only visual review of existing SafeRide Django templates.

Enabled only by SAFERIDE_VISUAL_PREVIEW=true in the isolated preview branch.
No database reads, account creation, seat holds, code acceptance, SOS dispatch,
or form submissions. Data is deliberately fictional. Never import into production.
"""

from datetime import UTC, datetime, timedelta

from django import forms
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


PAGE_GROUPS = (
    ("Discover", (
        ("search", "Find a bus", "passenger/search.html"),
        ("results", "Bus results", "passenger/results.html"),
        ("bus-detail", "Bus details & driver", "passenger/bus_detail.html"),
        ("route-updates", "Route updates", "safety/route_feed.html"),
    )),
    ("Journey", (
        ("reservation", "10-minute seat hold", "booking/hold.html"),
        ("queue", "Virtual queue", "booking/waitlist.html"),
        ("offer", "Two-minute seat offer", "booking/offer.html"),
        ("trip", "Journey progress", "passenger/trip.html"),
        ("history", "Passenger trip history", "passenger/history.html"),
        ("review", "Rate a journey", "safety/review.html"),
    )),
    ("Safety & Accounts", (
        ("register", "Create an account", "accounts/register.html"),
        ("login", "Sign in", "accounts/login.html"),
        ("verification", "Verification status", "accounts/verification.html"),
        ("passenger-profile", "Passenger profile", "passenger/profile.html"),
        ("driver-profile", "Driver profile", "driver/profile.html"),
        ("report", "Private safety report", "safety/report.html"),
        ("contribute", "Share a route update", "safety/route_update_form.html"),
    )),
    ("Driver Space", (
        ("driver-dashboard", "Driver dashboard", "driver/dashboard.html"),
        ("vehicles", "My vehicles", "driver/vehicle_list.html"),
        ("register-vehicle", "Register a vehicle", "driver/vehicle_form.html"),
        ("publish-departure", "Publish departure", "driver/publish_departure.html"),
        ("departure-detail", "Manage departure", "driver/departure_detail.html"),
        ("roster", "Boarding roster", "driver/roster.html"),
        ("boarding", "Check in a passenger", "driver/check_in.html"),
        ("driver-history", "Driver trip history", "driver/history.html"),
    )),
)
PAGES = {slug: template for _group, entries in PAGE_GROUPS for slug, _label, template in entries}


class RegistrationForm(forms.Form):
    role = forms.ChoiceField(choices=(("PASSENGER", "Passenger"), ("DRIVER", "Driver")))
    display_name = forms.CharField(label="Your name", initial="Tomi Ade")
    email = forms.EmailField(label="Email address", initial="tomi@example.test")
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)
    privacy_acknowledged = forms.BooleanField(label="I agree to the privacy notice", required=True)


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email address", initial="tomi@example.test")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)


class DeclarationForm(forms.Form):
    declaration = forms.ChoiceField(
        label="Your role", choices=(("PASSENGER", "Passenger"), ("DRIVER", "Driver"))
    )
    fictional_declaration = forms.BooleanField(label="I confirm these example details are fictional")


class VehicleForm(forms.Form):
    vehicle_type = forms.ChoiceField(choices=(("MINIBUS", "Minibus"), ("BUS", "Bus")))
    plate_display = forms.CharField(label="Vehicle plate", initial="SRD-204")
    seat_capacity = forms.IntegerField(label="Seats", min_value=1, initial=14)


class DepartureForm(forms.Form):
    vehicle = forms.ChoiceField(choices=(("1", "Minibus · SRD-204"),))
    route = forms.ChoiceField(choices=(("1", "Jibowu → Mile 2"),))
    boarding_point = forms.CharField(initial="Jibowu Park")
    scheduled_departure_at = forms.DateTimeField(
        label="Departure date and time", widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )


class ReviewForm(forms.Form):
    stars = forms.ChoiceField(label="Overall rating", choices=tuple(
        (str(n), f"{n} {'star' if n == 1 else 'stars'}") for n in range(5, 0, -1)
    ))
    comment = forms.CharField(label="What went well?", required=False, widget=forms.Textarea)


class ReportForm(forms.Form):
    category = forms.ChoiceField(choices=(("SAFETY", "Safety concern"), ("OTHER", "Other")))
    description = forms.CharField(label="Describe what happened", widget=forms.Textarea)


class CommunityForm(forms.Form):
    route = forms.ChoiceField(choices=(("JIBOWU-MILE2", "Jibowu → Mile 2"),))
    category = forms.ChoiceField(choices=(("BOARDING", "Boarding update"), ("TRAFFIC", "Traffic")))
    note = forms.CharField(label="Route update", widget=forms.Textarea)


NOW = datetime(2026, 10, 14, 20, 0, tzinfo=UTC)


def uri(slug):
    """Static visual-review URL; never a booking or approval endpoint."""
    return f"/preview/{slug}/"


def _sample():
    """Only safe, fictional public fields. No model instances or private credentials."""
    departure = {
        "route_label": "Jibowu → Mile 2",
        "scheduled_departure_at": NOW + timedelta(hours=4),
        "boarding_point": "Jibowu Park",
        "destination_point": "Mile 2",
        "vehicle_type_display": "Minibus",
        "plate_display": "SRD-204",
        "driver_name": "Amina O.",
        "driver_public_name": "Amina O.",
        "driver_initials": "AO",
        "driver_approved": True,
        "available_seats": 5,
        "capacity": 14,
        "is_open": True,
        "is_full": False,
        "status": "BOARDING_OPEN",
        "status_label": "Boarding open",
        "detail_url": uri("bus-detail"),
        "boarded_count": 7,
        "held_count": 2,
    }
    hold = {
        "reference": "SR-1024",
        "status": "HELD",
        "route_label": departure["route_label"],
        "boarding_point": departure["boarding_point"],
        "plate_display": departure["plate_display"],
        "expires_at": NOW + timedelta(seconds=600),
        "boarding_code": "482913",
    }
    trip = {
        "route_label": departure["route_label"],
        "plate_display": departure["plate_display"],
        "display_status": "On the way",
        "booking_status": "BOARDED",
        "booking_held_at": NOW - timedelta(minutes=35),
        "boarded_at": NOW - timedelta(minutes=25),
        "en_route_at": NOW - timedelta(minutes=18),
        "driver_arrived_at": None,
        "passenger_confirmed_at": None,
    }
    passenger = {
        "initials": "TA", "public_display_name": "Tomi A.",
        "short_reference": "SR-1024", "status": "HELD", "verified": True,
        "expires_at": NOW + timedelta(seconds=600),
    }
    vehicle = {
        "vehicle_type_display": "Minibus", "plate_display": "SRD-204",
        "seat_capacity": 14, "approval_status": "APPROVED",
        "can_publish": True, "publish_url": uri("publish-departure"),
    }
    return {
        "form_action": uri("register"),
        "register_url": uri("register"), "login_url": uri("login"),
        "search_url": uri("search"), "origin": "Jibowu", "destination": "Mile 2",
        "has_searched": True,
        "buses": [departure, {**departure, "plate_display": "SRD-208",
                               "available_seats": 0, "is_full": True,
                               "driver_name": "Tunde K.", "detail_url": uri("bus-detail")}],
        "bus": departure, "route_notices": [],
        "booking": hold, "server_now": NOW,
        "entry": {"status": "WAITING", "route_label": departure["route_label"],
                  "position": 4, "people_ahead": 3},
        "offer": {"status": "OFFERED", "route_label": departure["route_label"],
                  "expires_at": NOW + timedelta(seconds=120)},
        "trip": trip,
        "trips": [{**trip, "departed_at": NOW - timedelta(days=2),
                   "display_status": "Completed", "detail_url": uri("trip")}],
        "departure": {**departure, "vehicle_plate": departure["plate_display"],
                      "detail_url": uri("departure-detail")},
        "departures": [{**departure, "detail_url": uri("departure-detail")}],
        "roster": [passenger, {**passenger, "public_display_name": "Daniel I.",
                                "initials": "DI", "short_reference": "SR-1031",
                                "status": "BOARDED"}],
        "boarded_count": 7, "held_count": 2, "capacity": 14,
        "upcoming_count": 2, "approved_vehicle_count": 1, "boarded_today_count": 7,
        "vehicles": [vehicle, {**vehicle, "plate_display": "SRD-208",
                              "approval_status": "PENDING", "can_publish": False}],
        "updates": [{"status": "APPROVED", "type_label": "Boarding point",
                     "route_label": departure["route_label"],
                     "note": "Boarding point information posted for staff review.",
                     "published_at": NOW}],
        "route_label": departure["route_label"],
        "profile": {"initials": "AO", "public_display_name": "Amina O.", "is_approved": True},
        "status": "PENDING", "can_submit": True,
        "can_reserve": False, "can_join_waitlist": False, "can_join": False,
        "can_review": True, "trip_is_completed": True,
        "can_report": True, "can_contribute": True,
        "can_register": True, "can_publish": True, "can_check_in": True,
        "review_action": uri("review"), "report_action": uri("report"),
        "form_action": uri("register"), "submit_action": uri("verification"),
        "join_action": uri("queue"), "can_advance": False,
        "verification_url": uri("verification"), "vehicle_list_url": uri("vehicles"),
        "register_url": uri("register-vehicle"), "publish_url": uri("publish-departure"),
        "dashboard_url": uri("driver-dashboard"),
        "history_url": uri("history"), "reporting_url": uri("report"),
        "rating_url": uri("review"), "feed_url": uri("route-updates"),
        "contribute_url": uri("contribute"), "roster_url": uri("roster"),
        "checkin_url": uri("boarding"), "queue_url": uri("queue"),
        "offer_url": uri("offer"),
        "time_zone_label": "Africa/Lagos (WAT, UTC+1)",
    }


@never_cache
@require_GET
def gallery(request):
    response = render(request, "preview/gallery.html", {"groups": PAGE_GROUPS, "preview_gallery_url": "/preview/"})
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


@never_cache
@require_GET
def page(request, slug):
    template = PAGES.get(slug)
    if not template:
        raise Http404("Unknown review page")
    context = _sample()
    context["preview_gallery_url"] = "/preview/"
    if slug == "register":
        context["form"] = RegistrationForm()
        context["form_action"] = uri("register")
    elif slug == "login":
        context["form"] = LoginForm()
        context["form_action"] = uri("login")
    elif slug == "verification":
        context["form"] = DeclarationForm()
    elif slug == "register-vehicle":
        context["form"] = VehicleForm()
        context["form_action"] = uri("register-vehicle")
    elif slug == "publish-departure":
        context["form"] = DepartureForm()
        context["form_action"] = uri("publish-departure")
    elif slug == "review":
        context["form"] = ReviewForm()
    elif slug == "report":
        context["form"] = ReportForm()
    elif slug == "contribute":
        context["form"] = CommunityForm()
        context["form_action"] = uri("contribute")
    elif slug == "boarding":
        context["checkin_action"] = uri("boarding")
    elif slug == "driver-dashboard":
        context["publish_url"] = uri("publish-departure")
    elif slug == "vehicles":
        context["register_url"] = uri("register-vehicle")
    elif slug == "roster":
        context["checkin_url"] = uri("boarding")
    elif slug == "bus-detail":
        context["action_message"] = "Seat booking becomes available after backend integration."
    elif slug == "offer":
        context["accept_action"] = uri("offer")
        context["decline_action"] = uri("offer")
    # JS-enhanced countdowns show server timestamps from a fixed fictional clock;
    # no live poll endpoints, no real bookings, and all POST requests return HTTP 405.
    response = render(request, template, context)
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response

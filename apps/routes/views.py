from django.shortcuts import render

from .models import Route


def route_list(request):
    routes = Route.objects.filter(is_active=True)
    origin = (request.GET.get("origin") or "").strip()
    destination = (request.GET.get("destination") or "").strip()
    if origin:
        routes = routes.filter(origin_name__icontains=origin)
    if destination:
        routes = routes.filter(destination_name__icontains=destination)
    return render(
        request,
        "passenger/routes.html",
        {"routes": routes, "origin": origin, "destination": destination},
    )

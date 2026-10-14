import pytest

from apps.routes.models import Route


@pytest.mark.django_db
def test_demo_route_is_seeded_with_explicit_demo_label():
    route, _ = Route.objects.get_or_create(
        display_label="DEMO: Jibowu → Mile 2",
        defaults={
            "origin_name": "Jibowu",
            "destination_name": "Mile 2",
            "boarding_point": "DEMO boarding point — Jibowu",
            "destination_point": "DEMO destination point — Mile 2",
            "is_demo": True,
        },
    )

    assert route.origin_name == "Jibowu"
    assert route.destination_name == "Mile 2"
    assert route.display_label.startswith("DEMO:")
    assert route.boarding_point.startswith("DEMO")

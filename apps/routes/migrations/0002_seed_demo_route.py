from typing import ClassVar

from django.db import migrations


def create_demo_route(apps, schema_editor):
    Route = apps.get_model("routes", "Route")
    Route.objects.get_or_create(
        display_label="DEMO: Jibowu → Mile 2",
        defaults={
            "origin_name": "Jibowu",
            "destination_name": "Mile 2",
            "boarding_point": "DEMO boarding point — Jibowu",
            "destination_point": "DEMO destination point — Mile 2",
            "is_demo": True,
        },
    )


def remove_demo_route(apps, schema_editor):
    Route = apps.get_model("routes", "Route")
    Route.objects.filter(display_label="DEMO: Jibowu → Mile 2", is_demo=True).delete()


class Migration(migrations.Migration):
    dependencies: ClassVar[list] = [("routes", "0001_initial")]

    operations: ClassVar[list] = [migrations.RunPython(create_demo_route, remove_demo_route)]

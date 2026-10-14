import uuid
from typing import ClassVar

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


def install_driver_role_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    statements = [
        """
        CREATE FUNCTION vehicles_require_driver_role() RETURNS trigger AS $$
        DECLARE account_role varchar;
        BEGIN
            SELECT role INTO account_role FROM accounts_user WHERE id = NEW.user_id FOR UPDATE;
            IF account_role IS DISTINCT FROM 'DRIVER' THEN
                RAISE EXCEPTION 'A driver profile requires a DRIVER account.'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """,
        """
        CREATE TRIGGER vehicles_driver_profile_role_guard
        BEFORE INSERT OR UPDATE OF user_id ON vehicles_driverprofile
        FOR EACH ROW EXECUTE FUNCTION vehicles_require_driver_role();
        """,
        """
        CREATE FUNCTION vehicles_normalize_plate() RETURNS trigger AS $$
        BEGIN
            NEW.plate_normalized := regexp_replace(upper(NEW.plate_display), '[^A-Z0-9]', '', 'g');
            IF NEW.plate_normalized = '' THEN
                RAISE EXCEPTION 'A vehicle plate must contain a letter or number.'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """,
        """
        CREATE TRIGGER vehicles_plate_normalization_guard
        BEFORE INSERT OR UPDATE ON vehicles_vehicle
        FOR EACH ROW EXECUTE FUNCTION vehicles_normalize_plate();
        """,
        """
        CREATE FUNCTION vehicles_preserve_driver_profile_role() RETURNS trigger AS $$
        BEGIN
            IF NEW.role <> 'DRIVER' AND OLD.role = 'DRIVER'
                AND EXISTS (
                    SELECT 1 FROM vehicles_driverprofile WHERE user_id = OLD.id
                ) THEN
                RAISE EXCEPTION 'A user with a driver profile must remain a DRIVER.'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """,
        """
        CREATE TRIGGER vehicles_user_role_guard
        BEFORE UPDATE OF role ON accounts_user
        FOR EACH ROW EXECUTE FUNCTION vehicles_preserve_driver_profile_role();
        """,
    ]
    for statement in statements:
        schema_editor.execute(statement)


def remove_driver_role_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute(
        "DROP TRIGGER IF EXISTS vehicles_driver_profile_role_guard ON vehicles_driverprofile"
    )
    schema_editor.execute("DROP FUNCTION IF EXISTS vehicles_require_driver_role()")
    schema_editor.execute("DROP TRIGGER IF EXISTS vehicles_plate_normalization_guard ON vehicles_vehicle")
    schema_editor.execute("DROP FUNCTION IF EXISTS vehicles_normalize_plate()")
    schema_editor.execute("DROP TRIGGER IF EXISTS vehicles_user_role_guard ON accounts_user")
    schema_editor.execute("DROP FUNCTION IF EXISTS vehicles_preserve_driver_profile_role()")


class Migration(migrations.Migration):
    initial = True

    dependencies: ClassVar[list] = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations: ClassVar[list] = [
        migrations.CreateModel(
            name="DriverProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("public_display_name", models.CharField(blank=True, max_length=150)),
                (
                    "licence_status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending review"),
                            ("APPROVED", "Approved"),
                            ("REJECTED", "Rejected"),
                            ("SUSPENDED", "Suspended"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="driver_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [models.Index(fields=["licence_status"], name="vehicles_dr_licence_4d086a_idx")],
            },
        ),
        migrations.CreateModel(
            name="Vehicle",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("plate_display", models.CharField(max_length=20)),
                ("plate_normalized", models.CharField(editable=False, max_length=20, unique=True)),
                (
                    "vehicle_type",
                    models.CharField(
                        choices=[("BUS", "Bus"), ("MINIBUS", "Minibus")],
                        max_length=10,
                    ),
                ),
                ("seat_capacity", models.PositiveIntegerField()),
                (
                    "approval_status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("APPROVED", "Approved"),
                            ("REJECTED", "Rejected"),
                            ("SUSPENDED", "Suspended"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                (
                    "driver",
                    models.ForeignKey(
                        db_index=False,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="vehicles",
                        to="vehicles.driverprofile",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["driver"], name="vehicle_driver_idx"),
                    models.Index(fields=["approval_status"], name="vehicle_approval_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=Q(seat_capacity__gt=0),
                        name="vehicle_seat_capacity_positive",
                    ),
                ],
            },
        ),
        migrations.RunPython(install_driver_role_guards, remove_driver_role_guards),
    ]

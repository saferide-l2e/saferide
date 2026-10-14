from typing import ClassVar

from django.db import migrations


def install_departure_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    statements = [
        """
        CREATE FUNCTION departures_preserve_capacity_and_owner() RETURNS trigger AS $$
        DECLARE
            vehicle_driver bigint;
            vehicle_capacity integer;
            vehicle_status varchar;
        BEGIN
            SELECT driver_id, seat_capacity, approval_status
                INTO vehicle_driver, vehicle_capacity, vehicle_status
                FROM vehicles_vehicle WHERE id = NEW.vehicle_id FOR SHARE;

            IF vehicle_driver IS DISTINCT FROM NEW.driver_id THEN
                RAISE EXCEPTION 'The vehicle must belong to the departure driver.'
                    USING ERRCODE = '23514';
            END IF;

            IF TG_OP = 'INSERT' THEN
                IF NEW.status <> 'DRAFT' THEN
                    RAISE EXCEPTION 'A departure must be created as a draft.'
                        USING ERRCODE = '23514';
                END IF;
                NEW.capacity_snapshot := vehicle_capacity;
            ELSE
                IF NEW.capacity_snapshot <> OLD.capacity_snapshot THEN
                    RAISE EXCEPTION 'A departure capacity snapshot cannot be changed.'
                        USING ERRCODE = '23514';
                END IF;
                IF NEW.status = 'BOARDING_OPEN'
                    AND OLD.status <> 'BOARDING_OPEN'
                    AND vehicle_status <> 'APPROVED' THEN
                    RAISE EXCEPTION 'Only an approved vehicle can be published.'
                        USING ERRCODE = '23514';
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """,
        """
        CREATE TRIGGER departures_integrity_guard
        BEFORE INSERT OR UPDATE ON departures_departure
        FOR EACH ROW EXECUTE FUNCTION departures_preserve_capacity_and_owner();
        """,
    ]
    for statement in statements:
        schema_editor.execute(statement)


def remove_departure_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("DROP TRIGGER IF EXISTS departures_integrity_guard ON departures_departure")
    schema_editor.execute("DROP FUNCTION IF EXISTS departures_preserve_capacity_and_owner()")


class Migration(migrations.Migration):
    dependencies: ClassVar[list] = [
        ("departures", "0001_initial"),
        ("vehicles", "0001_initial"),
    ]

    operations: ClassVar[list] = [
        migrations.RunPython(install_departure_guards, remove_departure_guards)
    ]

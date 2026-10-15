from django.test import TestCase, override_settings
from django.core.management import call_command
from django.core.management.base import CommandError
from apps.accounts.models import User
from apps.departures.models import Departure
from apps.vehicles.models import Vehicle
from apps.safety.models import IncidentReport

class SeedDemoCommandTests(TestCase):

    @override_settings(DEBUG=True)
    def test_command_requires_explicit_opt_in_flag(self):
        """The command must fail if --reset-safe-demo flag is missing."""
        with self.assertRaises(CommandError) as ctx:
            call_command('seed_demo')
        self.assertIn("You must provide the --reset-safe-demo flag", str(ctx.exception))

    @override_settings(DEBUG=False, ALLOW_PRODUCTION_DEMO_SEED=False)
    def test_production_environment_blocks_execution(self):
        """The command must explicitly refuse execution on production blocks."""
        with self.assertRaises(CommandError) as ctx:
            call_command('seed_demo', '--reset-safe-demo')
        self.assertIn("Execution Refused: Seeding is blocked in production", str(ctx.exception))

    @override_settings(DEBUG=True)
    def test_idempotence_and_expected_counts(self):
        """Running the command twice must not duplicate data fields or counts."""
        call_command('seed_demo', '--reset-safe-demo')
        
        user_count_initial = User.objects.count()
        vehicle_count_initial = Vehicle.objects.count()
        departure_count_initial = Departure.objects.count()
        report_count_initial = IncidentReport.objects.count()

        # Check for matching target demo attributes
        demo_vehicle = Vehicle.objects.get(plate_normalized="DEMO001")
        self.assertEqual(demo_vehicle.capacity, 1)

        # Rerun command to verify idempotence
        call_command('seed_demo', '--reset-safe-demo')

        self.assertEqual(User.objects.count(), user_count_initial)
        self.assertEqual(Vehicle.objects.count(), vehicle_count_initial)
        self.assertEqual(Departure.objects.count(), departure_count_initial)
        self.assertEqual(IncidentReport.objects.count(), report_count_initial)

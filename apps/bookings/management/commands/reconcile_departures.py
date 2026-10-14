"""Reconcile expired seat holds and waitlist offers (architecture: periodic job).

Run this on a schedule (cron/worker). Correctness never depends on it — every
inventory operation reconciles under lock — but it keeps dashboards fresh and
advances the waitlist promptly.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.bookings.services import reconcile
from apps.departures.models import Departure, DepartureStatus


class Command(BaseCommand):
    help = "Expire stale holds/offers and advance waitlists for open departures."

    def handle(self, *args, **options):
        now = timezone.now()
        open_departures = Departure.objects.filter(
            status__in=[
                DepartureStatus.BOARDING_OPEN,
                DepartureStatus.BOARDING_CLOSED,
                DepartureStatus.EN_ROUTE,
            ]
        )
        count = 0
        for departure in open_departures.iterator():
            reconcile(departure, now)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Reconciled {count} departure(s)."))

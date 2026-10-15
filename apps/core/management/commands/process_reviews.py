"""Run timed approvals independently of page visits; restart-safe via DB state."""
import logging
import signal
from threading import Event

from django.core.management.base import BaseCommand
from django.db import close_old_connections

from apps.core.automatic_reviews import process_due_reviews

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Approve eligible pending submissions after five seconds; --watch runs the worker."

    def add_arguments(self, parser):
        parser.add_argument("--watch", action="store_true")

    def handle(self, *args, **options):
        if not options["watch"]:
            self.stdout.write(str(process_due_reviews()))
            return
        stopped = Event()
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda *_: stopped.set())
        self.stdout.write("Automatic review worker started (five-second delay).")
        while not stopped.is_set():
            try:
                close_old_connections()
                counts = process_due_reviews()
                if any(counts.values()):
                    self.stdout.write(str(counts))
            except Exception:
                # Do not log exception text: database URLs or submitted data can
                # appear in driver errors. Restart-safe timestamps retain work.
                logger.error("Automatic review processing failed; retrying.")
            finally:
                close_old_connections()
            stopped.wait(.25)

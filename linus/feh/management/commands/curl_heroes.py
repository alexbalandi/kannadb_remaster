import os

from django.conf import settings
from django.core.management.base import BaseCommand

from linus.feh.poro.porocurler_v2 import PHASES, CurlAll


def GetPklOutputFile():
    output_file_root = os.path.join(settings.MEDIA_ROOT, "poro")

    if not os.path.isdir(output_file_root):
        os.mkdir(output_file_root)

    filename = "poro.pkl"

    return os.path.join(output_file_root, filename)


def GetPklHeroURLFile():
    output_file_root = os.path.join(settings.MEDIA_ROOT, "poro")

    if not os.path.isdir(output_file_root):
        os.mkdir(output_file_root)

    filename = "porohero.pkl"

    return os.path.join(output_file_root, filename)


def GetPklDirectory():
    output_file_root = os.path.join(settings.MEDIA_ROOT, "poro", "icons")

    if not os.path.isdir(output_file_root):
        os.mkdir(output_file_root)

    return output_file_root


class Command(BaseCommand):
    help = "Curl heroes from gamepedia."

    def add_arguments(self, parser):
        parser.add_argument(
            "--delay",
            type=float,
            default=1.0,
            help="Delay in seconds between API requests (default: 1.0). Increase if you encounter rate limiting.",
        )

    def handle(self, *args, **options):
        request_delay = options["delay"]
        self.stdout.write(f"Using request delay: {request_delay} seconds")
        for phase in range(PHASES):
            self.stdout.write(f"Starting phase {phase}...")
            CurlAll(phase, GetPklOutputFile(), request_delay=request_delay)
            self.stdout.write(self.style.SUCCESS(f"Phase {phase} completed."))

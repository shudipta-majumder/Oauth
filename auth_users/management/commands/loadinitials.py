import json
import os
from functools import cached_property

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "load initial core users like management, cbo, admin"
    required_datetime_fixed_in_fixtures = ["user_fixture"]

    def fix_timestamp(self, filename: str):
        with open(f"{filename}.json") as file:
            data = json.load(file)

        for item in data:
            if "fields" in item:
                item["fields"]["created_at"] = timezone.now().isoformat()
                item["fields"]["updated_at"] = timezone.now().isoformat()

        with open(f"{filename}.json", "w") as file:
            json.dump(data, file, indent=4)

        self.stdout.write("Updated fixture data with current timestamps.")

    @cached_property
    def fixture_dirs(self):
        """
        Find fixtures in all available fixture directories.
        """
        all_fixtures = []
        all_fixtures.extend(settings.FIXTURE_DIRS)

        for app_config in apps.get_app_configs():
            app_fixture_dir = os.path.join(app_config.path, "fixtures")
            if os.path.isdir(app_fixture_dir):
                all_fixtures.append(app_fixture_dir)

        return all_fixtures

    def get_fixture_name_and_dirs(self, fixture_name):
        dirname, basename = os.path.split(fixture_name)
        if os.path.isabs(fixture_name):
            fixture_dirs = [dirname]
        else:
            fixture_dirs = self.fixture_dirs
            if os.path.sep in os.path.normpath(fixture_name):
                fixture_dirs = [os.path.join(dir_, dirname) for dir_ in fixture_dirs]
        return basename, fixture_dirs

    def handle(self, *args, **options) -> None:
        # * For Initial Users Loading
        try:
            fixture_name_and_dirs = self.get_fixture_name_and_dirs("user_fixture")
            file_name = fixture_name_and_dirs[0]
            dir = fixture_name_and_dirs[1][0]
            self.fix_timestamp(os.path.join(dir, file_name))
            call_command("loaddata", "user_fixture", verbosity=0)
        except Exception as error:
            raise CommandError(
                "loading user data failed with %s", error.args[-1]
            ) from error
        else:
            self.stdout.write("Loaded Users Successfully ✅")

        # * For Initial Groups Loading
        try:
            call_command("loaddata", "group_fixture", verbosity=0)
        except Exception as error:
            raise CommandError(
                "loading group data failed with %s", error.args[-1]
            ) from error
        else:
            self.stdout.write("Loaded Groups Successfully ✅")

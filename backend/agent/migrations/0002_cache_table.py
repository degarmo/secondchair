"""Create the table backing the database cache.

The interview throttle counts requests in the cache, so the table has to
exist everywhere the app runs - including the test database, which is built
from migrations alone.
"""

from django.core.management import call_command
from django.db import migrations


def create_cache_table(apps, schema_editor):
    call_command(
        "createcachetable",
        "django_cache_table",
        database=schema_editor.connection.alias,
        verbosity=0,
    )


def drop_cache_table(apps, schema_editor):
    schema_editor.execute("DROP TABLE IF EXISTS django_cache_table")


class Migration(migrations.Migration):
    dependencies = [("agent", "0001_initial")]

    operations = [migrations.RunPython(create_cache_table, drop_cache_table)]

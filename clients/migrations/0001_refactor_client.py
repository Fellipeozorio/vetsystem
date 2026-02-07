from django.db import migrations


class Migration(migrations.Migration):

    # keep this as a no-op migration that depends on the real generated migration
    dependencies = [
        ('clients', '0004_make_celular_required'),
    ]

    operations = []

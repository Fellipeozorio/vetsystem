# Generated manually on 2026-02-21

from django.db import migrations


def clear_como_conheceu(apps, schema_editor):
    """Limpa o campo como_conheceu para permitir a conversão para ForeignKey"""
    Client = apps.get_model('clients', 'Client')
    Client.objects.all().update(como_conheceu=None)


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0006_client_obs_celular_client_obs_email'),
    ]

    operations = [
        migrations.RunPython(clear_como_conheceu, migrations.RunPython.noop),
    ]

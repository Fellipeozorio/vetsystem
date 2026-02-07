from django.db import migrations, models


def set_celular_empty(apps, schema_editor):
    Client = apps.get_model('clients', 'Client')
    Client.objects.filter(celular__isnull=True).update(celular='')


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0003_marcacao_rename_whatsapp_client_cep_and_more'),
    ]

    operations = [
        migrations.RunPython(set_celular_empty, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='client',
            name='celular',
            field=models.CharField(max_length=30),
        ),
    ]

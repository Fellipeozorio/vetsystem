from django.db import migrations


def create_default_especies(apps, schema_editor):
    Especie = apps.get_model('cadastros', 'Especie')
    nomes = ['Ave', 'Canino', 'Felino', 'Primata', 'Roedor']
    for nome in nomes:
        Especie.objects.get_or_create(nome=nome, defaults={'ativo': True})


class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_especies),
    ]

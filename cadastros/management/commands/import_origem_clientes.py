from django.core.management.base import BaseCommand
from cadastros.models import OrigemCliente


class Command(BaseCommand):
    help = 'Importar origens de clientes padrões'

    def handle(self, *args, **options):
        names = [
            'Indicação', 'Google', 'Google Maps', 'Instagram', 'Facebook',
            'TikTok', 'WhatsApp', 'Site', 'Passando em frente', 'Evento', 'Outro'
        ]
        total = 0
        created = 0
        for n in names:
            obj, flag = OrigemCliente.objects.get_or_create(nome=n)
            total += 1
            if flag:
                created += 1

        self.stdout.write(f'Total nomes processados: {total}')
        self.stdout.write(f'Novas origens criadas: {created}')

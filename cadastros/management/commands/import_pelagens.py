import csv
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Import pelagens a partir de um CSV com coluna Nome'

    def add_arguments(self, parser):
        parser.add_argument('csvpath', nargs='?', type=str, help='Caminho para o arquivo CSV (padrão: Desktop/Cadastros/pelagens.csv)')

    def handle(self, *args, **options):
        csvpath = options.get('csvpath')
        if not csvpath:
            csvpath = str(Path.home() / 'Desktop' / 'Cadastros' / 'pelagens.csv')

        path = Path(csvpath)
        if not path.exists():
            self.stderr.write(f'Arquivo não encontrado: {path}')
            return

        from cadastros.models import Pelagem

        total = 0
        created = 0
        skipped = 0

        with path.open('r', encoding='utf-8-sig') as fh:
            reader = csv.reader(fh, delimiter=';')
            rows = list(reader)
            if not rows:
                self.stdout.write('CSV vazio')
                return

            # detect header
            start = 0
            if 'Nome' in rows[0][0]:
                start = 1

            for row in rows[start:]:
                if not row:
                    continue
                nome = row[0].strip()
                if not nome:
                    continue
                total += 1
                obj, created_flag = Pelagem.objects.get_or_create(nome=nome, defaults={'ativo': True})
                if created_flag:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(f'Total linhas processadas: {total}')
        self.stdout.write(f'Novas pelagens criadas: {created}')
        self.stdout.write(f'Já existentes/puladas: {skipped}')

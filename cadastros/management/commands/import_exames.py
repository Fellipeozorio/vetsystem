from pathlib import Path
import csv

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Importar exames a partir de um arquivo de texto/CSV com um nome por linha'

    def add_arguments(self, parser):
        parser.add_argument('csvpath', nargs='?', type=str, help='Caminho para o arquivo (padrão: Desktop/Cadastros/exames.csv)')

    def handle(self, *args, **options):
        csvpath = options.get('csvpath')
        if not csvpath:
            csvpath = str(Path.home() / 'Desktop' / 'Cadastros' / 'exames.csv')

        path = Path(csvpath)
        if not path.exists():
            self.stderr.write(f'Arquivo não encontrado: {path}')
            return

        from cadastros.models import Exame

        total = 0
        created = 0
        skipped = 0

        # arquivo parece ser uma lista simples; ler linha a linha com latin-1
        with path.open('r', encoding='latin-1') as fh:
            for raw in fh:
                nome = raw.strip()
                if not nome:
                    continue
                # pular header se presente
                if nome.lower() in ('exames', 'exame'):
                    continue

                total += 1
                obj, created_flag = Exame.objects.get_or_create(nome=nome)
                if created_flag:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(f'Total linhas processadas: {total}')
        self.stdout.write(f'Novos exames criados: {created}')
        self.stdout.write(f'Já existentes/puladas: {skipped}')

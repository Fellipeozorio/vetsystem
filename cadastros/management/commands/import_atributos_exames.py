import csv
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Importar atributos de exames a partir de CSV com colunas Nome;Ordem;Exame;Status;Caminho'

    def add_arguments(self, parser):
        parser.add_argument('csvpath', nargs='?', type=str, help='Caminho para o arquivo (padrão: Desktop/Cadastros/Atributos de exames.csv)')

    def _parse_bool(self, value):
        if not value:
            return True
        v = value.strip().lower()
        return v in ('sim', 'ativo', 'true', '1', 'yes', 'y')

    def handle(self, *args, **options):
        csvpath = options.get('csvpath')
        if not csvpath:
            csvpath = str(Path.home() / 'Desktop' / 'Cadastros' / 'Atributos de exames.csv')

        path = Path(csvpath)
        if not path.exists():
            self.stderr.write(f'Arquivo não encontrado: {path}')
            return

        from cadastros.models import Exame, AtributoExame

        total = 0
        created = 0
        updated = 0
        skipped = 0

        with path.open('r', encoding='latin-1') as fh:
            reader = csv.DictReader(fh, delimiter=';')
            for row in reader:
                if not row:
                    continue

                nome = (row.get('Nome') or '').strip()
                exame_nome = (row.get('Exame') or '').strip()
                ordem = (row.get('Ordem') or '').strip()
                status = (row.get('Status') or '').strip()

                if not nome:
                    continue

                ativo = self._parse_bool(status)

                # ensure exame exists
                exame_obj, _ = Exame.objects.get_or_create(nome=exame_nome or 'Outros')

                total += 1
                obj, created_flag = AtributoExame.objects.get_or_create(exame=exame_obj, nome=nome, defaults={})
                if created_flag:
                    created += 1
                else:
                    # no other fields to update currently
                    skipped += 1

        self.stdout.write(f'Total linhas processadas: {total}')
        self.stdout.write(f'Novos atributos criados: {created}')
        self.stdout.write(f'Já existentes/puladas: {skipped}')

import csv
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Importar vacinas a partir de CSV com colunas Nome;Grupo;Status'

    def add_arguments(self, parser):
        parser.add_argument('csvpath', nargs='?', type=str, help='Caminho para o arquivo CSV (padrão: Desktop/Cadastros/Vacinas.csv)')

    def _parse_bool(self, value):
        if not value:
            return False
        v = value.strip().lower()
        return v in ('sim', 'ativo', 'true', '1', 'yes', 'y')

    def handle(self, *args, **options):
        csvpath = options.get('csvpath')
        if not csvpath:
            csvpath = str(Path.home() / 'Desktop' / 'Cadastros' / 'Vacinas.csv')

        path = Path(csvpath)
        if not path.exists():
            self.stderr.write(f'Arquivo não encontrado: {path}')
            return

        from cadastros.models import Vacina

        total = 0
        created = 0
        updated = 0
        skipped = 0

        # read with latin-1 to handle legacy encodings in exported CSVs
        with path.open('r', encoding='latin-1') as fh:
            reader = csv.DictReader(fh, delimiter=';')
            for row in reader:
                if not row:
                    continue

                nome = (row.get('Nome') or row.get('nome') or '').strip()
                grupo = (row.get('Grupo') or row.get('grupo') or '').strip()
                status = (row.get('Status') or row.get('status') or '').strip()

                if not nome:
                    continue

                ativo = self._parse_bool(status)

                total += 1
                obj, created_flag = Vacina.objects.get_or_create(nome=nome, defaults={'grupo': grupo or None, 'ativo': ativo})
                if created_flag:
                    created += 1
                else:
                    changed = False
                    if grupo and obj.grupo != grupo:
                        obj.grupo = grupo
                        changed = True
                    if obj.ativo != ativo:
                        obj.ativo = ativo
                        changed = True
                    if changed:
                        obj.save()
                        updated += 1
                    else:
                        skipped += 1

        self.stdout.write(f'Total linhas processadas: {total}')
        self.stdout.write(f'Novas vacinas criadas: {created}')
        self.stdout.write(f'Vacinas atualizadas: {updated}')
        self.stdout.write(f'Já existentes/puladas: {skipped}')

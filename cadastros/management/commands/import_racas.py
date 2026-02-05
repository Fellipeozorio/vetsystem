import csv
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Import raças a partir de um CSV com colunas Nome;Espécie'

    def add_arguments(self, parser):
        parser.add_argument('csvpath', nargs='?', type=str, help='Caminho para o arquivo CSV (padrão: Desktop/Cadastros/racas.csv)')

    def handle(self, *args, **options):
        csvpath = options.get('csvpath')
        if not csvpath:
            csvpath = str(Path.home() / 'Desktop' / 'Cadastros' / 'racas.csv')

        path = Path(csvpath)
        if not path.exists():
            self.stderr.write(f'Arquivo não encontrado: {path}')
            return

        from cadastros.models import Especie, Raca

        created_especies = {}
        total = 0
        created = 0
        skipped = 0

        with path.open('r', encoding='utf-8-sig') as fh:
            reader = csv.reader(fh, delimiter=';')
            # skip header if present
            rows = list(reader)
            if not rows:
                self.stdout.write('CSV vazio')
                return

            # if header contains 'Nome' assume first row is header
            start = 0
            if 'Nome' in rows[0][0] or 'Esp' in rows[0][1]:
                start = 1

            for row in rows[start:]:
                if not row or len(row) < 2:
                    continue
                nome = row[0].strip()
                especie_name = row[1].strip()
                if not nome:
                    continue
                total += 1

                # find or create especie (case-insensitive)
                especie = Especie.objects.filter(nome__iexact=especie_name).first()
                if not especie:
                    if especie_name in created_especies:
                        especie = created_especies[especie_name]
                    else:
                        especie, _ = Especie.objects.get_or_create(nome=especie_name, defaults={'ativo': True})
                        created_especies[especie_name] = especie

                # create raca if not exists for that name (unique on nome)
                raca_obj, rcreated = Raca.objects.get_or_create(nome=nome, defaults={'ativo': True, 'especie': especie})
                if not rcreated:
                    # if exists but has no especie set, update it
                    if raca_obj.especie_id is None and especie is not None:
                        raca_obj.especie = especie
                        raca_obj.save()
                        created += 1
                    else:
                        skipped += 1
                else:
                    # ensure especie linked
                    if raca_obj.especie_id != especie.id:
                        raca_obj.especie = especie
                        raca_obj.save()
                    created += 1

        self.stdout.write(f'Total linhas processadas: {total}')
        self.stdout.write(f'Novas raças criadas: {created}')
        self.stdout.write(f'Já existentes/puladas: {skipped}')

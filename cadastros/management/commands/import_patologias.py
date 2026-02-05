import csv
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Import patologias a partir de um CSV com colunas Patologia;Descrição;Status'

    def add_arguments(self, parser):
        parser.add_argument('csvpath', nargs='?', type=str, help='Caminho para o arquivo CSV (padrão: Desktop/Cadastros/patologias.csv)')

    def handle(self, *args, **options):
        csvpath = options.get('csvpath')
        if not csvpath:
            csvpath = str(Path.home() / 'Desktop' / 'Cadastros' / 'patologias.csv')

        path = Path(csvpath)
        if not path.exists():
            self.stderr.write(f'Arquivo não encontrado: {path}')
            return

        from cadastros.models import Patologia

        total = 0
        created = 0
        updated = 0
        skipped = 0

        with path.open('r', encoding='utf-8-sig') as fh:
            reader = csv.DictReader(fh, delimiter=';')
            for row in reader:
                # handle possible empty rows
                if not row:
                    continue

                nome = (row.get('Patologia') or row.get('patologia') or '').strip()
                descricao = (row.get('Descrição') or row.get('Descricao') or row.get('descricao') or '').strip()
                status = (row.get('Status') or row.get('status') or '').strip()

                if not nome:
                    continue

                ativo = True if status.lower() == 'ativo' else False
                total += 1

                obj, created_flag = Patologia.objects.get_or_create(nome=nome, defaults={'descricao': descricao, 'ativo': ativo})
                if created_flag:
                    created += 1
                else:
                    # update fields if different
                    changed = False
                    if descricao and obj.descricao != descricao:
                        obj.descricao = descricao
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
        self.stdout.write(f'Novas patologias criadas: {created}')
        self.stdout.write(f'Patologias atualizadas: {updated}')
        self.stdout.write(f'Já existentes/puladas: {skipped}')

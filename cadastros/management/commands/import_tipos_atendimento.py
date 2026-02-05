import csv
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Importar tipos de atendimento a partir de CSV (sem alteraçao de modelos)'

    def add_arguments(self, parser):
        parser.add_argument('csvpath', nargs='?', type=str, help='Caminho para o arquivo CSV (padrão: Desktop/Cadastros/Tipo de atendimento.csv)')

    def _parse_bool(self, value):
        if not value:
            return False
        v = value.strip().lower()
        return v in ('sim', 'ativo', 'true', '1', 'yes', 'y')

    def _safe_int(self, value, default):
        try:
            return int(value)
        except Exception:
            return default

    def handle(self, *args, **options):
        csvpath = options.get('csvpath')
        if not csvpath:
            csvpath = str(Path.home() / 'Desktop' / 'Cadastros' / 'Tipo de atendimento.csv')

        path = Path(csvpath)
        if not path.exists():
            self.stderr.write(f'Arquivo não encontrado: {path}')
            return

        from cadastros.models import TipoAtendimento

        total = 0
        created = 0
        updated = 0
        skipped = 0

        # open with latin-1 to safely read files saved with legacy encodings
        fh = path.open('r', encoding='latin-1')
        reader = csv.DictReader(fh, delimiter=';')

        for row in reader:
                if not row:
                    continue

                # try common header names, otherwise fallback by position
                nome = (row.get('Tipo de atendimento') or row.get('Tipo de Atendimento') or row.get('Tipo') or '')
                if not nome:
                    # fallback to first column value
                    first = next(iter(row.values()), '')
                    nome = first
                nome = (nome or '').strip()
                if not nome:
                    continue

                # duration may have corrupted header; try several keys then second column
                duration_keys = ['Duração', 'Duracao', 'DuraÃ§Ã£o', 'Dura��o', 'DuraÃ§ao', 'DuraÃ§Ã£o']
                dur_val = None
                for k in duration_keys:
                    if row.get(k):
                        dur_val = row.get(k)
                        break
                if dur_val is None:
                    vals = list(row.values())
                    dur_val = vals[1] if len(vals) > 1 else ''

                duracao = self._safe_int((dur_val or '').strip(), 30)

                status = (row.get('Status') or row.get('status') or '')
                ativo = self._parse_bool(status)

                total += 1
                obj, created_flag = TipoAtendimento.objects.get_or_create(nome=nome, defaults={'duracao_padrao': duracao, 'ativo': ativo})
                if created_flag:
                    created += 1
                else:
                    changed = False
                    if obj.duracao_padrao != duracao:
                        obj.duracao_padrao = duracao
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
        self.stdout.write(f'Novos tipos criados: {created}')
        self.stdout.write(f'Tipos atualizados: {updated}')
        self.stdout.write(f'Já existentes/puladas: {skipped}')

import csv
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from cadastros.models import (
    Especie, Raca, Pelagem, Patologia,
    TipoAtendimento, Vacina, Exame
)


class Command(BaseCommand):
    help = 'Importa dados dos arquivos CSV para os cadastros'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_dir',
            type=str,
            help='Diretório contendo os arquivos CSV'
        )

    def handle(self, *args, **options):
        csv_dir = options['csv_dir']
        
        if not os.path.exists(csv_dir):
            self.stdout.write(self.style.ERROR(f'Diretório não encontrado: {csv_dir}'))
            return
        
        self.stdout.write(self.style.SUCCESS('Iniciando importação...'))
        
        # Importar na ordem correta (espécies antes de raças)
        self.import_especies(csv_dir)
        self.import_racas(csv_dir)
        self.import_pelagens(csv_dir)
        self.import_exames(csv_dir)
        self.import_patologias(csv_dir)
        self.import_tipos_atendimento(csv_dir)
        self.import_vacinas(csv_dir)
        
        self.stdout.write(self.style.SUCCESS('Importação concluída!'))

    def import_especies(self, csv_dir):
        """Extrai espécies únicas do arquivo de raças"""
        racas_file = os.path.join(csv_dir, 'racas.csv')
        if not os.path.exists(racas_file):
            self.stdout.write(self.style.WARNING('Arquivo racas.csv não encontrado'))
            return
        
        especies_set = set()
        
        # Tentar múltiplos encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(racas_file, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                        if 'Espécie' in row or 'Especie' in row:
                            especie = row.get('Espécie') or row.get('Especie')
                            if especie:
                                especies_set.add(especie.strip())
                break
            except UnicodeDecodeError:
                continue
        
        count = 0
        for especie_nome in especies_set:
            _, created = Especie.objects.get_or_create(
                nome=especie_nome,
                defaults={'ativo': True}
            )
            if created:
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ {count} espécies importadas'))

    def import_racas(self, csv_dir):
        """Importa raças do arquivo racas.csv"""
        racas_file = os.path.join(csv_dir, 'racas.csv')
        if not os.path.exists(racas_file):
            self.stdout.write(self.style.WARNING('Arquivo racas.csv não encontrado'))
            return
        
        count = 0
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(racas_file, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                        nome = row.get('Nome', '').strip()
                        especie_nome = (row.get('Espécie') or row.get('Especie', '')).strip()
                        
                        if nome and especie_nome:
                            try:
                                especie = Especie.objects.get(nome=especie_nome)
                                _, created = Raca.objects.get_or_create(
                                    nome=nome,
                                    defaults={'especie': especie, 'ativo': True}
                                )
                                if created:
                                    count += 1
                            except Especie.DoesNotExist:
                                self.stdout.write(self.style.WARNING(f'Espécie não encontrada: {especie_nome}'))
                break
            except UnicodeDecodeError:
                continue
        
        self.stdout.write(self.style.SUCCESS(f'✓ {count} raças importadas'))

    def import_pelagens(self, csv_dir):
        """Importa pelagens do arquivo pelagens.csv"""
        pelagens_file = os.path.join(csv_dir, 'pelagens.csv')
        if not os.path.exists(pelagens_file):
            self.stdout.write(self.style.WARNING('Arquivo pelagens.csv não encontrado'))
            return
        
        count = 0
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(pelagens_file, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                        nome = row.get('Nome', '').strip()
                        if nome:
                            _, created = Pelagem.objects.get_or_create(
                                nome=nome,
                                defaults={'ativo': True}
                            )
                            if created:
                                count += 1
                break
            except UnicodeDecodeError:
                continue
        
        self.stdout.write(self.style.SUCCESS(f'✓ {count} pelagens importadas'))

    def import_exames(self, csv_dir):
        """Importa exames do arquivo exames.csv"""
        exames_file = os.path.join(csv_dir, 'exames.csv')
        if not os.path.exists(exames_file):
            self.stdout.write(self.style.WARNING('Arquivo exames.csv não encontrado'))
            return
        
        count = 0
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(exames_file, 'r', encoding=encoding) as f:
                    # Arquivo tem apenas uma coluna sem header
                    for line in f:
                        nome = line.strip()
                        if nome and nome != 'Exames':  # Pular header
                            _, created = Exame.objects.get_or_create(
                                nome=nome,
                                defaults={'ativo': True}
                            )
                            if created:
                                count += 1
                break
            except UnicodeDecodeError:
                continue
        
        self.stdout.write(self.style.SUCCESS(f'✓ {count} exames importados'))

    def import_patologias(self, csv_dir):
        """Importa patologias do arquivo patologias.csv"""
        patologias_file = os.path.join(csv_dir, 'patologias.csv')
        if not os.path.exists(patologias_file):
            self.stdout.write(self.style.WARNING('Arquivo patologias.csv não encontrado'))
            return
        
        count = 0
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(patologias_file, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                        nome = row.get('Patologia', '').strip()
                        descricao = row.get('Descrição', '').strip()
                        status = row.get('Status', 'Ativo').strip()
                        
                        if nome:
                            _, created = Patologia.objects.get_or_create(
                                nome=nome,
                                defaults={
                                    'descricao': descricao,
                                    'ativo': status.lower() == 'ativo'
                                }
                            )
                            if created:
                                count += 1
                break
            except UnicodeDecodeError:
                continue
        
        self.stdout.write(self.style.SUCCESS(f'✓ {count} patologias importadas'))

    def import_tipos_atendimento(self, csv_dir):
        """Importa tipos de atendimento"""
        tipos_file = os.path.join(csv_dir, 'Tipo de atendimento.csv')
        if not os.path.exists(tipos_file):
            self.stdout.write(self.style.WARNING('Arquivo Tipo de atendimento.csv não encontrado'))
            return
        
        count = 0
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(tipos_file, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                        nome = row.get('Tipo de atendimento', '').strip()
                        duracao = row.get('Duração', '1').strip()
                        status = row.get('Status', 'Ativo').strip()
                        
                        if nome:
                            # Converter duração para número
                            try:
                                duracao_num = int(duracao) if duracao.isdigit() else 30
                            except:
                                duracao_num = 30
                            
                            _, created = TipoAtendimento.objects.get_or_create(
                                nome=nome,
                                defaults={
                                    'duracao_padrao': duracao_num,
                                    'ativo': status.lower() == 'ativo'
                                }
                            )
                            if created:
                                count += 1
                break
            except UnicodeDecodeError:
                continue
        
        self.stdout.write(self.style.SUCCESS(f'✓ {count} tipos de atendimento importados'))

    def import_vacinas(self, csv_dir):
        """Importa vacinas do arquivo Vacinas.csv"""
        vacinas_file = os.path.join(csv_dir, 'Vacinas.csv')
        if not os.path.exists(vacinas_file):
            self.stdout.write(self.style.WARNING('Arquivo Vacinas.csv não encontrado'))
            return
        
        count = 0
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(vacinas_file, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                        nome = row.get('Nome', '').strip()
                        grupo = row.get('Grupo', '').strip()
                        status = row.get('Status', 'Ativo').strip()
                        
                        if nome:
                            _, created = Vacina.objects.get_or_create(
                                nome=nome,
                                defaults={
                                    'grupo': grupo,
                                    'ativo': status.lower() == 'ativo'
                                }
                            )
                            if created:
                                count += 1
                break
            except UnicodeDecodeError:
                continue
        
        self.stdout.write(self.style.SUCCESS(f'✓ {count} vacinas importadas'))

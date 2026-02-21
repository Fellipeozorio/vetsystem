from django.db import models


class BaseCadastro(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Especie(BaseCadastro):
    pass


class Raca(BaseCadastro):
    especie = models.ForeignKey(
        Especie,
        on_delete=models.CASCADE,
        related_name='racas',
        verbose_name='Espécie'
    )


class Pelagem(BaseCadastro):
    pass


class FilaAtendimento(BaseCadastro):
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')


class Patologia(BaseCadastro):
    codigo = models.CharField(max_length=50, blank=True, null=True, verbose_name='Código')
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')


class TipoAtendimento(BaseCadastro):
    FLUXO_CLINICO = 'clinico'
    FLUXO_BANHO_TOSA = 'banho_tosa'
    FLUXO_SIMPLIFICADO = 'simplificado'
    
    FLUXO_CHOICES = [
        (FLUXO_CLINICO, 'Atendimento Clínico'),
        (FLUXO_BANHO_TOSA, 'Atendimento Banho e Tosa'),
        (FLUXO_SIMPLIFICADO, 'Fluxo Simplificado'),
    ]
    
    FREQUENCIA_NAO_RECORRENTE = 'nao_recorrente'
    FREQUENCIA_SEMANAL = 'semanal'
    FREQUENCIA_QUINZENAL = 'quinzenal'
    FREQUENCIA_MENSAL = 'mensal'
    FREQUENCIA_TRIMESTRAL = 'trimestral'
    FREQUENCIA_SEMESTRAL = 'semestral'
    FREQUENCIA_ANUAL = 'anual'
    
    FREQUENCIA_CHOICES = [
        (FREQUENCIA_NAO_RECORRENTE, 'Não é recorrente'),
        (FREQUENCIA_SEMANAL, 'Semanal'),
        (FREQUENCIA_QUINZENAL, 'Quinzenal'),
        (FREQUENCIA_MENSAL, 'Mensal'),
        (FREQUENCIA_TRIMESTRAL, 'Trimestral'),
        (FREQUENCIA_SEMESTRAL, 'Semestral'),
        (FREQUENCIA_ANUAL, 'Anual'),
    ]
    
    codigo = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Código'
    )
    duracao_padrao = models.PositiveIntegerField(
        help_text="Duração em minutos",
        default=30,
        verbose_name='Duração Padrão (min)'
    )
    fluxo_agenda = models.CharField(
        max_length=20,
        choices=FLUXO_CHOICES,
        default=FLUXO_CLINICO,
        verbose_name='Fluxo da Agenda'
    )
    mensagens_automaticas = models.BooleanField(
        default=False,
        verbose_name='Envio de Mensagens Automáticas'
    )
    frequencia_recomendada = models.CharField(
        max_length=20,
        choices=FREQUENCIA_CHOICES,
        default=FREQUENCIA_NAO_RECORRENTE,
        verbose_name='Frequência Recomendada'
    )
    modelo_atendimento = models.TextField(
        blank=True,
        null=True,
        verbose_name='Modelo de Atendimento'
    )
    
    def save(self, *args, **kwargs):
        # Gerar código sequencial se não existir
        if not self.codigo:
            # Buscar o maior código numérico existente
            # Excluir o próprio registro se já tiver ID (edição)
            query = TipoAtendimento.objects.exclude(codigo__isnull=True).exclude(codigo='')
            if self.pk:
                query = query.exclude(pk=self.pk)
            
            existing_codes = query.values_list('codigo', flat=True)
            numeric_codes = []
            for code in existing_codes:
                try:
                    numeric_codes.append(int(code))
                except (ValueError, TypeError):
                    pass
            
            if numeric_codes:
                next_num = max(numeric_codes) + 1
            else:
                next_num = 1
            
            self.codigo = str(next_num).zfill(3)
        super().save(*args, **kwargs)
    
    def get_duracao_display_horas(self):
        """Retorna a duração no formato HH:MM"""
        horas = self.duracao_padrao // 60
        minutos = self.duracao_padrao % 60
        return f"{horas:02d}:{minutos:02d}"
    
    def get_duracao_display_extenso(self):
        """Retorna a duração por extenso (ex: 1 hora e 45 minutos)"""
        horas = self.duracao_padrao // 60
        minutos = self.duracao_padrao % 60
        
        partes = []
        if horas > 0:
            if horas == 1:
                partes.append('1 hora')
            else:
                partes.append(f'{horas} horas')
        
        if minutos > 0:
            if minutos == 1:
                partes.append('1 minuto')
            else:
                partes.append(f'{minutos} minutos')
        
        if not partes:
            return '0 minutos'
        
        return ' e '.join(partes)
    
    def get_area_display(self):
        """Retorna o nome legível da área baseado no fluxo"""
        if self.fluxo_agenda == self.FLUXO_CLINICO:
            return 'Clínica'
        elif self.fluxo_agenda == self.FLUXO_BANHO_TOSA:
            return 'Banho e Tosa'
        else:
            return 'Simplificado'


class Vacina(BaseCadastro):
    TIPO_ANTIPARASITARIO = 'antiparasitario'
    TIPO_VACINAS = 'vacinas'
    TIPO_VERMIFUGOS = 'vermifugos'
    
    TIPO_CHOICES = [
        (TIPO_ANTIPARASITARIO, 'Antiparasitário'),
        (TIPO_VACINAS, 'Vacinas'),
        (TIPO_VERMIFUGOS, 'Vermífugos'),
    ]
    
    codigo = models.CharField(max_length=10, unique=True, editable=False, default='000', verbose_name='Código')
    tipo = models.CharField(
        max_length=50, 
        choices=TIPO_CHOICES,
        default=TIPO_VACINAS,
        verbose_name='Tipo'
    )
    laboratorios = models.TextField(blank=True, null=True, verbose_name='Laboratórios')
    
    def save(self, *args, **kwargs):
        # Gerar código sequencial se não existir ou for o padrão
        if not self.codigo or self.codigo == '000':
            last_vacina = Vacina.objects.order_by('-id').first()
            if last_vacina and last_vacina.codigo and last_vacina.codigo != '000':
                try:
                    last_number = int(last_vacina.codigo)
                    self.codigo = str(last_number + 1).zfill(3)
                except ValueError:
                    self.codigo = '001'
            else:
                self.codigo = '001'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nome} ({self.codigo})"


class ProtocoloVacina(models.Model):
    APLICACAO_INDETERMINADO = 'indeterminado'
    APLICACAO_1_DOSE = '1'
    APLICACAO_2_DOSES = '2'
    APLICACAO_3_DOSES = '3'
    APLICACAO_4_DOSES = '4'
    APLICACAO_5_DOSES = '5'
    APLICACAO_6_DOSES = '6'
    APLICACAO_7_DOSES = '7'
    APLICACAO_8_DOSES = '8'
    APLICACAO_9_DOSES = '9'
    APLICACAO_10_DOSES = '10'
    
    APLICACAO_CHOICES = [
        (APLICACAO_INDETERMINADO, 'Tempo Indeterminado'),
        (APLICACAO_1_DOSE, 'Apenas 1 dose'),
        (APLICACAO_2_DOSES, 'Apenas 2 doses'),
        (APLICACAO_3_DOSES, 'Apenas 3 doses'),
        (APLICACAO_4_DOSES, 'Apenas 4 doses'),
        (APLICACAO_5_DOSES, 'Apenas 5 doses'),
        (APLICACAO_6_DOSES, 'Apenas 6 doses'),
        (APLICACAO_7_DOSES, 'Apenas 7 doses'),
        (APLICACAO_8_DOSES, 'Apenas 8 doses'),
        (APLICACAO_9_DOSES, 'Apenas 9 doses'),
        (APLICACAO_10_DOSES, 'Apenas 10 doses'),
    ]
    
    vacina = models.ForeignKey(
        Vacina,
        on_delete=models.CASCADE,
        related_name='protocolos',
        verbose_name='Vacina'
    )
    nome = models.CharField(max_length=150, verbose_name='Nome')
    especie = models.ForeignKey(
        Especie,
        on_delete=models.CASCADE,
        related_name='protocolos_vacina',
        verbose_name='Espécie'
    )
    aplicacao = models.CharField(
        max_length=20,
        choices=APLICACAO_CHOICES,
        verbose_name='Aplicação'
    )
    intervalo_dias = models.IntegerField(verbose_name='Intervalo (dias)')
    vem_apos = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='protocolos_posteriores',
        verbose_name='Vem após'
    )
    
    class Meta:
        ordering = ['nome']
        verbose_name = 'Protocolo de Vacina'
        verbose_name_plural = 'Protocolos de Vacinas'
    
    def __str__(self):
        return f"{self.vacina.nome} - {self.nome}"


class Exame(BaseCadastro):
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')


class AtributoExame(models.Model):
    exame = models.ForeignKey(
        Exame,
        on_delete=models.CASCADE,
        related_name='atributos'
    )

    nome = models.CharField(max_length=150)
    unidade = models.CharField(max_length=50, blank=True, null=True)
    valor_referencia = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.exame.nome} - {self.nome}"


class ReferenciaExame(models.Model):
    exame = models.ForeignKey(
        Exame,
        on_delete=models.CASCADE,
        related_name='referencias'
    )

    descricao = models.TextField()

    def __str__(self):
        return f"Referência - {self.exame.nome}"


class ModeloReceita(models.Model):
    nome = models.CharField(max_length=150)
    conteudo = models.TextField()

    def __str__(self):
        return self.nome


class ModeloDocumento(models.Model):
    nome = models.CharField(max_length=150)
    conteudo = models.TextField()

    def __str__(self):
        return self.nome


class OrigemCliente(BaseCadastro):
    pass

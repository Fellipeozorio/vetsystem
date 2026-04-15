from django.db import models, transaction
from django.contrib.auth.models import User


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
    codigo = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        blank=True,
        verbose_name='Código'
    )
    permanente = models.BooleanField(
        default=False,
        verbose_name='Permanente',
        help_text='Se marcado, esta fila aparecerá todos os dias na agenda'
    )
    atribuido_a = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='filas_atendimento',
        verbose_name='Atribuído a',
        help_text='Veterinário responsável por atender esta fila'
    )
    
    def __str__(self):
        return f"{self.nome} ({self.codigo})"


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
    codigo = models.CharField(max_length=10, unique=True, editable=False, default='000', verbose_name='Código')
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    
    # Bloco 1: Cabeçalho (4 modelos)
    modelo_cabecalho = models.IntegerField(
        default=1,
        choices=[(1, 'Logo + Básico'), (2, 'Logo + Completo'), (3, 'Apenas Logo'), (4, 'Sem Cabeçalho')],
        verbose_name='Modelo do Cabeçalho'
    )
    
    # Bloco 3: Informações do Paciente (3 modelos)
    modelo_info_paciente = models.IntegerField(
        default=1,
        choices=[(1, 'Animal + Responsável Resumido'), (2, 'Animal + Responsável Completo'), (3, 'Sem Informações')],
        verbose_name='Modelo de Info do Paciente'
    )
    
    # Bloco 4: Apresentação (editor rico)
    conteudo_apresentacao = models.TextField(
        blank=True,
        verbose_name='Apresentação',
        help_text='Conteúdo da seção de apresentação'
    )
    
    # Bloco 6: Encerramento (editor rico)
    conteudo_encerramento = models.TextField(
        blank=True,
        verbose_name='Encerramento',
        help_text='Conteúdo da seção de encerramento'
    )
    
    # Bloco 7: Rodapé (2 modelos)
    modelo_rodape = models.IntegerField(
        default=1,
        choices=[(1, 'Completo'), (2, 'Sem Rodapé')],
        verbose_name='Modelo do Rodapé'
    )
    
    def save(self, *args, **kwargs):
        # Gerar código sequencial se não existir ou for o padrão
        if not self.codigo or self.codigo == '000':
            last_exame = Exame.objects.order_by('-id').first()
            if last_exame and last_exame.codigo and last_exame.codigo != '000':
                try:
                    last_number = int(last_exame.codigo)
                    self.codigo = str(last_number + 1).zfill(3)
                except ValueError:
                    self.codigo = '001'
            else:
                self.codigo = '001'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nome} ({self.codigo})"


class AtributoExame(models.Model):
    TIPO_DADO_CHOICES = [
        ('alfanumerico', 'Alfanumérico'),
        ('data', 'Data'),
        ('decimal', 'Decimal'),
        ('texto', 'Texto'),
        ('inteiro', 'Inteiro'),
    ]

    exame = models.ForeignKey(
        Exame,
        on_delete=models.CASCADE,
        related_name='atributos'
    )
    atributo_pai = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='filhos',
        verbose_name='Atributo pai'
    )

    nome = models.CharField(max_length=150)
    ordem = models.PositiveIntegerField(default=1, verbose_name='Ordem')
    tipo_dado = models.CharField(
        max_length=20,
        choices=TIPO_DADO_CHOICES,
        blank=True,
        null=True,
        verbose_name='Tipo do dado'
    )
    tamanho = models.CharField(max_length=20, blank=True, null=True, verbose_name='Tamanho')
    unidade = models.CharField(max_length=50, blank=True, null=True, verbose_name='Unidade')
    largura = models.PositiveIntegerField(blank=True, null=True, verbose_name='Largura (px)')
    obrigatorio = models.BooleanField(default=False, verbose_name='Obrigatório')
    opcoes_preenchimento = models.TextField(blank=True, null=True, verbose_name='Opções de preenchimento')
    ativo = models.BooleanField(default=True)
    valor_referencia = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['exame', 'ordem', 'nome']

    def __str__(self):
        return f"{self.exame.nome} - {self.nome}"

    @property
    def indent_style(self):
        depth = 0
        parent = self.atributo_pai
        while parent is not None:
            depth += 1
            parent = parent.atributo_pai
        return f"padding-left:{depth * 1.5}rem;" if depth > 0 else ""


class ReferenciaExame(models.Model):
    exame = models.ForeignKey(
        Exame,
        on_delete=models.CASCADE,
        related_name='referencias'
    )

    descricao = models.TextField()

    def __str__(self):
        return f"Referência - {self.exame.nome}"


class ModeloReceita(BaseCadastro):
    codigo = models.CharField(max_length=10, unique=True, editable=False, default='000', verbose_name='Código')
    autor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Autor'
    )
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    
    # Bloco 1: Cabeçalho (4 modelos)
    modelo_cabecalho = models.IntegerField(
        default=1,
        choices=[(1, 'Logo + Básico'), (2, 'Logo + Completo'), (3, 'Apenas Logo'), (4, 'Sem Cabeçalho')],
        verbose_name='Modelo do Cabeçalho'
    )
    
    # Bloco 3: Informações do Paciente (3 modelos)
    modelo_info_paciente = models.IntegerField(
        default=1,
        choices=[(1, 'Animal + Responsável Resumido'), (2, 'Animal + Responsável Completo'), (3, 'Sem Informações')],
        verbose_name='Modelo de Info do Paciente'
    )
    
    # Bloco 4: Apresentação (editor rico)
    conteudo_apresentacao = models.TextField(
        blank=True,
        verbose_name='Apresentação',
        help_text='Conteúdo da seção de apresentação'
    )
    
    # Bloco 6: Encerramento (editor rico)
    conteudo_encerramento = models.TextField(
        blank=True,
        verbose_name='Encerramento',
        help_text='Conteúdo da seção de encerramento'
    )
    
    # Bloco 7: Rodapé (2 modelos)
    modelo_rodape = models.IntegerField(
        default=1,
        choices=[(1, 'Completo'), (2, 'Sem Rodapé')],
        verbose_name='Modelo do Rodapé'
    )
    
    def save(self, *args, **kwargs):
        # Gerar código sequencial se não existir ou for o padrão
        if not self.codigo or self.codigo == '000':
            last_receita = ModeloReceita.objects.order_by('-id').first()
            if last_receita and last_receita.codigo and last_receita.codigo != '000':
                try:
                    last_number = int(last_receita.codigo)
                    self.codigo = str(last_number + 1).zfill(3)
                except ValueError:
                    self.codigo = '001'
            else:
                self.codigo = '001'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nome} ({self.codigo})"


class ModeloDocumento(BaseCadastro):
    codigo = models.CharField(max_length=10, unique=True, editable=False, default='000', verbose_name='Código')
    autor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Autor'
    )
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    
    # Bloco 1: Cabeçalho (4 modelos)
    modelo_cabecalho = models.IntegerField(
        default=1,
        choices=[(1, 'Logo + Básico'), (2, 'Logo + Completo'), (3, 'Apenas Logo'), (4, 'Sem Cabeçalho')],
        verbose_name='Modelo do Cabeçalho'
    )
    
    # Bloco 3: Informações do Paciente (3 modelos)
    modelo_info_paciente = models.IntegerField(
        default=1,
        choices=[(1, 'Animal + Responsável Resumido'), (2, 'Animal + Responsável Completo'), (3, 'Sem Informações')],
        verbose_name='Modelo de Info do Paciente'
    )
    
    # Bloco 4: Apresentação (editor rico)
    conteudo_apresentacao = models.TextField(
        blank=True,
        verbose_name='Apresentação',
        help_text='Conteúdo da seção de apresentação'
    )
    
    # Bloco 6: Encerramento (editor rico)
    conteudo_encerramento = models.TextField(
        blank=True,
        verbose_name='Encerramento',
        help_text='Conteúdo da seção de encerramento'
    )
    
    # Bloco 7: Rodapé (2 modelos)
    modelo_rodape = models.IntegerField(
        default=1,
        choices=[(1, 'Completo'), (2, 'Sem Rodapé')],
        verbose_name='Modelo do Rodapé'
    )
    
    def save(self, *args, **kwargs):
        # Gerar código sequencial se não existir ou for o padrão
        if not self.codigo or self.codigo == '000':
            last_documento = ModeloDocumento.objects.order_by('-id').first()
            if last_documento and last_documento.codigo and last_documento.codigo != '000':
                try:
                    last_number = int(last_documento.codigo)
                    self.codigo = str(last_number + 1).zfill(3)
                except ValueError:
                    self.codigo = '001'
            else:
                self.codigo = '001'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nome} ({self.codigo})"


class OrigemCliente(BaseCadastro):
    pass


class DadosUnidade(models.Model):
    """
    Modelo para armazenar informações da unidade/clínica.
    Singleton: deve existir apenas um registro.
    """
    nome_empreendimento = models.CharField(
        max_length=200,
        verbose_name='Nome do Empreendimento'
    )
    cnpj = models.CharField(
        max_length=18,
        unique=True,
        verbose_name='CNPJ',
        help_text='Formato: 00.000.000/0000-00'
    )
    inscricao_estadual = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Inscrição Estadual'
    )
    registro_crmv = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Registro CRMV',
        help_text='Registro no Conselho Regional de Medicina Veterinária'
    )
    
    # Endereço
    endereco = models.CharField(max_length=200, verbose_name='Endereço')
    numero = models.CharField(max_length=20, verbose_name='Número')
    bairro = models.CharField(max_length=100, verbose_name='Bairro')
    cidade = models.CharField(max_length=100, verbose_name='Cidade')
    estado = models.CharField(
        max_length=2,
        verbose_name='Estado',
        help_text='UF - Ex: SP, RJ, MG'
    )
    cep = models.CharField(
        max_length=9,
        verbose_name='CEP',
        help_text='Formato: 00000-000'
    )
    
    # Contatos
    telefone_comercial = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Telefone Comercial',
        help_text='Formato: (00) 0000-0000'
    )
    celular = models.CharField(
        max_length=20,
        verbose_name='Celular',
        help_text='Formato: (00) 00000-0000'
    )
    email = models.EmailField(verbose_name='E-mail')
    
    # Contatos Adicionais (armazenado como JSON)
    contatos_adicionais = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Contatos Adicionais',
        help_text='Lista de contatos adicionais em formato JSON'
    )
    
    # Logo
    logomarca = models.ImageField(
        upload_to='unit_logos/',
        blank=True,
        null=True,
        verbose_name='Logomarca',
        help_text='Logo da clínica para uso em documentos'
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Dados da Unidade'
        verbose_name_plural = 'Dados da Unidade'
    
    def __str__(self):
        return self.nome_empreendimento
    
    @property
    def endereco_completo(self):
        """
        Retorna o endereço completo formatado.
        Exemplo: Rua das Flores, 123 - Centro - São Paulo/SP - CEP 01234-567
        """
        partes = []
        
        # Endereço e número
        if self.endereco:
            endereco_num = self.endereco
            if self.numero:
                endereco_num += f", {self.numero}"
            partes.append(endereco_num)
        
        # Bairro
        if self.bairro:
            partes.append(self.bairro)
        
        # Cidade e Estado
        if self.cidade:
            cidade_estado = self.cidade
            if self.estado:
                cidade_estado += f"/{self.estado}"
            partes.append(cidade_estado)
        
        # CEP
        if self.cep:
            partes.append(f"CEP {self.cep}")
        
        return " - ".join(partes) if partes else ""
    
    def save(self, *args, **kwargs):
        # Garantir que existe apenas um registro
        if not self.pk and DadosUnidade.objects.exists():
            # Se está tentando criar um novo registro e já existe um, atualiza o existente
            existing = DadosUnidade.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)

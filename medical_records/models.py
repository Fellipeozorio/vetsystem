from django.db import models
from django.contrib.auth.models import User
from patients.models import Pet
from scheduling.models import Agendamento


class MedicalRecord(models.Model):
    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='prontuarios'
    )

    appointment = models.OneToOneField(
        Agendamento,
        on_delete=models.CASCADE,
        related_name='prontuario'
    )

    veterinario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    queixa_principal = models.TextField()
    anamnese = models.TextField(blank=True, null=True)
    diagnostico = models.TextField(blank=True, null=True)
    cid = models.CharField(max_length=20, blank=True, null=True)

    tratamento = models.TextField(blank=True, null=True)
    orientacoes = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prontuário - {self.pet.nome}"


class Prescription(models.Model):
    prontuario = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='prescricoes'
    )

    medicamento = models.CharField(max_length=150)
    dosagem = models.CharField(max_length=100)
    frequencia = models.CharField(max_length=100)
    duracao = models.CharField(max_length=100)

    def __str__(self):
        return self.medicamento


class Vaccine(models.Model):
    prontuario = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='vacinas'
    )

    nome = models.CharField(max_length=100)
    data_aplicacao = models.DateField()
    proxima_dose = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.nome


class Attachment(models.Model):
    prontuario = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='anexos'
    )

    descricao = models.CharField(max_length=200)
    arquivo = models.FileField(upload_to='prontuarios/')

    def __str__(self):
        return self.descricao


# Novos modelos para a timeline de histórico médico

class Atendimento(models.Model):
    """Registro de atendimento clínico"""
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='atendimentos')
    tipo_atendimento = models.ForeignKey('cadastros.TipoAtendimento', on_delete=models.PROTECT)
    data_hora = models.DateTimeField()
    observacoes = models.TextField(blank=True)
    detalhes = models.TextField(blank=True)
    arquivo = models.FileField(upload_to='atendimentos/', blank=True, null=True)
    data_retorno = models.DateField(blank=True, null=True)
    hora_retorno = models.TimeField(blank=True, null=True)
    obs_retorno = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Atendimento'
        verbose_name_plural = 'Atendimentos'

    def __str__(self):
        return f"{self.tipo_atendimento.nome} - {self.pet.nome} ({self.data_hora.strftime('%d/%m/%Y %H:%M')})"


class Peso(models.Model):
    """Registro de peso do animal"""
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='pesos')
    data_hora = models.DateTimeField()
    peso = models.DecimalField(max_digits=7, decimal_places=3)
    condicao_corporal = models.CharField(max_length=50, blank=True)
    observacoes = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Peso'
        verbose_name_plural = 'Pesos'

    def __str__(self):
        return f"{self.pet.nome} - {self.peso}kg ({self.data_hora.strftime('%d/%m/%Y')})"


class Patologia(models.Model):
    """Registro de patologia/diagnóstico"""
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='patologias')
    patologia_cadastro = models.ForeignKey('cadastros.Patologia', on_delete=models.PROTECT, null=True, blank=True, verbose_name='Patologia')
    data_hora = models.DateTimeField()
    diagnostico = models.CharField(max_length=200)
    cid = models.CharField(max_length=20, blank=True)
    gravidade = models.CharField(max_length=50, blank=True)
    observacoes = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Patologia'
        verbose_name_plural = 'Patologias'

    def __str__(self):
        return f"{self.diagnostico} - {self.pet.nome}"


class Documento(models.Model):
    """Registro de documentos"""
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='documentos')
    data_hora = models.DateTimeField()
    modelo_documento = models.ForeignKey(
        'cadastros.ModeloDocumento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_gerados',
        verbose_name='Modelo de Documento'
    )
    conteudo = models.TextField(blank=True, default='', verbose_name='Conteúdo')
    tipo = models.CharField(max_length=100, blank=True)
    titulo = models.CharField(max_length=200, blank=True)
    descricao = models.TextField(blank=True)
    arquivo = models.FileField(upload_to='documentos/', null=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'

    def __str__(self):
        return f"{self.titulo} - {self.pet.nome}"


class Exame(models.Model):
    """Registro de exames"""
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='exames')
    data_hora = models.DateTimeField()
    tipo = models.CharField(max_length=100)
    nome = models.CharField(max_length=200)
    resultado = models.TextField(blank=True)
    exame_cadastro = models.ForeignKey(
        'cadastros.Exame', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='registros_prontuario'
    )
    itens_resultado = models.TextField(blank=True)  # JSON [{atributo_id, nome, resultado, unidade}]
    conclusoes = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Exame'
        verbose_name_plural = 'Exames'

    def __str__(self):
        return f"{self.nome} - {self.pet.nome}"


class ExameArquivo(models.Model):
    """Arquivos de resultados de exames"""
    exame = models.ForeignKey(Exame, on_delete=models.CASCADE, related_name='arquivos')
    arquivo = models.FileField(upload_to='exames/')
    
    def __str__(self):
        return f"Arquivo de {self.exame.nome}"


class Foto(models.Model):
    """Registro de fotos"""
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='fotos')
    data_hora = models.DateTimeField()
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'

    def __str__(self):
        return f"{self.titulo} - {self.pet.nome}"


class FotoArquivo(models.Model):
    """Arquivos de imagens"""
    foto = models.ForeignKey(Foto, on_delete=models.CASCADE, related_name='arquivos')
    arquivo = models.ImageField(upload_to='fotos/')
    
    def __str__(self):
        return f"Imagem de {self.foto.titulo}"


class VacinaRegistro(models.Model):
    """Registro de vacinas aplicadas"""
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='vacinas_aplicadas')
    data_hora = models.DateTimeField()
    nome = models.CharField(max_length=200)
    lote = models.CharField(max_length=100, blank=True)
    fabricante = models.CharField(max_length=200, blank=True)
    proxima_dose = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Vacina'
        verbose_name_plural = 'Vacinas'

    def __str__(self):
        return f"{self.nome} - {self.pet.nome}"


class Receita(models.Model):
    """Registro de receitas médicas"""
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='receitas')
    data_hora = models.DateTimeField()
    modelo_receita = models.ForeignKey(
        'cadastros.ModeloReceita',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receitas_geradas',
        verbose_name='Modelo de Receita'
    )
    conteudo = models.TextField(blank=True, default='', verbose_name='Conteúdo')
    tipo = models.CharField(max_length=100, blank=True)
    validade = models.DateField(blank=True, null=True)
    prescricao = models.TextField(blank=True, default='')
    observacoes = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Receita'
        verbose_name_plural = 'Receitas'

    def __str__(self):
        return f"Receita - {self.pet.nome} ({self.data_hora.strftime('%d/%m/%Y')})"


class Observacao(models.Model):
    """Registro de observações gerais"""
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='observacoes')
    data_hora = models.DateTimeField()
    titulo = models.CharField(max_length=200)
    texto = models.TextField(blank=True, default='')
    conteudo = models.TextField(blank=True, default='')
    categoria = models.CharField(max_length=100, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Observação'
        verbose_name_plural = 'Observações'

    def __str__(self):
        return f"{self.titulo} - {self.pet.nome}"


class ObservacaoAnexo(models.Model):
    """Arquivos anexados a observações"""
    observacao = models.ForeignKey(Observacao, on_delete=models.CASCADE, related_name='anexos')
    arquivo = models.FileField(upload_to='observacoes_anexos/')
    nome_original = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Anexo de {self.observacao.titulo}"


class Video(models.Model):
    """Registro de vídeos"""
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='videos')
    data_hora = models.DateTimeField()
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    arquivo = models.FileField(upload_to='videos/')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Vídeo'
        verbose_name_plural = 'Vídeos'

    def __str__(self):
        return f"{self.titulo} - {self.pet.nome}"


class Internacao(models.Model):
    """Registro de internações"""
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='internacoes')
    data_hora = models.DateTimeField()
    status = models.CharField(max_length=50)
    gravidade = models.CharField(max_length=50, blank=True)
    motivo = models.TextField()
    data_entrada = models.DateField()
    previsao_alta = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Internação'
        verbose_name_plural = 'Internações'

    def __str__(self):
        return f"Internação - {self.pet.nome} ({self.data_entrada.strftime('%d/%m/%Y')})"


class ProtocoloVacinaRegistro(models.Model):
    """Registro de protocolo de vacina para um pet"""
    STATUS_PROGRAMADA = 'programada'
    STATUS_INTERROMPIDA = 'interrompida'
    STATUS_CHOICES = [
        (STATUS_PROGRAMADA, 'Programada'),
        (STATUS_INTERROMPIDA, 'Interrompida'),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='protocolos_vacina')
    protocolo = models.ForeignKey(
        'cadastros.ProtocoloVacina',
        on_delete=models.PROTECT,
        related_name='registros_pet'
    )
    data_inicial = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PROGRAMADA)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_inicial']
        verbose_name = 'Protocolo de Vacina Registrado'
        verbose_name_plural = 'Protocolos de Vacinas Registrados'

    def __str__(self):
        return f"{self.protocolo.vacina.nome} - {self.pet.nome} ({self.data_inicial.strftime('%d/%m/%Y')})"


class DoseVacinaRegistro(models.Model):
    """Dose individual de um protocolo de vacina registrado"""
    STATUS_PROGRAMADA = 'programada'
    STATUS_APLICADA = 'aplicada'
    STATUS_CHOICES = [
        (STATUS_PROGRAMADA, 'Programada'),
        (STATUS_APLICADA, 'Aplicada'),
    ]

    protocolo_registro = models.ForeignKey(
        ProtocoloVacinaRegistro,
        on_delete=models.CASCADE,
        related_name='doses'
    )
    numero_dose = models.PositiveIntegerField()
    data_programada = models.DateField()
    data_aplicacao = models.DateTimeField(blank=True, null=True)
    laboratorio = models.CharField(max_length=200, blank=True)
    lote = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PROGRAMADA)

    class Meta:
        ordering = ['numero_dose']
        verbose_name = 'Dose de Vacina'
        verbose_name_plural = 'Doses de Vacinas'

    def __str__(self):
        vacina = self.protocolo_registro.protocolo.vacina.nome
        return f"Dose {self.numero_dose} - {vacina} ({self.data_programada.strftime('%d/%m/%Y')})"


from django.db import models
from django.core.exceptions import ValidationError


class Marcacao(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome


class Client(models.Model):
    PESSOA_FISICA = 'F'
    PESSOA_JURIDICA = 'J'
    PERSON_TYPE_CHOICES = [
        (PESSOA_FISICA, 'Pessoa física'),
        (PESSOA_JURIDICA, 'Pessoa jurídica'),
    ]

    SEXO_M = 'M'
    SEXO_F = 'F'
    SEXO_CHOICES = [
        (SEXO_M, 'Masculino'),
        (SEXO_F, 'Feminino'),
    ]

    # Dualidade
    person_type = models.CharField(max_length=1, choices=PERSON_TYPE_CHOICES, default=PESSOA_FISICA)

    # Campos comuns / contato
    nome_completo = models.CharField(max_length=150)
    # Nacionalidade: Brasileiro / Estrangeiro
    NACIONALIDADE_BR = 'BR'
    NACIONALIDADE_EX = 'EX'
    NACIONALIDADE_CHOICES = [
        (NACIONALIDADE_BR, 'Brasileiro'),
        (NACIONALIDADE_EX, 'Estrangeiro'),
    ]
    nacionalidade = models.CharField(max_length=2, choices=NACIONALIDADE_CHOICES, blank=True, null=True, default=NACIONALIDADE_BR)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, blank=True, null=True)

    # Pessoa física
    cpf = models.CharField(max_length=20, blank=True, null=True)
    rg = models.CharField(max_length=30, blank=True, null=True)
    aniversario = models.DateField(blank=True, null=True)
    inscricao_municipal = models.CharField(max_length=50, blank=True, null=True)

    # Pessoa jurídica
    razao_social = models.CharField(max_length=150, blank=True, null=True)
    cnpj = models.CharField(max_length=20, blank=True, null=True)
    regime_tributario = models.CharField(max_length=100, blank=True, null=True)
    tipo_inscricao_estadual = models.CharField(max_length=50, blank=True, null=True)
    inscricao_estadual = models.CharField(max_length=50, blank=True, null=True)

    # Contato e preferências (exibidos independente da dualidade)
    origem = models.ForeignKey('cadastros.OrigemCliente', on_delete=models.SET_NULL, blank=True, null=True)
    profissao = models.CharField(max_length=150, blank=True, null=True)
    aceita_email = models.BooleanField(default=False)
    aceita_whatsapp = models.BooleanField(default=False)
    aceita_sms = models.BooleanField(default=False)
    aceita_campanha_sms = models.BooleanField(default=False)

    email = models.EmailField(blank=True, null=True)
    celular = models.CharField(max_length=30)
    este_numero_e_whatsapp = models.BooleanField(default=False)

    # Endereço (segunda aba)
    cep = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.CharField(max_length=250, blank=True, null=True)
    numero = models.CharField(max_length=50, blank=True, null=True)
    complemento = models.CharField(max_length=150, blank=True, null=True)
    ponto_referencia = models.CharField(max_length=200, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=50, blank=True, null=True)

    # Extra (terceira aba)
    observacoes = models.TextField(blank=True, null=True)
    marcacoes = models.ManyToManyField(Marcacao, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.person_type == self.PESSOA_JURIDICA and self.razao_social:
            return f"{self.razao_social} ({self.nome_completo})"
        return self.nome_completo

    def clean(self):
        super().clean()
        errors = {}
        if self.person_type == self.PESSOA_FISICA:
            if not self.cpf:
                errors['cpf'] = 'CPF obrigatório para pessoa física.'
        if self.person_type == self.PESSOA_JURIDICA:
            if not self.cnpj:
                errors['cnpj'] = 'CNPJ obrigatório para pessoa jurídica.'
        if errors:
            raise ValidationError(errors)

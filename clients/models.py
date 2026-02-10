from django.db import models
from django.core.validators import RegexValidator


class Client(models.Model):
    TIPO_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]
    
    NACIONALIDADE_CHOICES = [
        ('brasileiro', 'Brasileiro'),
        ('estrangeiro', 'Estrangeiro'),
    ]
    
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
    ]
    
    REGIME_TRIBUTARIO_CHOICES = [
        ('normal', 'Normal'),
        ('simples', 'Simples'),
    ]
    
    INSCRICAO_ESTADUAL_CHOICES = [
        ('contribuinte', 'Contribuinte de ICMS'),
        ('nao_contribuinte', 'Não contribuinte de ICMS'),
        ('isento', 'Isento de inscrição'),
    ]
    
    CONHECEU_CHOICES = [
        ('rua', 'Passando na rua'),
        ('facebook', 'Facebook'),
        ('site', 'Site'),
        ('instagram', 'Instagram'),
        ('indicacao', 'Indicação'),
        ('outros', 'Outros'),
    ]
    
    ESTADO_CHOICES = [
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins'),
    ]
    
    TIPO_CONTATO_CHOICES = [
        ('celular', 'Celular'),
        ('email', 'E-mail'),
        ('telefone_residencial', 'Telefone Residencial'),
        ('telefone_comercial', 'Telefone Comercial'),
        ('outros', 'Outros'),
    ]
    
    # Número sequencial interno
    codigo = models.PositiveIntegerField(unique=True, editable=False, null=True, blank=True)
    
    # Informações básicas
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES, default='PF')
    nome_completo = models.CharField(max_length=200)
    
    # Pessoa Física
    nacionalidade = models.CharField(max_length=20, choices=NACIONALIDADE_CHOICES, blank=True, null=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, blank=True, null=True)
    cpf = models.CharField(max_length=14, blank=True, null=True, unique=True)
    rg = models.CharField(max_length=20, blank=True, null=True)
    data_aniversario = models.DateField(blank=True, null=True)
    profissao = models.CharField(max_length=100, blank=True, null=True)
    
    # Pessoa Jurídica
    cnpj = models.CharField(max_length=18, blank=True, null=True, unique=True)
    regime_tributario = models.CharField(max_length=20, choices=REGIME_TRIBUTARIO_CHOICES, blank=True, null=True)
    inscricao_estadual = models.CharField(max_length=30, choices=INSCRICAO_ESTADUAL_CHOICES, blank=True, null=True)
    
    # Comum a ambos
    inscricao_municipal = models.CharField(max_length=50, blank=True, null=True)
    como_conheceu = models.CharField(max_length=20, choices=CONHECEU_CHOICES, blank=True, null=True)
    
    # Contatos principais
    celular = models.CharField(max_length=20, default='')
    celular_whatsapp = models.BooleanField(default=True)
    email = models.EmailField(blank=True, null=True)
    
    # Endereço
    cep = models.CharField(max_length=9, blank=True, null=True)
    endereco = models.CharField(max_length=200, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, choices=ESTADO_CHOICES, blank=True, null=True)
    ponto_referencia = models.CharField(max_length=200, blank=True, null=True)
    
    # Informações complementares
    tags = models.CharField(max_length=500, blank=True, help_text='Tags separadas por vírgula')
    observacoes = models.TextField(blank=True, null=True)
    
    # Preferências de privacidade
    aceita_email = models.BooleanField(default=True)
    aceita_sms = models.BooleanField(default=True)
    aceita_whatsapp = models.BooleanField(default=True)
    aceita_campanha_sms = models.BooleanField(default=True)
    
    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['codigo']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
    
    def save(self, *args, **kwargs):
        if not self.codigo:
            # Gerar próximo código sequencial
            ultimo = Client.objects.order_by('-codigo').first()
            self.codigo = (ultimo.codigo + 1) if ultimo else 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.codigo} - {self.nome_completo}"
    
    def get_tags_list(self):
        """Retorna lista de tags"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []


class ContatoAdicional(models.Model):
    """Contatos adicionais do cliente"""
    TIPO_CHOICES = [
        ('celular', 'Celular'),
        ('email', 'E-mail'),
        ('telefone_residencial', 'Telefone Residencial'),
        ('telefone_comercial', 'Telefone Comercial'),
        ('outros', 'Outros'),
    ]
    
    cliente = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contatos_adicionais')
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    valor = models.CharField(max_length=200)
    whatsapp = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Contato Adicional'
        verbose_name_plural = 'Contatos Adicionais'
    
    def __str__(self):
        return f"{self.cliente.nome_completo} - {self.get_tipo_display()}: {self.valor}"

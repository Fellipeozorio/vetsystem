from django.db import models
from clients.models import Client
from cadastros.models import Especie, Raca, Pelagem


class Pet(models.Model):

    SEXO_CHOICES = [
        ('M', 'Macho'),
        ('F', 'Fêmea'),
        ('I', 'Indeterminado'),
    ]
    
    ESTERILIZACAO_CHOICES = [
        ('fertil', 'Fértil'),
        ('castrado', 'Castrado'),
        ('vasectomizado', 'Vasectomizado'),
    ]
    
    STATUS_CHOICES = [
        ('vivo', 'Vivo'),
        ('obito', 'Óbito'),
    ]

    # Código sequencial
    codigo = models.PositiveIntegerField(unique=True, editable=False, null=True, blank=True)
    
    # Status do animal
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='vivo')

    tutor = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='pets'
    )

    nome = models.CharField(max_length=100)

    especie = models.ForeignKey(
        Especie,
        on_delete=models.PROTECT
    )

    raca = models.ForeignKey(
        Raca,
        on_delete=models.PROTECT
    )

    pelagem = models.ForeignKey(
        Pelagem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    esterilizacao = models.CharField(max_length=20, choices=ESTERILIZACAO_CHOICES, blank=True, null=True)

    data_nascimento = models.DateField(blank=True, null=True)
    idade_estimada = models.PositiveIntegerField(blank=True, null=True)

    peso = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )

    porte = models.CharField(max_length=50, blank=True, null=True)
    caracteristicas = models.TextField(blank=True, null=True)

    microchip = models.CharField(max_length=50, blank=True, null=True)
    temperamento = models.TextField(blank=True, null=True)
    
    # Marcações (tags)
    marcacoes = models.CharField(max_length=500, blank=True, help_text='Tags separadas por vírgula')
    
    # Pedigree
    pedigree = models.BooleanField(default=False)
    numero_pedigree = models.CharField(max_length=100, blank=True, null=True)

    foto = models.ImageField(
        upload_to='pets/',
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['codigo']
        verbose_name = 'Animal'
        verbose_name_plural = 'Animais'
    
    def save(self, *args, **kwargs):
        if not self.codigo:
            # Gerar próximo código sequencial
            ultimo = Pet.objects.order_by('-codigo').first()
            self.codigo = (ultimo.codigo + 1) if ultimo else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nome} ({self.tutor.nome_completo})"
    
    def get_marcacoes_list(self):
        """Retorna lista de marcações"""
        if self.marcacoes:
            return [tag.strip() for tag in self.marcacoes.split(',')]
        return []
    
    def get_avatar_icon(self):
        """Retorna o ícone de avatar padrão baseado na espécie"""
        if self.foto:
            return self.foto.url
        
        especie_nome = self.especie.nome.lower()
        if 'felino' in especie_nome or 'gato' in especie_nome:
            return 'cat'
        elif 'canino' in especie_nome or 'cão' in especie_nome or 'cachorro' in especie_nome:
            return 'dog'
        else:
            return 'paw'

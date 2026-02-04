from django.db import models
from clients.models import Client


class Pet(models.Model):

    SEXO_CHOICES = [
        ('M', 'Macho'),
        ('F', 'Fêmea'),
    ]

    ESPECIE_CHOICES = [
        ('CAO', 'Cão'),
        ('GATO', 'Gato'),
        ('OUTRO', 'Outro'),
    ]

    tutor = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='pets'
    )

    nome = models.CharField(max_length=100)
    especie = models.CharField(max_length=10, choices=ESPECIE_CHOICES)
    raca = models.CharField(max_length=100, blank=True, null=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)

    data_nascimento = models.DateField(blank=True, null=True)
    idade_estimada = models.PositiveIntegerField(blank=True, null=True)

    peso = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )

    porte = models.CharField(max_length=50, blank=True, null=True)
    cor_pelagem = models.CharField(max_length=100, blank=True, null=True)
    caracteristicas = models.TextField(blank=True, null=True)

    microchip = models.CharField(max_length=50, blank=True, null=True)
    temperamento = models.TextField(blank=True, null=True)

    foto = models.ImageField(
        upload_to='pets/',
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nome} ({self.tutor.nome_completo})"

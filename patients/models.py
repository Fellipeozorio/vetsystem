from django.db import models
from clients.models import Client
from cadastros.models import Especie, Raca, Pelagem


class Pet(models.Model):

    SEXO_CHOICES = [
        ('M', 'Macho'),
        ('F', 'Fêmea'),
    ]

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

    foto = models.ImageField(
        upload_to='pets/',
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nome} ({self.tutor.nome_completo})"

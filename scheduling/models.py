from django.db import models
from django.contrib.auth.models import User
from clients.models import Client
from patients.models import Pet


class Appointment(models.Model):

    STATUS_CHOICES = [
        ('AGENDADA', 'Agendada'),
        ('CONFIRMADA', 'Confirmada'),
        ('REALIZADA', 'Realizada'),
        ('CANCELADA', 'Cancelada'),
        ('REMARCADA', 'Remarcada'),
        ('NO_SHOW', 'Não compareceu'),
    ]

    SERVICO_CHOICES = [
        ('CONSULTA', 'Consulta'),
        ('VACINA', 'Vacinação'),
        ('BANHO', 'Banho'),
        ('TOSA', 'Tosa'),
        ('CIRURGIA', 'Cirurgia'),
    ]

    tutor = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='consultas'
    )

    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='consultas'
    )

    veterinario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas'
    )

    servico = models.CharField(max_length=20, choices=SERVICO_CHOICES)

    data_hora_inicio = models.DateTimeField()
    data_hora_fim = models.DateTimeField()

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='AGENDADA'
    )

    observacoes = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pet.nome} - {self.get_servico_display()} ({self.data_hora_inicio:%d/%m/%Y %H:%M})"


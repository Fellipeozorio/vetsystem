from django.db import models
from django.contrib.auth.models import User
from patients.models import Pet
from scheduling.models import Appointment


class MedicalRecord(models.Model):
    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='prontuarios'
    )

    appointment = models.OneToOneField(
        Appointment,
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

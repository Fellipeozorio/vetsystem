from django.db import models


class Client(models.Model):
    nome_completo = models.CharField(max_length=150)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    rg = models.CharField(max_length=20, blank=True, null=True)

    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True, null=True)

    endereco = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome_completo

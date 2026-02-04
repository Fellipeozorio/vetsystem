from django.db import models
from django.db.models import Sum
from datetime import date

class FinancialEntry(models.Model):

    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
    ]

    FORMA_PAGAMENTO_CHOICES = [
        ('DINHEIRO', 'Dinheiro'),
        ('CREDITO', 'Cartão de Crédito'),
        ('DEBITO', 'Cartão de Débito'),
        ('PIX', 'PIX'),
    ]

    descricao = models.CharField(max_length=200)

    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES
    )

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    forma_pagamento = models.CharField(
        max_length=20,
        choices=FORMA_PAGAMENTO_CHOICES
    )

    data = models.DateTimeField(auto_now_add=True)

    venda = models.OneToOneField(
        'sales.Sale',
        on_delete=models.CASCADE,
        related_name='financeiro',
        null=True,
        blank=True
    )

    caixa = models.ForeignKey(
        'billing.CashRegister',
        on_delete=models.PROTECT,
        related_name='lancamentos',
        null=True,
        blank=True
    )

    @classmethod
    def total_entradas(cls, inicio, fim):
        return cls.objects.filter(
            tipo='ENTRADA',
            data__date__range=(inicio, fim)
        ).aggregate(total=Sum('valor'))['total'] or 0

    @classmethod
    def total_saidas(cls, inicio, fim):
        return cls.objects.filter(
            tipo='SAIDA',
            data__date__range=(inicio, fim)
        ).aggregate(total=Sum('valor'))['total'] or 0
    
    @classmethod
    def dre(cls, inicio, fim):
        receitas = cls.total_entradas(inicio, fim)
        despesas = cls.total_saidas(inicio, fim)
        resultado = receitas - despesas

        return {
            'receitas': receitas,
            'despesas': despesas,
            'resultado': resultado
        }
    
    @classmethod
    def fluxo_caixa(cls, inicio, fim):
        return cls.objects.filter(
            data__date__range=(inicio, fim)
        ).values(
            'data__date',
            'tipo'
        ).annotate(
            total=Sum('valor')
        ).order_by('data__date')


    def __str__(self):
        return f"{self.descricao} - R$ {self.valor}"


class CashRegister(models.Model):

    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('FECHADO', 'Fechado'),
    ]

    data = models.DateField(auto_now_add=True)

    valor_abertura = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    valor_fechamento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ABERTO'
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    @classmethod
    def caixa_aberto(cls):
        return cls.objects.filter(status='ABERTO').first()

    def __str__(self):
        return f"Caixa {self.data} - {self.status}"

    def calcular_total_entradas(self):
        return sum(
            entry.valor
            for entry in self.lancamentos.filter(tipo='ENTRADA')
        )

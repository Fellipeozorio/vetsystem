from django.db import models
from inventory.models import Product


class Service(models.Model):

    nome = models.CharField(max_length=100)
    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Sale(models.Model):

    STATUS_CHOICES = [
        ('ABERTA', 'Aberta'),
        ('PAGA', 'Paga'),
        ('CANCELADA', 'Cancelada'),
    ]

    FORMA_PAGAMENTO_CHOICES = [
        ('DINHEIRO', 'Dinheiro'),
        ('CREDITO', 'Cartão de Crédito'),
        ('DEBITO', 'Cartão de Débito'),
        ('PIX', 'PIX'),
    ]

    data = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ABERTA'
    )

    forma_pagamento = models.CharField(
        max_length=20,
        choices=FORMA_PAGAMENTO_CHOICES,
        blank=True,
        null=True
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def gerar_lancamento_financeiro(self):
        from billing.models import FinancialEntry, CashRegister

        if hasattr(self, 'financeiro'):
            return

        if self.status == 'PAGA':
            caixa = CashRegister.caixa_aberto()

            FinancialEntry.objects.create(
                descricao=f"Venda #{self.id}",
                tipo='ENTRADA',
                valor=self.total,
                forma_pagamento=self.forma_pagamento,
                venda=self,
                caixa=caixa
            )

    def atualizar_total(self):
        total = sum(item.subtotal for item in self.itens.all())
        self.total = total
        self.save()

    def __str__(self):
        return f"Venda #{self.id}"


class SaleItem(models.Model):

    venda = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='itens'
    )

    produto = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    servico = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    quantidade = models.PositiveIntegerField(default=1)

    preco_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def save(self, *args, **kwargs):

        # Define preço automaticamente
        if self.produto:
            self.preco_unitario = self.produto.preco_venda

        if self.servico:
            self.preco_unitario = self.servico.preco

        # Calcula subtotal
        self.subtotal = self.quantidade * self.preco_unitario

        # Baixa estoque SOMENTE se for produto
        if not self.pk and self.produto:
            self.produto.estoque_atual -= self.quantidade
            self.produto.save()

        super().save(*args, **kwargs)

    def __str__(self):
        if self.produto:
            return self.produto.nome
        return self.servico.nome


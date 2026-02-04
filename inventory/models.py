from django.db import models


class Product(models.Model):
    nome = models.CharField(max_length=150)
    codigo_barras = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    descricao = models.TextField(blank=True, null=True)

    preco_custo = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    preco_venda = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    estoque_atual = models.PositiveIntegerField(default=0)
    estoque_minimo = models.PositiveIntegerField(default=0)

    fornecedor = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class StockMovement(models.Model):

    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
    ]

    produto = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='movimentacoes'
    )

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    quantidade = models.PositiveIntegerField()
    data = models.DateTimeField(auto_now_add=True)
    observacao = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.produto.nome}"


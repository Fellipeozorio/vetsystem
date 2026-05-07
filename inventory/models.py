from django.db import models
from datetime import date


class Brand(models.Model):
    nome = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'

    def __str__(self):
        return self.nome


class Product(models.Model):
    TIPO_CHOICES = [
        ('produto', 'Produto'),
        ('servico', 'Serviço'),
    ]

    nome = models.CharField(max_length=150)
    codigo = models.CharField(max_length=50, blank=True, null=True)
    codigo_barras = models.CharField(max_length=50, blank=True, null=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='produto')
    marca = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos'
    )

    descricao = models.TextField(blank=True, null=True)

    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    markup = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    estoque_atual = models.PositiveIntegerField(default=0)
    estoque_minimo = models.PositiveIntegerField(default=0)
    estoque_maximo = models.PositiveIntegerField(default=0)

    validade = models.DateField(blank=True, null=True)
    pendencia_fiscal = models.BooleanField(default=False)

    fornecedor = models.CharField(max_length=150, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Produto/Serviço'
        verbose_name_plural = 'Produtos/Serviços'

    def __str__(self):
        return self.nome

    def situacao_estoque(self):
        if self.tipo == 'servico':
            return None
        if self.estoque_minimo > 0 and self.estoque_atual < self.estoque_minimo:
            return 'repor'
        if self.estoque_maximo > 0 and self.estoque_atual > self.estoque_maximo:
            return 'excesso'
        if self.estoque_atual == 0:
            return 'repor'
        return 'adequado'

    def situacao_estoque_label(self):
        mapa = {
            'repor': ('Repor', 'danger'),
            'excesso': ('Excesso', 'warning'),
            'adequado': ('Adequado', 'success'),
            None: ('—', 'secondary'),
        }
        return mapa.get(self.situacao_estoque(), ('—', 'secondary'))

    def validade_vencida(self):
        if self.validade:
            return self.validade < date.today()
        return False

    def vencendo_em_60_dias(self):
        if self.validade:
            from datetime import timedelta
            limite = date.today() + timedelta(days=60)
            return date.today() <= self.validade <= limite
        return False


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


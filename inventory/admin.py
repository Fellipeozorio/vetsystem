from django.contrib import admin
from .models import Product, StockMovement


class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    readonly_fields = ('data',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'estoque_atual',
        'estoque_minimo',
        'preco_venda',
        'ativo',
    )

    list_filter = ('ativo',)
    search_fields = ('nome', 'codigo_barras')
    inlines = [StockMovementInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('produto', 'tipo', 'quantidade', 'data')
    list_filter = ('tipo', 'data')


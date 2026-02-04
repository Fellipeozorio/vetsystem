from django.contrib import admin
from .models import Sale, SaleItem, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome',)


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'data', 'status', 'total', 'forma_pagamento')
    list_filter = ('status', 'data')
    inlines = [SaleItemInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.atualizar_total()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.gerar_lancamento_financeiro()

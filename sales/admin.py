from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from datetime import date
from .models import Sale, SaleItem, Service, CashRegister, FinancialEntry


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


class FinancialEntryInline(admin.TabularInline):
    model = FinancialEntry
    extra = 0
    readonly_fields = ('descricao', 'tipo', 'valor', 'forma_pagamento', 'data')


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ('data', 'status', 'valor_abertura', 'valor_fechamento')
    inlines = [FinancialEntryInline]

    def save_model(self, request, obj, form, change):
        if obj.status == 'FECHADO' and obj.valor_fechamento is None:
            total = obj.calcular_total_entradas()
            obj.valor_fechamento = obj.valor_abertura + total
        super().save_model(request, obj, form, change)


@admin.register(FinancialEntry)
class FinancialEntryAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'tipo', 'valor', 'forma_pagamento', 'data', 'caixa')
    list_filter = ('tipo', 'forma_pagamento', 'data')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'relatorios/',
                self.admin_site.admin_view(self.relatorios),
                name='financeiro-relatorios'
            )
        ]
        return custom_urls + urls

    def relatorios(self, request):
        hoje = date.today()
        inicio = request.GET.get('inicio', hoje.replace(day=1))
        fim = request.GET.get('fim', hoje)

        dre = FinancialEntry.dre(inicio, fim)
        fluxo = FinancialEntry.fluxo_caixa(inicio, fim)

        context = dict(
            self.admin_site.each_context(request),
            dre=dre,
            fluxo=fluxo,
            inicio=inicio,
            fim=fim
        )

        return render(request, 'admin/financeiro_relatorios.html', context)

    def has_view_permission(self, request, obj=None):
        return request.user.groups.filter(name='Administrador').exists()

    def has_add_permission(self, request):
        return request.user.groups.filter(name='Administrador').exists()


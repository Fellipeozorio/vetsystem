from django.contrib import admin
from .models import Client, ContatoAdicional
from patients.models import Pet


class PetInline(admin.TabularInline):
    model = Pet
    extra = 1
    fields = ('nome', 'especie', 'raca', 'sexo', 'data_nascimento')


class ContatoAdicionalInline(admin.TabularInline):
    model = ContatoAdicional
    extra = 0
    fields = ('tipo', 'valor', 'whatsapp', 'observacoes')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome_completo', 'tipo', 'celular', 'email', 'cidade', 'criado_em')
    list_filter = ('tipo', 'nacionalidade', 'estado', 'aceita_email', 'aceita_sms', 'aceita_whatsapp')
    search_fields = ('nome_completo', 'cpf', 'cnpj', 'celular', 'email', 'codigo')
    readonly_fields = ('codigo', 'criado_em', 'atualizado_em')
    inlines = [ContatoAdicionalInline, PetInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('codigo', 'tipo', 'nome_completo')
        }),
        ('Pessoa Física', {
            'fields': ('nacionalidade', 'sexo', 'cpf', 'rg', 'data_aniversario', 'profissao'),
            'classes': ('collapse',)
        }),
        ('Pessoa Jurídica', {
            'fields': ('cnpj', 'regime_tributario', 'inscricao_estadual'),
            'classes': ('collapse',)
        }),
        ('Informações Adicionais', {
            'fields': ('inscricao_municipal', 'como_conheceu')
        }),
        ('Contatos', {
            'fields': ('celular', 'celular_whatsapp', 'email')
        }),
        ('Endereço', {
            'fields': ('cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'ponto_referencia')
        }),
        ('Informações Complementares', {
            'fields': ('tags', 'observacoes')
        }),
        ('Preferências de Privacidade', {
            'fields': ('aceita_email', 'aceita_sms', 'aceita_whatsapp', 'aceita_campanha_sms')
        }),
        ('Metadados', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContatoAdicional)
class ContatoAdicionalAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'tipo', 'valor', 'whatsapp')
    list_filter = ('tipo', 'whatsapp')
    search_fields = ('cliente__nome_completo', 'valor')

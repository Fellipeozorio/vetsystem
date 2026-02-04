from django.contrib import admin
from .models import Client
from patients.models import Pet


class PetInline(admin.TabularInline):
    model = Pet
    extra = 1


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'telefone', 'email')
    search_fields = ('nome_completo', 'cpf', 'telefone')
    inlines = [PetInline]

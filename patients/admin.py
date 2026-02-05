from django.contrib import admin
from .models import Pet


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('nome', 'especie', 'sexo', 'tutor')
    list_filter = ('especie', 'sexo')
    search_fields = ('nome', 'tutor__nome_completo')
    autocomplete_fields = ('especie', 'raca')

from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'pet',
        'tutor',
        'servico',
        'data_hora_inicio',
        'status',
        'veterinario',
    )

    list_filter = ('status', 'servico', 'data_hora_inicio')
    search_fields = ('pet__nome', 'tutor__nome_completo')
    date_hierarchy = 'data_hora_inicio'

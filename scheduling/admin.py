from django.contrib import admin
from .models import Agendamento, HorarioFuncionamento, ConfiguracaoAgendaUsuario, FilaDiaCalendario


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = (
        'animal',
        'cliente',
        'tipo_atendimento',
        'data',
        'horario',
        'status',
        'fila',
        'veterinario',
    )

    list_filter = ('status', 'data', 'tipo_atendimento', 'fila')
    search_fields = ('animal__nome', 'cliente__nome_completo', 'tipo_atendimento__nome')
    date_hierarchy = 'data'


@admin.register(HorarioFuncionamento)
class HorarioFuncionamentoAdmin(admin.ModelAdmin):
    list_display = ('dia_semana', 'horario_inicio', 'horario_fim', 'ativo')
    list_filter = ('ativo', 'dia_semana')


@admin.register(ConfiguracaoAgendaUsuario)
class ConfiguracaoAgendaUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo_atendimento', 'permissao_agenda', 'ativo')
    list_filter = ('tipo_atendimento', 'permissao_agenda', 'ativo')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')


@admin.register(FilaDiaCalendario)
class FilaDiaCalendarioAdmin(admin.ModelAdmin):
    list_display = ('fila', 'data', 'ativo', 'criado_por')
    list_filter = ('ativo', 'data', 'fila')
    search_fields = ('fila__nome',)
    date_hierarchy = 'data'


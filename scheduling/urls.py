from django.urls import path
from . import views

app_name = 'scheduling'

urlpatterns = [
    # Página principal da agenda
    path('agenda/', views.agenda_view, name='agenda'),
    
    # Configuração da agenda
    path('agenda/configuracao/', views.configuracao_view, name='configuracao'),
    
    # API para FullCalendar
    path('api/eventos/', views.get_eventos_api, name='get_eventos_api'),
    path('api/agendamento/criar/', views.criar_agendamento_api, name='criar_agendamento_api'),
    path('api/agendamento/<int:pk>/', views.get_agendamento_api, name='get_agendamento_api'),
    path('api/agendamento/<int:pk>/editar/', views.editar_agendamento_api, name='editar_agendamento_api'),
    path('api/agendamento/<int:pk>/deletar/', views.deletar_agendamento_api, name='deletar_agendamento_api'),
    path('api/agendamentos/atualizar-ordem/', views.atualizar_ordem_agendamentos_api, name='atualizar_ordem_agendamentos_api'),
    
    # API para autocomplete
    path('api/clientes/', views.get_clientes_api, name='get_clientes_api'),
    path('api/buscar-clientes/', views.buscar_clientes_api, name='buscar_clientes_api'),
    path('api/animais/<int:cliente_id>/', views.get_animais_api, name='get_animais_api'),
    path('api/cliente/<int:pk>/', views.get_cliente_detalhes_api, name='get_cliente_detalhes_api'),
    path('api/fila/<int:pk>/detalhes/', views.get_fila_detalhes_api, name='get_fila_detalhes_api'),
    path('api/veterinarios/', views.get_veterinarios_api, name='get_veterinarios_api'),
    
    # API para filas
    path('api/filas/<str:data>/', views.get_filas_dia_api, name='get_filas_dia_api'),
    path('api/fila-dia/adicionar/', views.adicionar_fila_dia_api, name='adicionar_fila_dia_api'),
    path('api/fila-dia/remover/', views.remover_fila_dia_api, name='remover_fila_dia_api'),
    
    # Configuração - Horários
    path('api/horarios/', views.get_horarios_api, name='get_horarios_api'),
    path('api/horarios/salvar/', views.salvar_horarios_api, name='salvar_horarios_api'),
    path('api/horario/<int:pk>/editar/', views.editar_horario_api, name='editar_horario_api'),
    
    # Configuração - Usuários
    path('api/usuarios-config/', views.get_usuarios_config_api, name='get_usuarios_config_api'),
    path('api/usuario-config/<int:pk>/', views.get_usuario_config_api, name='get_usuario_config_api'),
    path('api/usuario-config/<int:pk>/editar/', views.editar_usuario_config_api, name='editar_usuario_config_api'),
    path('api/usuario-config/<int:pk>/salvar/', views.editar_usuario_config_api, name='salvar_usuario_config_api'),
]

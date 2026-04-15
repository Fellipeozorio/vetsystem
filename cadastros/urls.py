from django.urls import path
from . import views

app_name = 'cadastros'

urlpatterns = [
    # ===== API ENDPOINTS =====
    path('api/tipos-atendimento/', views.api_tipos_atendimento_list, name='api_tipos_atendimento_list'),
    path('api/tipos-atendimento/<int:pk>/template/', views.api_tipo_atendimento_template, name='api_tipo_atendimento_template'),
    path('api/filas-atendimento/', views.api_filas_atendimento_list, name='api_filas_atendimento_list'),
    path('api/patologias/', views.api_patologias_list, name='api_patologias_list'),
    path('api/modelos-documento/', views.api_modelos_documento_list, name='api_modelos_documento_list'),
    path('api/modelos-documento/<int:pk>/', views.api_modelo_documento_detail, name='api_modelo_documento_detail'),
    
    # URLs específicas para tipos de atendimento (devem vir antes das genéricas)
    path('tipos-atendimento/', views.tipos_atendimento_list, name='tipos_atendimento_list'),
    path('tipos-atendimento/criar/', views.tipo_atendimento_create, name='tipo_atendimento_create'),
    path('tipos-atendimento/<int:pk>/editar/', views.tipo_atendimento_edit, name='tipo_atendimento_edit'),
    path('tipos-atendimento/<int:pk>/excluir/', views.tipo_atendimento_delete, name='tipo_atendimento_delete'),
    
    # URLs específicas para filas de atendimento
    path('filas-atendimento/', views.filas_atendimento_list, name='filas_atendimento_list'),
    path('filas-atendimento/criar/', views.fila_atendimento_create, name='fila_atendimento_create'),
    path('filas-atendimento/<int:pk>/', views.fila_atendimento_detail, name='fila_atendimento_detail'),
    path('filas-atendimento/<int:pk>/editar/', views.fila_atendimento_update, name='fila_atendimento_update'),
    path('filas-atendimento/<int:pk>/excluir/', views.fila_atendimento_delete, name='fila_atendimento_delete'),
    
    # URLs específicas para exames
    path('exames/', views.exames_list, name='exames_list'),
    path('exames/criar/', views.exame_create, name='exame_create'),
    path('exames/<int:pk>/editar/', views.exame_edit, name='exame_edit'),
    path('exames/<int:pk>/excluir/', views.exame_delete, name='exame_delete'),
    
    # URLs específicas para atributos de exames
    path('atributos-exames/', views.atributos_exames_list, name='atributos_exames_list'),
    path('atributos-exames/criar/', views.atributo_exame_create, name='atributo_exame_create'),
    path('atributos-exames/<int:pk>/', views.atributo_exame_detail, name='atributo_exame_detail'),
    path('atributos-exames/<int:pk>/editar/', views.atributo_exame_update, name='atributo_exame_update'),
    path('atributos-exames/<int:pk>/excluir/', views.atributo_exame_delete, name='atributo_exame_delete'),
    
    # URLs específicas para receitas
    path('receitas/', views.receitas_list, name='receitas_list'),
    path('receitas/criar/', views.receita_create, name='receita_create'),
    path('receitas/<int:pk>/editar/', views.receita_edit, name='receita_edit'),
    path('receitas/<int:pk>/excluir/', views.receita_delete, name='receita_delete'),
    
    # URLs específicas para documentos
    path('documentos/', views.documentos_list, name='documentos_list'),
    path('documentos/criar/', views.documento_create, name='documento_create'),
    path('documentos/<int:pk>/editar/', views.documento_edit, name='documento_edit'),
    path('documentos/<int:pk>/excluir/', views.documento_delete, name='documento_delete'),
    
    # URLs para protocolos de vacinas
    path('vacinas/<int:vacina_id>/protocolos/', views.vacina_protocolos_list, name='vacina_protocolos_list'),
    path('protocolos/create/', views.protocolo_create, name='protocolo_create'),
    path('protocolos/<int:pk>/update/', views.protocolo_update, name='protocolo_update'),
    path('protocolos/<int:pk>/delete/', views.protocolo_delete, name='protocolo_delete'),
    
    # URL para dados da unidade
    path('dados-unidade/', views.dados_unidade_view, name='dados_unidade'),
    
    # URLs genéricas para todos os outros cadastros
    path('<str:tipo>/', views.cadastro_list, name='list'),
    path('<str:tipo>/criar/', views.cadastro_create, name='create'),
    path('<str:tipo>/<int:pk>/', views.cadastro_detail, name='detail'),
    path('<str:tipo>/<int:pk>/editar/', views.cadastro_update, name='update'),
    path('<str:tipo>/<int:pk>/excluir/', views.cadastro_delete, name='delete'),
]

from django.urls import path
from . import views

app_name = 'cadastros'

urlpatterns = [
    # URLs específicas para tipos de atendimento (devem vir antes das genéricas)
    path('tipos-atendimento/', views.tipos_atendimento_list, name='tipos_atendimento_list'),
    path('tipos-atendimento/criar/', views.tipo_atendimento_create, name='tipo_atendimento_create'),
    path('tipos-atendimento/<int:pk>/editar/', views.tipo_atendimento_edit, name='tipo_atendimento_edit'),
    path('tipos-atendimento/<int:pk>/excluir/', views.tipo_atendimento_delete, name='tipo_atendimento_delete'),
    
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

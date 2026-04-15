from django.urls import path
from . import views

app_name = 'medical_records'

urlpatterns = [
    path('atendimento/', views.atendimento_list, name='atendimento_list'),
    path('animal/<int:pet_id>/', views.animal_records, name='animal_records'),
    
    # API endpoints para salvar registros
    path('api/<int:pet_id>/atendimento/', views.salvar_atendimento, name='salvar_atendimento'),
    path('api/<int:pet_id>/peso/', views.salvar_peso, name='salvar_peso'),
    path('api/<int:pet_id>/patologia/', views.salvar_patologia, name='salvar_patologia'),
    path('api/<int:pet_id>/documento/', views.salvar_documento, name='salvar_documento'),
    path('api/<int:pet_id>/exame/', views.salvar_exame, name='salvar_exame'),
    path('api/<int:pet_id>/fotos/', views.salvar_fotos, name='salvar_fotos'),
    path('api/<int:pet_id>/vacina/', views.salvar_vacina, name='salvar_vacina'),
    path('api/<int:pet_id>/receita/', views.salvar_receita, name='salvar_receita'),
    path('api/<int:pet_id>/observacao/', views.salvar_observacao, name='salvar_observacao'),
    path('api/<int:pet_id>/video/', views.salvar_video, name='salvar_video'),
    path('api/<int:pet_id>/internacao/', views.salvar_internacao, name='salvar_internacao'),
    
    # API endpoints para buscar registros individuais
    path('api/<int:pet_id>/<str:tipo>/<int:registro_id>/detalhes/', views.obter_registro, name='obter_registro'),
    
    # API endpoint para deletar registros
    path('api/<int:pet_id>/<str:tipo>/<int:registro_id>/', views.deletar_registro, name='deletar_registro'),
    
    # API endpoint para listar registros da timeline
    path('api/<int:pet_id>/timeline/', views.listar_timeline, name='listar_timeline'),

    # Impressão PDF de documento
    path('imprimir-documento/', views.imprimir_documento_view, name='imprimir_documento'),
    # Servir PDF temporário com nome de arquivo no path (para Chrome usar nome correto)
    path('pdf/<str:token>/<path:filename>', views.servir_pdf_temp_view, name='servir_pdf_temp'),
]


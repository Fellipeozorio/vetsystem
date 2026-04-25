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
    path('api/<int:pet_id>/exame-atributos/<int:exame_id>/', views.obter_atributos_exame, name='obter_atributos_exame'),
    path('api/<int:pet_id>/fotos/', views.salvar_fotos, name='salvar_fotos'),
    path('api/<int:pet_id>/vacina/', views.salvar_vacina, name='salvar_vacina'),
    path('api/<int:pet_id>/receita/', views.salvar_receita, name='salvar_receita'),
    path('api/<int:pet_id>/observacao/', views.salvar_observacao, name='salvar_observacao'),
    path('api/<int:pet_id>/video/', views.salvar_video, name='salvar_video'),
    path('api/<int:pet_id>/internacao/', views.salvar_internacao, name='salvar_internacao'),
    
    # API endpoints para buscar registros individuais
    path('api/<int:pet_id>/<str:tipo>/<int:registro_id>/detalhes/', views.obter_registro, name='obter_registro'),
    
    # API endpoints para protocolos de vacina (devem vir ANTES da rota genérica deletar_registro)
    path('api/<int:pet_id>/vacinas-tipos/', views.listar_tipos_vacina, name='listar_tipos_vacina'),
    path('api/<int:pet_id>/vacinas-disponiveis/', views.listar_vacinas_disponiveis, name='listar_vacinas_disponiveis'),
    path('api/<int:pet_id>/protocolos-vacina/', views.listar_protocolos_vacina, name='listar_protocolos_vacina'),
    path('api/<int:pet_id>/protocolos-vacina/salvar/', views.salvar_protocolo_vacina, name='salvar_protocolo_vacina'),
    path('api/<int:pet_id>/protocolos-vacina/<int:protocolo_id>/', views.detalhe_protocolo_vacina, name='detalhe_protocolo_vacina'),
    path('api/<int:pet_id>/protocolos-vacina/<int:protocolo_id>/interromper/', views.interromper_protocolo_vacina, name='interromper_protocolo_vacina'),
    path('api/<int:pet_id>/protocolos-vacina/<int:protocolo_id>/retomar/', views.retomar_protocolo_vacina, name='retomar_protocolo_vacina'),
    path('api/<int:pet_id>/protocolos-vacina/<int:protocolo_id>/excluir/', views.deletar_protocolo_vacina, name='deletar_protocolo_vacina'),
    path('api/<int:pet_id>/dose-vacina/<int:dose_id>/', views.detalhe_dose_vacina, name='detalhe_dose_vacina'),
    path('api/<int:pet_id>/dose-vacina/<int:dose_id>/salvar/', views.salvar_dose_vacina, name='salvar_dose_vacina'),
    path('api/<int:pet_id>/dose-vacina/<int:dose_id>/excluir/', views.excluir_dose_vacina, name='excluir_dose_vacina'),

    # API endpoint para deletar registros (rota genérica — deve ficar APÓS as rotas específicas)
    path('api/<int:pet_id>/<str:tipo>/<int:registro_id>/', views.deletar_registro, name='deletar_registro'),
    
    # API endpoint para listar registros da timeline
    path('api/<int:pet_id>/timeline/', views.listar_timeline, name='listar_timeline'),

    # Impressão PDF de documento
    path('imprimir-documento/', views.imprimir_documento_view, name='imprimir_documento'),
    # Servir PDF temporário com nome de arquivo no path (para Chrome usar nome correto)
    path('pdf/<str:token>/<path:filename>', views.servir_pdf_temp_view, name='servir_pdf_temp'),
]


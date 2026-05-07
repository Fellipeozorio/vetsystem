from django.urls import path
from . import views

app_name = 'queries'

urlpatterns = [
    path('vacinacao/', views.vacinacao_view, name='vacinacao'),
    path('aniversarios/', views.aniversarios_view, name='aniversarios'),
    path('api/vacinacao/', views.api_vacinacao, name='api_vacinacao'),
    path('api/vacinacao/resumo/', views.api_vacinacao_resumo, name='api_vacinacao_resumo'),
    path('api/aniversarios/', views.api_aniversarios, name='api_aniversarios'),
]

from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('ponto-de-venda/', views.ponto_de_venda, name='ponto_de_venda'),
    path('minhas-vendas/', views.minhas_vendas, name='minhas_vendas'),
    path('consulta-vendas/', views.consulta_vendas, name='consulta_vendas'),
    path('pacotes-vendidos/', views.pacotes_vendidos, name='pacotes_vendidos'),
    path('lista-de-precos/', views.lista_de_precos, name='lista_de_precos'),
    path('ranking-de-precos/', views.ranking_de_precos, name='ranking_de_precos'),
    path('modelo-orcamento/', views.modelo_orcamento, name='modelo_orcamento'),
    path('modelo-demonstrativo/', views.modelo_demonstrativo, name='modelo_demonstrativo'),
    path('configuracoes/', views.configuracoes, name='configuracoes'),
]

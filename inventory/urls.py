from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    path('produtos/', views.produtos_servicos, name='produtos'),
    path('produtos/salvar/', views.produto_save, name='produto_save'),
    path('produtos/<int:pk>/', views.produto_detail, name='produto_detail'),
    path('produtos/<int:pk>/deletar/', views.produto_delete, name='produto_delete'),

    path('marcas/', views.marcas, name='marcas'),
    path('marcas/salvar/', views.marca_save, name='marca_save'),
    path('marcas/<int:pk>/', views.marca_detail, name='marca_detail'),
    path('marcas/<int:pk>/deletar/', views.marca_delete, name='marca_delete'),
]

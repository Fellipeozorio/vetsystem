from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.client_list, name='list'),
    path('criar/', views.client_create_ajax, name='create_ajax'),
    path('<int:pk>/', views.client_detail, name='detail'),
    path('<int:pk>/atualizar/', views.client_update_ajax, name='update_ajax'),
    path('<int:pk>/excluir/', views.client_delete, name='delete'),
]

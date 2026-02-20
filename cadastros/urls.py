from django.urls import path
from . import views

app_name = 'cadastros'

urlpatterns = [
    # URLs genéricas para todos os cadastros
    path('<str:tipo>/', views.cadastro_list, name='list'),
    path('<str:tipo>/criar/', views.cadastro_create, name='create'),
    path('<str:tipo>/<int:pk>/', views.cadastro_detail, name='detail'),
    path('<str:tipo>/<int:pk>/editar/', views.cadastro_update, name='update'),
    path('<str:tipo>/<int:pk>/excluir/', views.cadastro_delete, name='delete'),
]

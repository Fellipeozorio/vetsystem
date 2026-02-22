from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('criar/', views.pet_create_ajax, name='create_ajax'),
    path('<int:pet_id>/detalhes/', views.pet_detail_ajax, name='detail_ajax'),
    path('<int:pet_id>/editar/', views.pet_edit_ajax, name='edit_ajax'),
    path('<int:pet_id>/excluir/', views.pet_delete_ajax, name='delete_ajax'),
    path('<int:pet_id>/transferir/', views.pet_transfer_ajax, name='transfer_ajax'),
]

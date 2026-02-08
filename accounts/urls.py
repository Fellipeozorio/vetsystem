from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('perfil/', views.profile_view, name='profile'),
    path('perfil/editar/', views.edit_profile_view, name='edit_profile'),
    path('alterar-senha/', views.change_password_view, name='change_password'),
    path('usuarios/', views.user_list_view, name='user_list'),
    path('usuarios/novo/', views.user_create_view, name='user_create'),
    path('usuarios/criar-ajax/', views.user_create_ajax, name='user_create_ajax'),
    path('usuarios/<int:user_id>/editar/', views.user_edit_view, name='user_edit'),
    path('usuarios/<int:user_id>/excluir/', views.user_delete_view, name='user_delete'),
    path('api/group-permissions/<int:group_id>/', views.get_group_permissions, name='get_group_permissions'),
]

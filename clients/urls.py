from django.urls import path
from .views import ClientListView, ClientDetailView, ClientCreateView, ClientUpdateView

app_name = 'clients'

urlpatterns = [
    path('', ClientListView.as_view(), name='list'),
    path('novo/', ClientCreateView.as_view(), name='create'),
    path('<int:pk>/', ClientDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', ClientUpdateView.as_view(), name='update'),
]

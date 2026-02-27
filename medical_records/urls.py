from django.urls import path
from . import views

app_name = 'medical_records'

urlpatterns = [
    path('atendimento/', views.atendimento_list, name='atendimento_list'),
    path('animal/<int:pet_id>/', views.animal_records, name='animal_records'),
]

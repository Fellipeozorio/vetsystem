# Views for clients app
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Client


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'clients/list.html'
    context_object_name = 'clients'
    paginate_by = 20
    
    def get_queryset(self):
        return Client.objects.all().order_by('-criado_em')


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = 'clients/detail.html'
    context_object_name = 'client'


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    template_name = 'clients/form.html'
    fields = ['person_type', 'nome_completo', 'cpf', 'rg', 'cnpj', 'razao_social', 
              'nacionalidade', 'sexo', 'celular', 'email', 'cep', 'endereco', 
              'numero', 'bairro', 'cidade', 'estado']
    success_url = reverse_lazy('clients:list')


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    template_name = 'clients/form.html'
    fields = ['person_type', 'nome_completo', 'cpf', 'rg', 'cnpj', 'razao_social',
              'nacionalidade', 'sexo', 'celular', 'email', 'cep', 'endereco',
              'numero', 'bairro', 'cidade', 'estado']
    success_url = reverse_lazy('clients:list')



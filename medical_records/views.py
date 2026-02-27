from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from patients.models import Pet
from clients.models import Client
from cadastros.models import Especie, Raca, Pelagem


@login_required
def atendimento_list(request):
    """Lista de clientes para atendimento clínico."""
    # Busca
    search = request.GET.get('search', '').strip()
    
    # Filtros
    tipo_filter = request.GET.get('tipo', '')
    
    # Query inicial
    clients = Client.objects.all()
    
    # Dicionário de filtros ativos
    active_filters = {}
    
    # Filtros avançados
    if request.GET.get('filter_nome'):
        nome = request.GET.get('filter_nome')
        clients = clients.filter(nome_completo__icontains=nome)
        active_filters['nome'] = nome
    
    if request.GET.get('filter_codigo'):
        codigo = request.GET.get('filter_codigo')
        clients = clients.filter(codigo__icontains=codigo)
        active_filters['codigo'] = codigo
    
    if request.GET.get('filter_tipo'):
        tipo = request.GET.get('filter_tipo')
        clients = clients.filter(tipo=tipo)
        active_filters['tipo'] = tipo
    
    if request.GET.get('filter_sexo'):
        sexo = request.GET.get('filter_sexo')
        clients = clients.filter(sexo=sexo)
        active_filters['sexo'] = sexo
    
    if request.GET.get('filter_cpf'):
        cpf = request.GET.get('filter_cpf')
        clients = clients.filter(cpf__icontains=cpf)
        active_filters['cpf'] = cpf
    
    if request.GET.get('filter_ativo'):
        ativo = request.GET.get('filter_ativo')
        if ativo.lower() == 'true':
            clients = clients.filter(ativo=True)
            active_filters['ativo'] = 'true'
        elif ativo.lower() == 'false':
            clients = clients.filter(ativo=False)
            active_filters['ativo'] = 'false'
    
    # Filtros de Animal
    if request.GET.get('filter_pet_nome'):
        pet_nome = request.GET.get('filter_pet_nome')
        clients = clients.filter(pets__nome__icontains=pet_nome).distinct()
        active_filters['pet_nome'] = pet_nome
    
    if request.GET.get('filter_pet_sexo'):
        pet_sexo = request.GET.get('filter_pet_sexo')
        clients = clients.filter(pets__sexo=pet_sexo).distinct()
        active_filters['pet_sexo'] = pet_sexo
    
    if request.GET.get('filter_pet_especie'):
        pet_especie = request.GET.get('filter_pet_especie')
        clients = clients.filter(pets__raca__especie_id=pet_especie).distinct()
        active_filters['pet_especie'] = pet_especie
    
    if request.GET.get('filter_pet_raca'):
        pet_raca = request.GET.get('filter_pet_raca')
        clients = clients.filter(pets__raca_id=pet_raca).distinct()
        active_filters['pet_raca'] = pet_raca
    
    # Aplicar busca (nome, código, celular, email, CPF)
    if search:
        clients = clients.filter(
            Q(nome_completo__icontains=search) |
            Q(codigo__icontains=search) |
            Q(celular__icontains=search) |
            Q(email__icontains=search) |
            Q(cpf__icontains=search) |
            Q(cnpj__icontains=search)
        )
    
    # Aplicar filtro de tipo
    if tipo_filter:
        clients = clients.filter(tipo=tipo_filter)
    
    # Paginação
    paginator = Paginator(clients, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Buscar dados para filtros
    especies = Especie.objects.filter(ativo=True).order_by('nome')
    racas = Raca.objects.filter(ativo=True).order_by('nome')
    pelagens = Pelagem.objects.filter(ativo=True).order_by('nome')
    
    # Adicionar nomes de espécie e raça aos filtros ativos
    if 'pet_especie' in active_filters:
        try:
            especie_obj = Especie.objects.get(id=active_filters['pet_especie'])
            active_filters['pet_especie_nome'] = especie_obj.nome
        except Especie.DoesNotExist:
            active_filters['pet_especie_nome'] = 'Desconhecida'
    
    if 'pet_raca' in active_filters:
        try:
            raca_obj = Raca.objects.get(id=active_filters['pet_raca'])
            active_filters['pet_raca_nome'] = raca_obj.nome
        except Raca.DoesNotExist:
            active_filters['pet_raca_nome'] = 'Desconhecida'
    
    context = {
        'clients': page_obj,
        'search': search,
        'tipo_filter': tipo_filter,
        'active_filters': active_filters,
        'especies': especies,
        'racas': racas,
        'pelagens': pelagens,
    }
    
    return render(request, 'medical_records/atendimento_clinico_list.html', context)


@login_required
def animal_records(request, pet_id):
    """Página de prontuário do animal."""
    pet = get_object_or_404(Pet, id=pet_id)
    
    context = {
        'pet': pet,
        'cliente': pet.tutor,
    }
    
    return render(request, 'medical_records/animal_records.html', context)

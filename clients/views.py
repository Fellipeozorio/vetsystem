from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
import json

from .models import Client, ContatoAdicional


@login_required
def client_list(request):
    """Lista de clientes com busca e filtros."""
    # Busca
    search = request.GET.get('search', '').strip()
    
    # Filtros
    tipo_filter = request.GET.get('tipo', '')
    
    # Query inicial
    clients = Client.objects.all()
    
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
    
    context = {
        'clients': page_obj,
        'search': search,
        'tipo_filter': tipo_filter,
    }
    
    return render(request, 'clients/client_list.html', context)


@login_required
@require_http_methods(["POST"])
def client_create_ajax(request):
    """Criar cliente via AJAX."""
    try:
        # Parse dados do formulário
        tipo = request.POST.get('tipo')
        nome_completo = request.POST.get('nome_completo')
        
        # Validação básica
        if not nome_completo:
            return JsonResponse({'success': False, 'error': 'Nome completo é obrigatório'})
        
        # Criar cliente
        client = Client()
        client.tipo = tipo
        client.nome_completo = nome_completo
        
        # Campos Pessoa Física
        if tipo == 'PF':
            client.nacionalidade = request.POST.get('nacionalidade')
            client.sexo = request.POST.get('sexo')
            client.cpf = request.POST.get('cpf')
            client.rg = request.POST.get('rg')
            data_aniversario = request.POST.get('data_aniversario')
            if data_aniversario:
                client.data_aniversario = data_aniversario
            client.profissao = request.POST.get('profissao')
        
        # Campos Pessoa Jurídica
        elif tipo == 'PJ':
            client.cnpj = request.POST.get('cnpj')
            client.nacionalidade = request.POST.get('nacionalidade')
            client.regime_tributario = request.POST.get('regime_tributario')
            client.inscricao_estadual = request.POST.get('inscricao_estadual')
        
        # Campos comuns
        client.inscricao_municipal = request.POST.get('inscricao_municipal', '')
        client.como_conheceu = request.POST.get('como_conheceu', '')
        
        # Contatos
        client.celular = request.POST.get('celular')
        client.celular_whatsapp = request.POST.get('celular_whatsapp') == 'true'
        client.email = request.POST.get('email', '')
        
        # Endereço
        client.cep = request.POST.get('cep', '')
        client.endereco = request.POST.get('endereco', '')
        client.numero = request.POST.get('numero', '')
        client.complemento = request.POST.get('complemento', '')
        client.bairro = request.POST.get('bairro', '')
        client.cidade = request.POST.get('cidade', '')
        client.estado = request.POST.get('estado', '')
        client.ponto_referencia = request.POST.get('ponto_referencia', '')
        
        # Informações complementares
        client.tags = request.POST.get('tags', '')
        client.observacoes = request.POST.get('observacoes', '')
        
        # Preferências de privacidade
        client.aceita_email = request.POST.get('aceita_email') == 'true'
        client.aceita_sms = request.POST.get('aceita_sms') == 'true'
        client.aceita_whatsapp = request.POST.get('aceita_whatsapp') == 'true'
        client.aceita_campanha_sms = request.POST.get('aceita_campanha_sms') == 'true'
        
        client.save()
        
        # Processar contatos adicionais (se houver)
        contatos_json = request.POST.get('contatos_adicionais', '[]')
        try:
            contatos = json.loads(contatos_json)
            for contato in contatos:
                ContatoAdicional.objects.create(
                    cliente=client,
                    tipo=contato.get('tipo'),
                    valor=contato.get('valor'),
                    whatsapp=contato.get('whatsapp', False),
                    observacoes=contato.get('observacoes', '')
                )
        except json.JSONDecodeError:
            pass
        
        return JsonResponse({
            'success': True,
            'message': f'Cliente {client.nome_completo} criado com sucesso! Código: {client.codigo}',
            'client_id': client.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def client_delete(request, pk):
    """Excluir cliente."""
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        nome = client.nome_completo
        client.delete()
        # Redirecionar com mensagem
        return redirect('clients:list')
    
    return redirect('clients:list')

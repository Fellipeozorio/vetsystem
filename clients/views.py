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
@require_http_methods(["GET"])
def check_duplicate(request):
    """Verificar se CPF ou CNPJ já está cadastrado."""
    document_type = request.GET.get('type', '').lower()
    document_value = request.GET.get('value', '').strip()
    
    if not document_type or not document_value:
        return JsonResponse({'exists': False})
    
    exists = False
    message = ''
    
    # Buscar todos os clientes e comparar removendo formatação
    if document_type == 'cpf':
        from django.db.models import Q
        import re
        # Buscar clientes que tenham CPF
        clients = Client.objects.filter(cpf__isnull=False).exclude(cpf='')
        for client in clients:
            # Remover formatação do CPF no banco
            cpf_sem_formatacao = re.sub(r'\D', '', client.cpf or '')
            if cpf_sem_formatacao == document_value:
                exists = True
                break
        message = 'Já existe um cliente cadastrado com este CPF' if exists else ''
    elif document_type == 'cnpj':
        from django.db.models import Q
        import re
        # Buscar clientes que tenham CNPJ
        clients = Client.objects.filter(cnpj__isnull=False).exclude(cnpj='')
        for client in clients:
            # Remover formatação do CNPJ no banco
            cnpj_sem_formatacao = re.sub(r'\D', '', client.cnpj or '')
            if cnpj_sem_formatacao == document_value:
                exists = True
                break
        message = 'Já existe um cliente cadastrado com este CNPJ' if exists else ''
    
    return JsonResponse({
        'exists': exists,
        'message': message
    })


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
        
        # Validar CPF duplicado para Pessoa Física
        if tipo == 'PF':
            cpf = request.POST.get('cpf', '').strip()
            if cpf and Client.objects.filter(cpf=cpf).exists():
                return JsonResponse({'success': False, 'error': 'Já existe um cliente cadastrado com este CPF'})
        
        # Validar CNPJ duplicado para Pessoa Jurídica
        if tipo == 'PJ':
            cnpj = request.POST.get('cnpj', '').strip()
            if cnpj and Client.objects.filter(cnpj=cnpj).exists():
                return JsonResponse({'success': False, 'error': 'Já existe um cliente cadastrado com este CNPJ'})
        
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


@login_required
def client_detail(request, pk):
    """Detalhes do cliente."""
    client = get_object_or_404(Client, pk=pk)
    pets = client.pets.all()
    contatos_adicionais = client.contatos_adicionais.all()
    
    context = {
        'client': client,
        'pets': pets,
        'contatos_adicionais': contatos_adicionais,
    }
    
    return render(request, 'clients/client_detail.html', context)


@login_required
@require_http_methods(["POST"])
def client_update_ajax(request, pk):
    """Atualizar cliente via AJAX."""
    try:
        client = get_object_or_404(Client, pk=pk)
        
        # Parse dados do formulário
        tipo = request.POST.get('tipo')
        nome_completo = request.POST.get('nome_completo') or request.POST.get('nome_completo_pj')
        
        # Validação básica
        if not nome_completo:
            return JsonResponse({'success': False, 'error': 'Nome completo é obrigatório'})
        
        # Validar CPF duplicado para Pessoa Física (exceto próprio cliente)
        if tipo == 'PF':
            cpf = request.POST.get('cpf', '').strip()
            if cpf and Client.objects.filter(cpf=cpf).exclude(id=client.id).exists():
                return JsonResponse({'success': False, 'error': 'Já existe outro cliente cadastrado com este CPF'})
        
        # Validar CNPJ duplicado para Pessoa Jurídica (exceto próprio cliente)
        if tipo == 'PJ':
            cnpj = request.POST.get('cnpj', '').strip()
            if cnpj and Client.objects.filter(cnpj=cnpj).exclude(id=client.id).exists():
                return JsonResponse({'success': False, 'error': 'Já existe outro cliente cadastrado com este CNPJ'})
        
        # Atualizar tipo e nome
        tipo_mudou = client.tipo != tipo
        client.tipo = tipo
        client.nome_completo = nome_completo
        
        # Apenas limpar e atualizar campos específicos se o tipo mudou
        if tipo_mudou:
            if tipo == 'PF':
                # Limpar campos PJ
                client.cnpj = ''
                client.regime_tributario = ''
                client.inscricao_estadual = ''
            elif tipo == 'PJ':
                # Limpar campos PF
                client.cpf = ''
                client.rg = ''
                client.sexo = ''
                client.data_aniversario = None
                client.profissao = ''
        
        # Atualizar campos específicos do tipo (se fornecidos no POST)
        if tipo == 'PF':
            # Atualizar campos PF (se fornecidos)
            if 'nacionalidade' in request.POST:
                client.nacionalidade = request.POST.get('nacionalidade', '')
            if 'sexo' in request.POST:
                client.sexo = request.POST.get('sexo', '')
            if 'cpf' in request.POST:
                client.cpf = request.POST.get('cpf', '')
            if 'rg' in request.POST:
                client.rg = request.POST.get('rg', '')
            if 'data_aniversario' in request.POST:
                data_aniversario = request.POST.get('data_aniversario', '')
                client.data_aniversario = data_aniversario if data_aniversario else None
            if 'profissao' in request.POST:
                client.profissao = request.POST.get('profissao', '')
        
        elif tipo == 'PJ':
            # Atualizar campos PJ (se fornecidos)
            if 'cnpj' in request.POST:
                client.cnpj = request.POST.get('cnpj', '')
            if 'regime_tributario' in request.POST:
                client.regime_tributario = request.POST.get('regime_tributario', '')
            if 'inscricao_estadual' in request.POST:
                client.inscricao_estadual = request.POST.get('inscricao_estadual', '')
            if 'nacionalidade' in request.POST:
                client.nacionalidade = request.POST.get('nacionalidade', '')
        
        # Campos comuns
        client.inscricao_municipal = request.POST.get('inscricao_municipal', '')
        client.como_conheceu = request.POST.get('como_conheceu', '')
        
        # Contatos (se fornecidos)
        celular = request.POST.get('celular')
        if celular:
            client.celular = celular
            whatsapp_value = request.POST.get('celular_whatsapp', '0')
            client.celular_whatsapp = whatsapp_value == '1' or whatsapp_value == 'true'
        
        email = request.POST.get('email')
        if email is not None:
            client.email = email
        
        # Endereço (se fornecido)
        if 'cep' in request.POST:
            client.cep = request.POST.get('cep', '')
            client.endereco = request.POST.get('endereco', '')
            client.numero = request.POST.get('numero', '')
            client.complemento = request.POST.get('complemento', '')
            client.bairro = request.POST.get('bairro', '')
            client.cidade = request.POST.get('cidade', '')
            client.estado = request.POST.get('estado', '')
            client.ponto_referencia = request.POST.get('ponto_referencia', '')
        
        # Informações complementares (se fornecidas)
        if 'tags' in request.POST:
            client.tags = request.POST.get('tags', '')
        if 'observacoes' in request.POST:
            client.observacoes = request.POST.get('observacoes', '')
        
        # Preferências de privacidade
        if 'aceita_email' in request.POST:
            client.aceita_email = 'aceita_email' in request.POST
        if 'aceita_sms' in request.POST:
            client.aceita_sms = 'aceita_sms' in request.POST
        if 'aceita_whatsapp' in request.POST:
            client.aceita_whatsapp = 'aceita_whatsapp' in request.POST
        if 'aceita_campanha_sms' in request.POST:
            client.aceita_campanha_sms = 'aceita_campanha_sms' in request.POST
        
        client.save()
        
        # Atualizar contatos adicionais (se fornecidos)
        if 'contatos_adicionais_tipo[]' in request.POST:
            # Remover contatos existentes
            client.contatos_adicionais.all().delete()
            
            # Adicionar novos contatos
            tipos = request.POST.getlist('contatos_adicionais_tipo[]')
            valores = request.POST.getlist('contatos_adicionais_valor[]')
            obs_list = request.POST.getlist('contatos_adicionais_obs[]')
            whatsapp_list = request.POST.getlist('contatos_adicionais_whatsapp[]')
            
            for i, (tipo_contato, valor) in enumerate(zip(tipos, valores)):
                if valor.strip():  # Só criar se tiver valor
                    ContatoAdicional.objects.create(
                        cliente=client,
                        tipo=tipo_contato,
                        valor=valor,
                        whatsapp='on' in whatsapp_list if i < len(whatsapp_list) else False,
                        observacoes=obs_list[i] if i < len(obs_list) else ''
                    )
        
        return JsonResponse({
            'success': True,
            'message': f'Cliente {client.nome_completo} atualizado com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


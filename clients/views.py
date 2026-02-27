from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
import json

from .models import Client, ContatoAdicional
from cadastros.models import OrigemCliente, Especie, Raca, Pelagem


@login_required
def client_list(request):
    """Lista de clientes com busca e filtros."""
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
    
    # Buscar origens ativas
    origens_cliente = OrigemCliente.objects.filter(ativo=True).order_by('nome')
    
    # Buscar dados para cadastro de animais
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
        'origens_cliente': origens_cliente,
        'especies': especies,
        'racas': racas,
        'pelagens': pelagens,
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
        como_conheceu_id = request.POST.get('como_conheceu', '')
        client.como_conheceu_id = como_conheceu_id if como_conheceu_id else None
        
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
    
    # Buscar origens ativas
    origens_cliente = OrigemCliente.objects.filter(ativo=True).order_by('nome')
    
    # Buscar dados para cadastro de animais
    especies = Especie.objects.filter(ativo=True).order_by('nome')
    racas = Raca.objects.filter(ativo=True).order_by('nome')
    pelagens = Pelagem.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'client': client,
        'pets': pets,
        'contatos_adicionais': contatos_adicionais,
        'origens_cliente': origens_cliente,
        'especies': especies,
        'racas': racas,
        'pelagens': pelagens,
    }
    
    return render(request, 'clients/client_detail.html', context)


@login_required
@require_http_methods(["POST"])
def client_update_ajax(request, pk):
    """Atualizar cliente via AJAX."""
    try:
        client = get_object_or_404(Client, pk=pk)
        
        # Debug: Log dos dados recebidos
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"=== UPDATE CLIENT {pk} ===")
        logger.info(f"POST data: {dict(request.POST)}")
        
        # Identificar qual formulário está sendo enviado
        tipo = request.POST.get('tipo')
        
        # Determinar qual campo de nome usar baseado no tipo
        if tipo == 'PJ':
            nome_completo = request.POST.get('nome_completo_pj', '')
        else:
            nome_completo = request.POST.get('nome_completo', '')
        
        logger.info(f"tipo: {tipo}, nome_completo (PF): {request.POST.get('nome_completo')}, nome_completo_pj (PJ): {request.POST.get('nome_completo_pj')}")
        logger.info(f"Usando nome_completo: {nome_completo}")
        
        # Se tipo ou nome_completo estão presentes, é o formulário de informações
        # Nesse caso, validar campos obrigatórios
        if tipo is not None or nome_completo:
            # Validação de informações básicas
            if not nome_completo:
                return JsonResponse({'success': False, 'error': 'Nome completo é obrigatório'})
            
            # Se tipo não foi enviado, usar o tipo atual do cliente
            if tipo is None:
                tipo = client.tipo
            
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
            logger.info(f"Atualizando nome_completo para: {nome_completo}")
            
            # Apenas limpar e atualizar campos específicos se o tipo mudou
            if tipo_mudou:
                if tipo == 'PF':
                    # Limpar campos PJ (usar None para campos unique)
                    client.cnpj = None
                    client.regime_tributario = ''
                    client.inscricao_estadual = ''
                elif tipo == 'PJ':
                    # Limpar campos PF (usar None para campos unique)
                    client.cpf = None
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
                    cpf_value = request.POST.get('cpf', '').strip()
                    client.cpf = cpf_value if cpf_value else None
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
                    cnpj_value = request.POST.get('cnpj', '').strip()
                    client.cnpj = cnpj_value if cnpj_value else None
                if 'regime_tributario' in request.POST:
                    client.regime_tributario = request.POST.get('regime_tributario', '')
                if 'inscricao_estadual' in request.POST:
                    client.inscricao_estadual = request.POST.get('inscricao_estadual', '')
                if 'nacionalidade' in request.POST:
                    client.nacionalidade = request.POST.get('nacionalidade', '')
            
            # Campos comuns (se fornecidos)
            if 'inscricao_municipal' in request.POST:
                client.inscricao_municipal = request.POST.get('inscricao_municipal', '')
            if 'como_conheceu' in request.POST:
                como_conheceu_id = request.POST.get('como_conheceu', '')
                client.como_conheceu_id = como_conheceu_id if como_conheceu_id else None
        
        # Contatos (se fornecidos)
        if 'celular' in request.POST:
            celular = request.POST.get('celular')
            client.celular = celular
            whatsapp_value = request.POST.get('celular_whatsapp', '0')
            client.celular_whatsapp = whatsapp_value == '1' or whatsapp_value == 'true'
            client.obs_celular = request.POST.get('obs_celular', '')
        
        if 'email' in request.POST:
            email = request.POST.get('email')
            client.email = email
            client.obs_email = request.POST.get('obs_email', '')
        
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
        # Processar APENAS se for o formulário de privacidade específico
        if request.POST.get('form_type') == 'privacy':
            # Checkboxes não enviados = False (desmarcados)
            client.aceita_email = 'aceita_email' in request.POST
            client.aceita_sms = 'aceita_sms' in request.POST
            client.aceita_whatsapp = 'aceita_whatsapp' in request.POST
            client.aceita_campanha_sms = 'aceita_campanha_sms' in request.POST
            logger.info(f"Atualizando privacidade - email: {client.aceita_email}, sms: {client.aceita_sms}, whatsapp: {client.aceita_whatsapp}, campanha_sms: {client.aceita_campanha_sms}")
        
        logger.info(f"Salvando cliente - tipo: {client.tipo}, nome_completo: {client.nome_completo}")
        client.save()
        logger.info(f"Cliente salvo com sucesso - ID: {client.id}")
        
        # Atualizar contatos adicionais (se flag estiver presente)
        if 'update_contatos_adicionais' in request.POST:
            logger.info("Processando contatos adicionais")
            # Sempre remover contatos existentes quando formulário é submetido
            deleted_count = client.contatos_adicionais.count()
            client.contatos_adicionais.all().delete()
            logger.info(f"{deleted_count} contatos anteriores removidos")
            
            # Adicionar novos contatos (se houver)
            tipos = request.POST.getlist('contatos_adicionais_tipo[]')
            valores = request.POST.getlist('contatos_adicionais_valor[]')
            obs_list = request.POST.getlist('contatos_adicionais_obs[]')
            whatsapp_list = request.POST.getlist('contatos_adicionais_whatsapp_processed[]')
            
            logger.info(f"Tipos: {tipos}")
            logger.info(f"Valores: {valores}")
            logger.info(f"Observações: {obs_list}")
            logger.info(f"WhatsApp processed: {whatsapp_list}")
            
            for i, (tipo_contato, valor) in enumerate(zip(tipos, valores)):
                if valor.strip():  # Só criar se tiver valor
                    # Usar a lista processada de WhatsApp (0 ou 1)
                    tem_whatsapp = whatsapp_list[i] == '1' if i < len(whatsapp_list) else False
                    
                    contato = ContatoAdicional.objects.create(
                        cliente=client,
                        tipo=tipo_contato,
                        valor=valor,
                        whatsapp=tem_whatsapp,
                        observacoes=obs_list[i] if i < len(obs_list) else ''
                    )
                    logger.info(f"Contato adicional criado: {contato.tipo} - {contato.valor} (WhatsApp: {contato.whatsapp})")
        
        return JsonResponse({
            'success': True,
            'message': f'Cliente {client.nome_completo} atualizado com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def client_list_api(request):
    """Retorna lista de clientes para select (API)."""
    try:
        clients = Client.objects.all().order_by('nome_completo')
        
        clientes_data = [{
            'id': client.id,
            'nome': client.nome_completo,
            'codigo': client.codigo
        } for client in clients]
        
        return JsonResponse({
            'success': True,
            'clientes': clientes_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


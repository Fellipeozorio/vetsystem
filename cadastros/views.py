from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
import time
from .models import (
    Especie, Raca, Pelagem, FilaAtendimento, Patologia,
    TipoAtendimento, Vacina, Exame, AtributoExame,
    ReferenciaExame, ModeloReceita, ModeloDocumento, OrigemCliente,
    ProtocoloVacina, DadosUnidade
)


# Mapeamento de modelos para facilitar a navegação
MODEL_MAP = {
    'especies': Especie,
    'racas': Raca,
    'pelagens': Pelagem,
    'filas-atendimento': FilaAtendimento,
    'patologias': Patologia,
    'tipos-atendimento': TipoAtendimento,
    'vacinas': Vacina,
    'exames': Exame,
    'atributos-exames': AtributoExame,
    'referencias-exames': ReferenciaExame,
    'origens-cliente': OrigemCliente,
}

MENU_LABELS = {
    'especies': 'Espécies',
    'racas': 'Raças',
    'pelagens': 'Pelagens',
    'filas-atendimento': 'Filas de Atendimento',
    'patologias': 'Patologias',
    'tipos-atendimento': 'Tipos de Atendimento',
    'vacinas': 'Vacinas',
    'exames': 'Exames',
    'atributos-exames': 'Atributos de Exames',
    'referencias-exames': 'Referências de Exames',
    'origens-cliente': 'Origem dos Clientes',
}


@login_required
def cadastro_list(request, tipo):
    """View genérica para listar cadastros"""
    if tipo not in MODEL_MAP:
        messages.error(request, 'Tipo de cadastro inválido.')
        return redirect('dashboard')
    
    model = MODEL_MAP[tipo]
    query = request.GET.get('q', '')
    
    # Buscar registros apenas na primeira coluna (nome)
    if query:
        items = model.objects.filter(nome__icontains=query)
    else:
        items = model.objects.all()
    
    # Aplicar filtros avançados
    active_filters = {}
    for key, value in request.GET.items():
        if key.startswith('filter_') and value:
            field_name = key.replace('filter_', '')
            # Verificar se o campo existe no modelo
            if hasattr(model, field_name):
                try:
                    field = model._meta.get_field(field_name)
                    field_type = field.get_internal_type()
                    
                    # Tratamento especial para campo booleano 'ativo'
                    if field_name == 'ativo':
                        if value.lower() in ['true', '1', 'sim']:
                            items = items.filter(ativo=True)
                            active_filters[field_name] = 'True'
                        elif value.lower() in ['false', '0', 'não', 'nao']:
                            items = items.filter(ativo=False)
                            active_filters[field_name] = 'False'
                    # Tratamento para ForeignKey
                    elif field_type == 'ForeignKey':
                        items = items.filter(**{field_name: value})
                        active_filters[field_name] = value
                    # Tratamento para campos numéricos
                    elif field_type in ['IntegerField', 'PositiveIntegerField', 'DecimalField', 'FloatField']:
                        items = items.filter(**{field_name: value})
                        active_filters[field_name] = value
                    # Tratamento padrão para texto (icontains)
                    else:
                        filter_key = f'{field_name}__icontains'
                        items = items.filter(**{filter_key: value})
                        active_filters[field_name] = value
                except Exception:
                    # Se houver erro ao obter o campo, tenta filtro padrão
                    filter_key = f'{field_name}__icontains'
                    items = items.filter(**{filter_key: value})
                    active_filters[field_name] = value
    
    # Paginação
    paginator = Paginator(items, 20)  # 20 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obter campos do modelo para o filtro avançado
    # Incluir todos os campos visíveis nas colunas da lista
    model_fields = []
    for field in model._meta.fields:
        field_type = field.get_internal_type()
        # Excluir campos que não devem aparecer nos filtros
        excluded_fields = ['id', 'ativo', 'nome']
        # Para patologias, também excluir os campos descricao e codigo
        if tipo == 'patologias' and field.name in ['descricao', 'codigo']:
            continue
        
        if field.name not in excluded_fields:
            if field_type in ['CharField', 'TextField', 'IntegerField', 'PositiveIntegerField']:
                model_fields.append({
                    'name': field.name,
                    'verbose_name': field.verbose_name or field.name.replace('_', ' ').title(),
                    'type': 'text'
                })
            elif field_type == 'ForeignKey':
                model_fields.append({
                    'name': field.name,
                    'verbose_name': field.verbose_name or field.name.replace('_', ' ').title(),
                    'type': 'foreignkey',
                    'related_model': field.related_model.__name__.lower()
                })
    
    context = {
        'tipo': tipo,
        'label': MENU_LABELS.get(tipo, tipo),
        'page_obj': page_obj,
        'query': query,
        'active_filters': active_filters,
        'model_fields': model_fields,
    }
    
    # Adicionar dados relacionados ao contexto
    # Sempre adicionar espécies (usado em raças e filtro avançado)
    context['especies'] = Especie.objects.filter(ativo=True)
    
    # Definir template específico ou usar o base_list
    template_map = {
        'especies': 'cadastros/especies_list.html',
        'racas': 'cadastros/racas_list.html',
        'pelagens': 'cadastros/pelagens_list.html',
        'vacinas': 'cadastros/vacinas_list.html',
        'exames': 'cadastros/exames_list.html',
        'patologias': 'cadastros/patologias_list.html',
        'tipos-atendimento': 'cadastros/tipos-atendimento_list.html',
    }
    
    template = template_map.get(tipo, 'cadastros/base_list.html')
    
    return render(request, template, context)


@login_required
def cadastro_create(request, tipo):
    """View genérica para criar cadastro"""
    if tipo not in MODEL_MAP:
        return JsonResponse({'success': False, 'error': 'Tipo inválido'})
    
    if request.method == 'POST':
        model = MODEL_MAP[tipo]
        try:
            data = {'nome': request.POST.get('nome')}
            
            # Campos específicos por modelo
            if tipo == 'racas':
                especie_id = request.POST.get('especie')
                if especie_id:
                    data['especie_id'] = especie_id
            elif tipo == 'patologias':
                data['codigo'] = request.POST.get('codigo', '')
                data['descricao'] = request.POST.get('descricao', '')
            elif tipo == 'tipos-atendimento':
                data['duracao_padrao'] = request.POST.get('duracao_padrao', 30)
            elif tipo == 'vacinas':
                data['tipo'] = request.POST.get('tipo', 'vacinas')
                # Processar laboratórios JSON
                laboratorios_json = request.POST.get('laboratorios_json', '')
                if laboratorios_json:
                    data['laboratorios'] = laboratorios_json
            elif tipo in ['filas-atendimento', 'exames']:
                data['descricao'] = request.POST.get('descricao', '')
            
            # Adicionar campo ativo se existir
            if hasattr(model, 'ativo'):
                ativo_value = request.POST.get('ativo', '')
                # Checkbox envia 'on' quando marcado, vazio quando desmarcado
                data['ativo'] = ativo_value in ['on', 'true', 'True', '1']
            
            obj = model.objects.create(**data)
            return JsonResponse({
                'success': True,
                'message': f'{MENU_LABELS.get(tipo, "Registro")} criado com sucesso!',
                'id': obj.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


@login_required
def cadastro_detail(request, tipo, pk):
    """View genérica para obter detalhes de um cadastro"""
    if tipo not in MODEL_MAP:
        return JsonResponse({'success': False, 'error': 'Tipo inválido'})
    
    model = MODEL_MAP[tipo]
    obj = get_object_or_404(model, pk=pk)
    
    # Montar dados do objeto
    data = {
        'id': obj.id,
        'nome': obj.nome if hasattr(obj, 'nome') else '',
    }
    
    # Campos específicos por modelo
    if tipo == 'racas' and hasattr(obj, 'especie'):
        data['especie'] = obj.especie_id if obj.especie else None
    if hasattr(obj, 'codigo'):
        data['codigo'] = obj.codigo
    if hasattr(obj, 'descricao'):
        data['descricao'] = obj.descricao
    if hasattr(obj, 'duracao_padrao'):
        data['duracao_padrao'] = obj.duracao_padrao
    if hasattr(obj, 'tipo'):
        data['tipo'] = obj.tipo
    if hasattr(obj, 'laboratorios'):
        data['laboratorios'] = obj.laboratorios
    if hasattr(obj, 'conteudo'):
        data['conteudo'] = obj.conteudo
    if hasattr(obj, 'ativo'):
        data['ativo'] = obj.ativo
    
    return JsonResponse({'success': True, 'data': data})


@login_required
def cadastro_update(request, tipo, pk):
    """View genérica para atualizar cadastro"""
    if tipo not in MODEL_MAP:
        return JsonResponse({'success': False, 'error': 'Tipo inválido'})
    
    model = MODEL_MAP[tipo]
    obj = get_object_or_404(model, pk=pk)
    
    if request.method == 'POST':
        try:
            if hasattr(obj, 'nome'):
                obj.nome = request.POST.get('nome')
            
            # Campos específicos por modelo
            if tipo == 'racas' and hasattr(obj, 'especie'):
                especie_id = request.POST.get('especie')
                if especie_id:
                    obj.especie_id = especie_id
            elif tipo == 'patologias':
                obj.codigo = request.POST.get('codigo', '')
                obj.descricao = request.POST.get('descricao', '')
            elif tipo == 'tipos-atendimento':
                obj.duracao_padrao = request.POST.get('duracao_padrao', 30)
            elif tipo == 'vacinas':
                obj.tipo = request.POST.get('tipo', 'vacinas')
                # Processar laboratórios JSON
                laboratorios_json = request.POST.get('laboratorios_json', '')
                if laboratorios_json:
                    obj.laboratorios = laboratorios_json
            elif tipo in ['filas-atendimento', 'exames']:
                obj.descricao = request.POST.get('descricao', '')
            
            # Atualizar campo ativo se existir
            if hasattr(obj, 'ativo'):
                ativo_value = request.POST.get('ativo', '')
                # Checkbox envia 'on' quando marcado, vazio quando desmarcado
                obj.ativo = ativo_value in ['on', 'true', 'True', '1']
            
            obj.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{MENU_LABELS.get(tipo, "Registro")} atualizado com sucesso!'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


@login_required
def cadastro_delete(request, tipo, pk):
    """View genérica para deletar cadastro"""
    if tipo not in MODEL_MAP:
        return JsonResponse({'success': False, 'error': 'Tipo inválido'})
    
    model = MODEL_MAP[tipo]
    obj = get_object_or_404(model, pk=pk)
    
    if request.method == 'POST':
        try:
            obj.delete()
            return JsonResponse({
                'success': True,
                'message': f'{MENU_LABELS.get(tipo, "Registro")} excluído com sucesso!'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


# ==================== Views específicas para Tipos de Atendimento ====================

def _get_duration_options():
    """Gera lista de opções de duração formatadas"""
    # Minutos: 5, 10, 15, 20, 25, 30, 45
    minutes_list = [5, 10, 15, 20, 25, 30, 45]
    
    # Horas: 1h, 1h30, 2h, 2h30, ..., 12h
    hours_list = []
    for hour in range(1, 13):  # 1 a 12 horas
        hours_list.append(hour * 60)  # hora cheia
        if hour < 12:  # adicionar meia hora, exceto para 12h
            hours_list.append(hour * 60 + 30)
    
    all_durations = minutes_list + hours_list
    
    # Formatar as opções
    formatted_options = []
    for minutes in all_durations:
        if minutes < 60:
            label = f"{minutes} minutos"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                label = f"{hours} hora" if hours == 1 else f"{hours} horas"
            else:
                label = f"{hours} hora e {remaining_minutes} minutos" if hours == 1 else f"{hours} horas e {remaining_minutes} minutos"
        
        formatted_options.append({
            'value': minutes,
            'label': label
        })
    
    return formatted_options


@login_required
def tipos_atendimento_list(request):
    """Lista de tipos de atendimento com colunas customizadas"""
    query = request.GET.get('q', '')
    
    # Buscar registros
    if query:
        items = TipoAtendimento.objects.filter(nome__icontains=query)
    else:
        items = TipoAtendimento.objects.all()
    
    # Aplicar filtros avançados
    active_filters = {}
    
    # Filtro por nome
    if request.GET.get('filter_nome'):
        items = items.filter(nome__icontains=request.GET.get('filter_nome'))
        active_filters['nome'] = request.GET.get('filter_nome')
    
    # Filtro por código
    if request.GET.get('filter_codigo'):
        items = items.filter(codigo__icontains=request.GET.get('filter_codigo'))
        active_filters['codigo'] = request.GET.get('filter_codigo')
    
    # Filtro por fluxo da agenda
    if request.GET.get('filter_fluxo_agenda'):
        items = items.filter(fluxo_agenda=request.GET.get('filter_fluxo_agenda'))
        active_filters['fluxo_agenda'] = request.GET.get('filter_fluxo_agenda')
    
    # Filtro por alertas (mensagens automáticas)
    if request.GET.get('filter_mensagens_automaticas'):
        value = request.GET.get('filter_mensagens_automaticas')
        if value.lower() in ['true', '1', 'sim']:
            items = items.filter(mensagens_automaticas=True)
            active_filters['mensagens_automaticas'] = 'True'
        elif value.lower() in ['false', '0', 'não', 'nao']:
            items = items.filter(mensagens_automaticas=False)
            active_filters['mensagens_automaticas'] = 'False'
    
    # Filtro por status
    if request.GET.get('filter_ativo'):
        value = request.GET.get('filter_ativo')
        if value.lower() in ['true', '1', 'sim']:
            items = items.filter(ativo=True)
            active_filters['ativo'] = 'True'
        elif value.lower() in ['false', '0', 'não', 'nao']:
            items = items.filter(ativo=False)
            active_filters['ativo'] = 'False'
    
    # Ordenar por código e nome
    items = items.order_by('codigo', 'nome')
    
    # Paginação
    paginator = Paginator(items, 20)  # 20 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tipo': 'tipos-atendimento',
        'label': 'Tipos de Atendimento',
        'page_obj': page_obj,
        'query': query,
        'active_filters': active_filters,
    }
    
    return render(request, 'cadastros/tipos_atendimento_list.html', context)


@login_required
def tipo_atendimento_create(request):
    """Criar novo tipo de atendimento"""
    if request.method == 'POST':
        try:
            # Processar dados do formulário
            data = {
                'nome': request.POST.get('nome'),
                'duracao_padrao': int(request.POST.get('duracao_padrao', 30)),
                'fluxo_agenda': request.POST.get('fluxo_agenda', 'clinico'),
                'frequencia_recomendada': request.POST.get('frequencia_recomendada', 'nao_recorrente'),
                'modelo_atendimento': request.POST.get('modelo_atendimento', ''),
            }
            
            # Processar campos booleanos (radio buttons)
            data['ativo'] = request.POST.get('ativo', 'false') == 'true'
            data['mensagens_automaticas'] = request.POST.get('mensagens_automaticas', 'false') == 'true'
            
            # Criar objeto
            TipoAtendimento.objects.create(**data)
            
            messages.success(request, 'Tipo de atendimento criado com sucesso!')
            return redirect('cadastros:tipos_atendimento_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar tipo de atendimento: {str(e)}')
    
    context = {
        'duration_options': _get_duration_options(),
    }
    
    return render(request, 'cadastros/tipo_atendimento_form.html', context)


@login_required
def tipo_atendimento_edit(request, pk):
    """Editar tipo de atendimento existente"""
    obj = get_object_or_404(TipoAtendimento, pk=pk)
    
    if request.method == 'POST':
        try:
            # Atualizar dados
            obj.nome = request.POST.get('nome')
            obj.duracao_padrao = int(request.POST.get('duracao_padrao', 30))
            obj.fluxo_agenda = request.POST.get('fluxo_agenda', 'clinico')
            obj.frequencia_recomendada = request.POST.get('frequencia_recomendada', 'nao_recorrente')
            obj.modelo_atendimento = request.POST.get('modelo_atendimento', '')
            
            # Processar campos booleanos
            obj.ativo = request.POST.get('ativo', 'false') == 'true'
            obj.mensagens_automaticas = request.POST.get('mensagens_automaticas', 'false') == 'true'
            
            obj.save()
            
            messages.success(request, 'Tipo de atendimento atualizado com sucesso!')
            return redirect('cadastros:tipos_atendimento_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar tipo de atendimento: {str(e)}')
    
    context = {
        'object': obj,
        'duration_options': _get_duration_options(),
    }
    
    return render(request, 'cadastros/tipo_atendimento_form.html', context)


@login_required
def tipo_atendimento_delete(request, pk):
    """Excluir tipo de atendimento"""
    obj = get_object_or_404(TipoAtendimento, pk=pk)
    
    if request.method == 'POST':
        try:
            obj.delete()
            # Se for AJAX, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Tipo de atendimento excluído com sucesso!'
                })
            # Se for POST normal, redirecionar
            messages.success(request, f'Tipo de atendimento "{obj.nome}" excluído com sucesso!')
            return redirect('cadastros:tipos_atendimento_list')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            messages.error(request, f'Erro ao excluir tipo de atendimento: {str(e)}')
            return redirect('cadastros:tipos_atendimento_list')
    
    # GET não é mais suportado - redirecionar para a lista
    return redirect('cadastros:tipos_atendimento_list')


# ===== FILAS DE ATENDIMENTO =====
@login_required
def filas_atendimento_list(request):
    """Lista de filas de atendimento com colunas customizadas"""
    query = request.GET.get('q', '')
    
    # Buscar registros
    if query:
        items = FilaAtendimento.objects.filter(nome__icontains=query)
    else:
        items = FilaAtendimento.objects.all()
    
    # Aplicar filtros avançados
    active_filters = {}
    
    # Filtro por nome
    if request.GET.get('filter_nome'):
        items = items.filter(nome__icontains=request.GET.get('filter_nome'))
        active_filters['nome'] = request.GET.get('filter_nome')
    
    # Filtro por código
    if request.GET.get('filter_codigo'):
        items = items.filter(codigo__icontains=request.GET.get('filter_codigo'))
        active_filters['codigo'] = request.GET.get('filter_codigo')
    
    # Filtro por permanente
    if request.GET.get('filter_permanente'):
        value = request.GET.get('filter_permanente')
        if value.lower() in ['true', '1', 'sim']:
            items = items.filter(permanente=True)
            active_filters['permanente'] = 'Sim'
        elif value.lower() in ['false', '0', 'não', 'nao']:
            items = items.filter(permanente=False)
            active_filters['permanente'] = 'Não'
    
    # Filtro por usuário atribuído
    if request.GET.get('filter_atribuido_a'):
        user_id = request.GET.get('filter_atribuido_a')
        items = items.filter(atribuido_a_id=user_id)
        # Buscar o nome do usuário para exibir no filtro
        try:
            user = User.objects.get(id=user_id)
            active_filters['atribuido_a'] = user.get_full_name() or user.username
        except User.DoesNotExist:
            active_filters['atribuido_a'] = user_id
    
    # Filtro por status
    if request.GET.get('filter_ativo'):
        value = request.GET.get('filter_ativo')
        if value.lower() in ['true', '1', 'sim']:
            items = items.filter(ativo=True)
            active_filters['ativo'] = 'True'
        elif value.lower() in ['false', '0', 'não', 'nao']:
            items = items.filter(ativo=False)
            active_filters['ativo'] = 'False'
    
    # Ordenar por código e nome
    items = items.select_related('atribuido_a').order_by('codigo', 'nome')
    
    # Paginação
    paginator = Paginator(items, 20)  # 20 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Buscar veterinários para filtros (grupo Veterinário ou todos os usuários se não existir o grupo)
    try:
        grupo_vet = Group.objects.get(name='Veterinário')
        veterinarios = User.objects.filter(groups=grupo_vet, is_active=True).order_by('first_name', 'username')
    except Group.DoesNotExist:
        veterinarios = User.objects.filter(is_active=True).order_by('first_name', 'username')
    
    context = {
        'tipo': 'filas-atendimento',
        'label': 'Filas de Atendimento',
        'page_obj': page_obj,
        'query': query,
        'active_filters': active_filters,
        'veterinarios': veterinarios,
    }
    
    return render(request, 'cadastros/filas_atendimento_list.html', context)


@login_required
def fila_atendimento_create(request):
    """Criar nova fila de atendimento"""
    if request.method == 'POST':
        # Processar dados do formulário
        nome = request.POST.get('nome')
        permanente = request.POST.get('permanente', 'false') == 'true'
        ativo = request.POST.get('ativo', 'false') == 'true'
        
        # Atribuir veterinário se selecionado
        atribuido_a = None
        atribuido_a_id = request.POST.get('atribuido_a')
        if atribuido_a_id:
            try:
                atribuido_a = User.objects.get(id=int(atribuido_a_id))
            except (ValueError, User.DoesNotExist):
                pass
        
        # Tentar criar com retry em caso de conflito de código ou lock do banco
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                # Gerar código e salvar na mesma transação atômica
                with transaction.atomic():
                    # Gerar o próximo código com lock
                    existing_codes = FilaAtendimento.objects.select_for_update().exclude(
                        codigo__isnull=True
                    ).exclude(codigo='').values_list('codigo', flat=True)
                    
                    numeric_codes = []
                    for code in existing_codes:
                        try:
                            numeric_codes.append(int(code))
                        except (ValueError, TypeError):
                            pass
                    
                    if numeric_codes:
                        next_num = max(numeric_codes) + 1
                    else:
                        next_num = 1
                    
                    codigo = str(next_num).zfill(3)
                    
                    # Criar o objeto diretamente com todos os campos
                    fila = FilaAtendimento(
                        nome=nome,
                        codigo=codigo,
                        permanente=permanente,
                        ativo=ativo,
                        atribuido_a=atribuido_a
                    )
                    fila.save(force_insert=True)
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Fila de atendimento criada com sucesso!'
                    })
            except IntegrityError as e:
                # Se for erro de código duplicado ou nome duplicado, tentar novamente
                if ('codigo' in str(e).lower() or 'locked' in str(e).lower()) and attempt < max_attempts - 1:
                    # Aguardar um pouco antes de tentar novamente (backoff exponencial)
                    time.sleep(0.1 * (2 ** min(attempt, 3)))  # Max 0.8s
                    continue
                else:
                    # Se não for erro de código/lock ou esgotamos as tentativas
                    return JsonResponse({
                        'success': False,
                        'error': f'Erro ao criar fila de atendimento: {str(e)}'
                    })
            except Exception as e:
                # Para database locked, tentar novamente
                if ('locked' in str(e).lower() or 'lock' in str(e).lower()) and attempt < max_attempts - 1:
                    time.sleep(0.1 * (2 ** min(attempt, 3)))
                    continue
                return JsonResponse({
                    'success': False,
                    'error': f'Erro ao criar fila de atendimento: {str(e)}'
                })
        
        # Se chegou aqui, esgotou as tentativas
        return JsonResponse({
            'success': False,
            'error': 'Não foi possível criar a fila após várias tentativas. Tente novamente.'
        })
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


@login_required
def fila_atendimento_detail(request, pk):
    """API: Obter detalhes de uma fila de atendimento"""
    fila = get_object_or_404(FilaAtendimento, pk=pk)
    
    return JsonResponse({
        'success': True,
        'data': {
            'id': fila.id,
            'codigo': fila.codigo,
            'nome': fila.nome,
            'permanente': fila.permanente,
            'atribuido_a': fila.atribuido_a_id,
            'ativo': fila.ativo,
        }
    })


@login_required
def fila_atendimento_update(request, pk):
    """Atualizar fila de atendimento"""
    obj = get_object_or_404(FilaAtendimento, pk=pk)
    
    if request.method == 'POST':
        try:
            # Atualizar dados
            obj.nome = request.POST.get('nome')
            obj.permanente = request.POST.get('permanente', 'false') == 'true'
            obj.ativo = request.POST.get('ativo', 'false') == 'true'
            
            # Atribuir veterinário
            atribuido_a_id = request.POST.get('atribuido_a')
            if atribuido_a_id:
                obj.atribuido_a_id = int(atribuido_a_id)
            else:
                obj.atribuido_a = None
            
            obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Fila de atendimento atualizada com sucesso!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erro ao atualizar fila de atendimento: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


@login_required
def fila_atendimento_delete(request, pk):
    """Excluir fila de atendimento"""
    obj = get_object_or_404(FilaAtendimento, pk=pk)
    
    if request.method == 'POST':
        try:
            nome = obj.nome
            obj.delete()
            return JsonResponse({
                'success': True,
                'message': f'Fila "{nome}" excluída com sucesso!'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erro ao excluir fila de atendimento: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


# ===== API ENDPOINTS =====
@login_required
def api_tipos_atendimento_list(request):
    """API: Listar todos os tipos de atendimento (JSON)"""
    tipos = TipoAtendimento.objects.filter(ativo=True).values('id', 'nome', 'modelo_atendimento')
    return JsonResponse(list(tipos), safe=False)


@login_required
def api_tipo_atendimento_template(request, pk):
    """API: Obter template de um tipo de atendimento específico (JSON)"""
    tipo = get_object_or_404(TipoAtendimento, pk=pk)
    return JsonResponse({
        'id': tipo.id,
        'nome': tipo.nome,
        'modelo_atendimento': tipo.modelo_atendimento or ''
    })


# Views para Protocolos de Vacina
@login_required
def vacina_protocolos_list(request, vacina_id):
    """Listar protocolos de uma vacina"""
    vacina = get_object_or_404(Vacina, pk=vacina_id)
    protocolos = vacina.protocolos.all().order_by('nome')
    
    protocolos_data = []
    for protocolo in protocolos:
        protocolos_data.append({
            'id': protocolo.id,
            'nome': protocolo.nome,
            'especie': protocolo.especie_id,
            'especie_nome': protocolo.especie.nome,
            'aplicacao': protocolo.aplicacao,
            'aplicacao_display': protocolo.get_aplicacao_display(),
            'intervalo_dias': protocolo.intervalo_dias,
            'vem_apos': protocolo.vem_apos_id if protocolo.vem_apos else None,
            'vem_apos_nome': protocolo.vem_apos.nome if protocolo.vem_apos else None,
        })
    
    return JsonResponse({'success': True, 'protocolos': protocolos_data})


@login_required
def protocolo_create(request):
    """Criar protocolo de vacina"""
    print(f"protocolo_create chamado - Method: {request.method}")
    if request.method == 'POST':
        try:
            vacina_id = request.POST.get('vacina_id')
            print(f"vacina_id: {vacina_id}")
            vacina = get_object_or_404(Vacina, pk=vacina_id)
            
            nome = request.POST.get('nome')
            especie_id = request.POST.get('especie')
            aplicacao = request.POST.get('aplicacao')
            intervalo_dias = request.POST.get('intervalo_dias')
            vem_apos_id = request.POST.get('vem_apos')
            
            print(f"Dados recebidos: nome={nome}, especie={especie_id}, aplicacao={aplicacao}, intervalo={intervalo_dias}, vem_apos={vem_apos_id}")
            
            protocolo = ProtocoloVacina.objects.create(
                vacina=vacina,
                nome=nome,
                especie_id=especie_id,
                aplicacao=aplicacao,
                intervalo_dias=intervalo_dias,
                vem_apos_id=vem_apos_id if vem_apos_id else None
            )
            
            print(f"Protocolo criado com sucesso: ID={protocolo.id}")
            
            return JsonResponse({
                'success': True,
                'message': 'Protocolo criado com sucesso!',
                'id': protocolo.id
            })
        except Exception as e:
            print(f"Erro ao criar protocolo: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


@login_required
def protocolo_update(request, pk):
    """Atualizar protocolo de vacina"""
    protocolo = get_object_or_404(ProtocoloVacina, pk=pk)
    
    if request.method == 'POST':
        try:
            protocolo.nome = request.POST.get('nome')
            protocolo.especie_id = request.POST.get('especie')
            protocolo.aplicacao = request.POST.get('aplicacao')
            protocolo.intervalo_dias = request.POST.get('intervalo_dias')
            
            vem_apos_id = request.POST.get('vem_apos')
            protocolo.vem_apos_id = vem_apos_id if vem_apos_id else None
            
            protocolo.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Protocolo atualizado com sucesso!'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


@login_required
def protocolo_delete(request, pk):
    """Deletar protocolo de vacina"""
    protocolo = get_object_or_404(ProtocoloVacina, pk=pk)
    
    if request.method == 'POST':
        try:
            protocolo.delete()
            return JsonResponse({
                'success': True,
                'message': 'Protocolo excluído com sucesso!'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


@login_required
def dados_unidade_view(request):
    """
    View para visualizar/editar dados da unidade.
    Todos os usuários autenticados podem visualizar.
    Apenas staff/admin podem editar.
    """
    # Obter ou criar o registro único de dados da unidade
    dados_unidade, created = DadosUnidade.objects.get_or_create(
        pk=1,
        defaults={
            'nome_empreendimento': '',
            'cnpj': '00.000.000/0000-00',
            'inscricao_estadual': '',
            'registro_crmv': '',
            'endereco': '',
            'numero': '',
            'bairro': '',
            'cidade': '',
            'estado': '',
            'cep': '',
            'telefone_comercial': '',
            'celular': '',
            'email': '',
        }
    )
    
    # Verificar se o usuário tem permissão para editar (staff ou superuser)
    pode_editar = request.user.is_staff or request.user.is_superuser
    
    # Processar formulário de edição (apenas para staff/admin)
    if request.method == 'POST' and pode_editar:
        try:
            dados_unidade.nome_empreendimento = request.POST.get('nome_empreendimento', '')
            dados_unidade.cnpj = request.POST.get('cnpj', '')
            dados_unidade.inscricao_estadual = request.POST.get('inscricao_estadual', '')
            dados_unidade.registro_crmv = request.POST.get('registro_crmv', '')
            dados_unidade.endereco = request.POST.get('endereco', '')
            dados_unidade.numero = request.POST.get('numero', '')
            dados_unidade.bairro = request.POST.get('bairro', '')
            dados_unidade.cidade = request.POST.get('cidade', '')
            dados_unidade.estado = request.POST.get('estado', '')
            dados_unidade.cep = request.POST.get('cep', '')
            dados_unidade.telefone_comercial = request.POST.get('telefone_comercial', '')
            dados_unidade.celular = request.POST.get('celular', '')
            dados_unidade.email = request.POST.get('email', '')
            
            # Processar contatos adicionais
            contatos_adicionais = []
            
            # Primeiro, preservar contatos salvos
            i = 1
            while f'contato_salvo_tipo_{i}' in request.POST:
                tipo = request.POST.get(f'contato_salvo_tipo_{i}')
                valor = request.POST.get(f'contato_salvo_valor_{i}')
                whatsapp = request.POST.get(f'contato_salvo_whatsapp_{i}', 'false')
                
                if tipo and valor:
                    contatos_adicionais.append({
                        'tipo': tipo,
                        'valor': valor,
                        'whatsapp': whatsapp == 'true'
                    })
                i += 1
            
            # Depois, adicionar novos contatos
            i = 1
            while f'contato_tipo_{i}' in request.POST:
                tipo = request.POST.get(f'contato_tipo_{i}')
                valor = request.POST.get(f'contato_valor_{i}')
                whatsapp = request.POST.get(f'contato_whatsapp_{i}', 'false')
                
                if tipo and valor:
                    contatos_adicionais.append({
                        'tipo': tipo,
                        'valor': valor,
                        'whatsapp': whatsapp == 'true'
                    })
                i += 1
            
            dados_unidade.contatos_adicionais = contatos_adicionais
            
            # Processar upload de imagem (logomarca)
            if 'logomarca' in request.FILES:
                dados_unidade.logomarca = request.FILES['logomarca']
            
            dados_unidade.save()
            messages.success(request, 'Dados da unidade atualizados com sucesso!')
            return redirect('cadastros:dados_unidade')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar dados: {str(e)}')
    
    context = {
        'dados_unidade': dados_unidade,
        'pode_editar': pode_editar,
    }
    
    return render(request, 'cadastros/dados_unidade.html', context)


# ==================== Views específicas para Exames ====================

@login_required
def exames_list(request):
    """Listar exames com busca e filtros"""
    query = request.GET.get('q', '')
    
    # Buscar exames
    if query:
        items = Exame.objects.filter(nome__icontains=query)
    else:
        items = Exame.objects.all()
    
    # Filtros avançados
    active_filters = {}
    
    # Filtro por nome
    if request.GET.get('filter_nome'):
        nome = request.GET.get('filter_nome')
        items = items.filter(nome__icontains=nome)
        active_filters['nome'] = nome
    
    # Filtro por código
    if request.GET.get('filter_codigo'):
        codigo = request.GET.get('filter_codigo')
        items = items.filter(codigo__icontains=codigo)
        active_filters['codigo'] = codigo
    
    # Filtro por status
    if request.GET.get('filter_ativo'):
        value = request.GET.get('filter_ativo')
        if value.lower() in ['true', '1', 'sim']:
            items = items.filter(ativo=True)
            active_filters['ativo'] = 'True'
        elif value.lower() in ['false', '0', 'não', 'nao']:
            items = items.filter(ativo=False)
            active_filters['ativo'] = 'False'
    
    # Ordenar por nome
    items = items.order_by('nome')
    
    # Paginação
    paginator = Paginator(items, 20)  # 20 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tipo': 'exames',
        'label': 'Exames',
        'page_obj': page_obj,
        'query': query,
        'active_filters': active_filters,
    }
    
    return render(request, 'cadastros/exames_list.html', context)


@login_required
def exame_create(request):
    """Criar novo exame"""
    if request.method == 'POST':
        try:
            # Processar dados do formulário
            data = {
                'nome': request.POST.get('nome'),
                'descricao': request.POST.get('descricao', ''),
                'modelo_cabecalho': int(request.POST.get('modelo_cabecalho', 1)),
                'modelo_info_paciente': int(request.POST.get('modelo_info_paciente', 1)),
                'conteudo_apresentacao': request.POST.get('conteudo_apresentacao', ''),
                'conteudo_encerramento': request.POST.get('conteudo_encerramento', ''),
                'modelo_rodape': int(request.POST.get('modelo_rodape', 1)),
            }
            
            # Processar campo booleano ativo
            data['ativo'] = request.POST.get('ativo', 'false') == 'true'
            
            # Criar objeto
            Exame.objects.create(**data)
            
            messages.success(request, 'Exame criado com sucesso!')
            return redirect('cadastros:exames_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar exame: {str(e)}')
    
    # Buscar dados da unidade para preview
    dados_unidade = DadosUnidade.objects.first()
    
    context = {
        'dados_unidade': dados_unidade,
    }
    
    return render(request, 'cadastros/exame_form.html', context)


@login_required
def exame_edit(request, pk):
    """Editar exame existente"""
    obj = get_object_or_404(Exame, pk=pk)
    
    if request.method == 'POST':
        try:
            # Atualizar dados
            obj.nome = request.POST.get('nome')
            obj.descricao = request.POST.get('descricao', '')
            obj.modelo_cabecalho = int(request.POST.get('modelo_cabecalho', 1))
            obj.modelo_info_paciente = int(request.POST.get('modelo_info_paciente', 1))
            obj.conteudo_apresentacao = request.POST.get('conteudo_apresentacao', '')
            obj.conteudo_encerramento = request.POST.get('conteudo_encerramento', '')
            obj.modelo_rodape = int(request.POST.get('modelo_rodape', 1))
            
            # Processar campo booleano
            obj.ativo = request.POST.get('ativo', 'false') == 'true'
            
            obj.save()
            
            messages.success(request, 'Exame atualizado com sucesso!')
            return redirect('cadastros:exames_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar exame: {str(e)}')
    
    # Buscar dados da unidade para preview
    dados_unidade = DadosUnidade.objects.first()
    
    context = {
        'object': obj,
        'dados_unidade': dados_unidade,
    }
    
    return render(request, 'cadastros/exame_form.html', context)


@login_required
def exame_delete(request, pk):
    """Excluir exame"""
    obj = get_object_or_404(Exame, pk=pk)
    
    if request.method == 'POST':
        try:
            obj.delete()
            # Se for AJAX, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Exame excluído com sucesso!'
                })
            # Se for POST normal, redirecionar
            messages.success(request, f'Exame "{obj.nome}" excluído com sucesso!')
            return redirect('cadastros:exames_list')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            messages.error(request, f'Erro ao excluir exame: {str(e)}')
            return redirect('cadastros:exames_list')
    
    # GET não é mais suportado - redirecionar para a lista
    return redirect('cadastros:exames_list')


# ============================================================================
# VIEWS DE RECEITAS
# ============================================================================

@login_required
def receitas_list(request):
    """Listar receitas com busca e filtros"""
    query = request.GET.get('q', '')
    
    # Buscar receitas
    if query:
        items = ModeloReceita.objects.filter(nome__icontains=query)
    else:
        items = ModeloReceita.objects.all()
    
    # Filtros avançados
    active_filters = {}
    
    # Filtro por nome
    if request.GET.get('filter_nome'):
        nome = request.GET.get('filter_nome')
        items = items.filter(nome__icontains=nome)
        active_filters['nome'] = nome
    
    # Filtro por status
    if request.GET.get('filter_ativo'):
        value = request.GET.get('filter_ativo')
        if value.lower() in ['true', '1', 'sim']:
            items = items.filter(ativo=True)
            active_filters['ativo'] = 'True'
        elif value.lower() in ['false', '0', 'não', 'nao']:
            items = items.filter(ativo=False)
            active_filters['ativo'] = 'False'
    
    # Filtro por código
    if request.GET.get('filter_codigo'):
        codigo = request.GET.get('filter_codigo')
        items = items.filter(codigo__icontains=codigo)
        active_filters['codigo'] = codigo
    
    # Filtro por autor
    if request.GET.get('filter_autor'):
        autor = request.GET.get('filter_autor')
        items = items.filter(autor__username__icontains=autor)
        active_filters['autor'] = autor
    
    # Ordenar por nome
    items = items.order_by('nome')
    
    # Paginação
    paginator = Paginator(items, 20)  # 20 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tipo': 'receitas',
        'label': 'Receitas',
        'page_obj': page_obj,
        'query': query,
        'active_filters': active_filters,
    }
    
    return render(request, 'cadastros/receitas_list.html', context)


@login_required
def receita_create(request):
    """Criar nova receita"""
    if request.method == 'POST':
        try:
            # Processar dados do formulário
            data = {
                'nome': request.POST.get('nome'),
                'descricao': request.POST.get('descricao', ''),
                'modelo_cabecalho': int(request.POST.get('modelo_cabecalho', 1)),
                'modelo_info_paciente': int(request.POST.get('modelo_info_paciente', 1)),
                'conteudo_apresentacao': request.POST.get('conteudo_apresentacao', ''),
                'conteudo_encerramento': request.POST.get('conteudo_encerramento', ''),
                'modelo_rodape': int(request.POST.get('modelo_rodape', 1)),
            }
            
            # Processar campo booleano ativo
            data['ativo'] = request.POST.get('ativo', 'false') == 'true'
            
            # Definir o autor como o usuário atual
            data['autor'] = request.user
            
            # Criar objeto
            ModeloReceita.objects.create(**data)
            
            messages.success(request, 'Receita criada com sucesso!')
            return redirect('cadastros:receitas_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar receita: {str(e)}')
    
    # Buscar dados da unidade para preview
    dados_unidade = DadosUnidade.objects.first()
    
    context = {
        'dados_unidade': dados_unidade,
    }
    
    return render(request, 'cadastros/receita_form.html', context)


@login_required
def receita_edit(request, pk):
    """Editar receita existente"""
    obj = get_object_or_404(ModeloReceita, pk=pk)
    
    if request.method == 'POST':
        try:
            # Atualizar dados
            obj.nome = request.POST.get('nome')
            obj.descricao = request.POST.get('descricao', '')
            obj.modelo_cabecalho = int(request.POST.get('modelo_cabecalho', 1))
            obj.modelo_info_paciente = int(request.POST.get('modelo_info_paciente', 1))
            obj.conteudo_apresentacao = request.POST.get('conteudo_apresentacao', '')
            obj.conteudo_encerramento = request.POST.get('conteudo_encerramento', '')
            obj.modelo_rodape = int(request.POST.get('modelo_rodape', 1))
            
            # Processar campo booleano
            obj.ativo = request.POST.get('ativo', 'false') == 'true'
            
            obj.save()
            
            messages.success(request, 'Receita atualizada com sucesso!')
            return redirect('cadastros:receitas_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar receita: {str(e)}')
    
    # Buscar dados da unidade para preview
    dados_unidade = DadosUnidade.objects.first()
    
    context = {
        'object': obj,
        'dados_unidade': dados_unidade,
    }
    
    return render(request, 'cadastros/receita_form.html', context)


@login_required
def receita_delete(request, pk):
    """Excluir receita"""
    obj = get_object_or_404(ModeloReceita, pk=pk)
    
    if request.method == 'POST':
        try:
            obj.delete()
            # Se for AJAX, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Receita excluída com sucesso!'
                })
            # Se for POST normal, redirecionar
            messages.success(request, f'Receita "{obj.nome}" excluída com sucesso!')
            return redirect('cadastros:receitas_list')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            messages.error(request, f'Erro ao excluir receita: {str(e)}')
            return redirect('cadastros:receitas_list')
    
    # GET não é mais suportado - redirecionar para a lista
    return redirect('cadastros:receitas_list')


# ================== VIEWS ESPECÍFICAS PARA DOCUMENTOS ==================

def documentos_list(request):
    """Listar documentos com busca e filtros"""
    query = request.GET.get('q', '')
    
    # Buscar documentos
    if query:
        items = ModeloDocumento.objects.filter(nome__icontains=query)
    else:
        items = ModeloDocumento.objects.all()
    
    # Filtros avançados
    active_filters = {}
    
    # Filtro por nome
    if request.GET.get('filter_nome'):
        nome = request.GET.get('filter_nome')
        items = items.filter(nome__icontains=nome)
        active_filters['nome'] = nome
    
    # Filtro por status
    if request.GET.get('filter_ativo'):
        value = request.GET.get('filter_ativo')
        if value.lower() in ['true', '1', 'sim']:
            items = items.filter(ativo=True)
            active_filters['ativo'] = 'True'
        elif value.lower() in ['false', '0', 'não', 'nao']:
            items = items.filter(ativo=False)
            active_filters['ativo'] = 'False'
    
    # Filtro por código
    if request.GET.get('filter_codigo'):
        codigo = request.GET.get('filter_codigo')
        items = items.filter(codigo__icontains=codigo)
        active_filters['codigo'] = codigo
    
    # Filtro por autor
    if request.GET.get('filter_autor'):
        autor = request.GET.get('filter_autor')
        items = items.filter(autor__username__icontains=autor)
        active_filters['autor'] = autor
    
    # Ordenar por nome
    items = items.order_by('nome')
    
    # Paginação
    paginator = Paginator(items, 20)  # 20 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tipo': 'documentos',
        'label': 'Documentos',
        'page_obj': page_obj,
        'query': query,
        'active_filters': active_filters,
    }
    
    return render(request, 'cadastros/documentos_list.html', context)


@login_required
def documento_create(request):
    """Criar novo documento"""
    if request.method == 'POST':
        try:
            # Processar dados do formulário
            data = {
                'nome': request.POST.get('nome'),
                'descricao': request.POST.get('descricao', ''),
                'modelo_cabecalho': int(request.POST.get('modelo_cabecalho', 1)),
                'modelo_info_paciente': int(request.POST.get('modelo_info_paciente', 1)),
                'conteudo_apresentacao': request.POST.get('conteudo_apresentacao', ''),
                'conteudo_encerramento': request.POST.get('conteudo_encerramento', ''),
                'modelo_rodape': int(request.POST.get('modelo_rodape', 1)),
            }
            
            # Processar campo booleano ativo
            data['ativo'] = request.POST.get('ativo', 'false') == 'true'
            
            # Definir o autor como o usuário atual
            data['autor'] = request.user
            
            # Criar objeto
            ModeloDocumento.objects.create(**data)
            
            messages.success(request, 'Documento criado com sucesso!')
            return redirect('cadastros:documentos_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar documento: {str(e)}')
    
    # Buscar dados da unidade para preview
    dados_unidade = DadosUnidade.objects.first()
    
    context = {
        'dados_unidade': dados_unidade,
    }
    
    return render(request, 'cadastros/documento_form.html', context)


@login_required
def documento_edit(request, pk):
    """Editar documento existente"""
    obj = get_object_or_404(ModeloDocumento, pk=pk)
    
    if request.method == 'POST':
        try:
            # Atualizar dados
            obj.nome = request.POST.get('nome')
            obj.descricao = request.POST.get('descricao', '')
            obj.modelo_cabecalho = int(request.POST.get('modelo_cabecalho', 1))
            obj.modelo_info_paciente = int(request.POST.get('modelo_info_paciente', 1))
            obj.conteudo_apresentacao = request.POST.get('conteudo_apresentacao', '')
            obj.conteudo_encerramento = request.POST.get('conteudo_encerramento', '')
            obj.modelo_rodape = int(request.POST.get('modelo_rodape', 1))
            
            # Processar campo booleano
            obj.ativo = request.POST.get('ativo', 'false') == 'true'
            
            obj.save()
            
            messages.success(request, 'Documento atualizado com sucesso!')
            return redirect('cadastros:documentos_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar documento: {str(e)}')
    
    # Buscar dados da unidade para preview
    dados_unidade = DadosUnidade.objects.first()
    
    context = {
        'object': obj,
        'dados_unidade': dados_unidade,
    }
    
    return render(request, 'cadastros/documento_form.html', context)


@login_required
def documento_delete(request, pk):
    """Excluir documento"""
    obj = get_object_or_404(ModeloDocumento, pk=pk)
    
    if request.method == 'POST':
        try:
            obj.delete()
            # Se for AJAX, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Documento excluído com sucesso!'
                })
            # Se for POST normal, redirecionar
            messages.success(request, f'Documento "{obj.nome}" excluído com sucesso!')
            return redirect('cadastros:documentos_list')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            messages.error(request, f'Erro ao excluir documento: {str(e)}')
            return redirect('cadastros:documentos_list')
    
    # GET não é mais suportado - redirecionar para a lista
    return redirect('cadastros:documentos_list')

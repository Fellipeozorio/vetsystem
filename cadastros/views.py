from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import (
    Especie, Raca, Pelagem, FilaAtendimento, Patologia,
    TipoAtendimento, Vacina, Exame, AtributoExame,
    ReferenciaExame, ModeloReceita, ModeloDocumento, OrigemCliente,
    ProtocoloVacina
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
    'modelos-receita': ModeloReceita,
    'modelos-documento': ModeloDocumento,
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
    'modelos-receita': 'Modelos de Receita',
    'modelos-documento': 'Modelos de Documento',
    'origens-cliente': 'Origens dos Clientes',
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
            elif tipo in ['modelos-receita', 'modelos-documento']:
                data['conteudo'] = request.POST.get('conteudo', '')
            
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
            elif tipo in ['modelos-receita', 'modelos-documento']:
                obj.conteudo = request.POST.get('conteudo', '')
            
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

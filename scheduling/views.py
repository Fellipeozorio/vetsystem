from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.db.models import Q
from django.utils import timezone
from django.template.loader import render_to_string
from datetime import datetime, timedelta, date, time as datetime_time
import json

from .models import Agendamento, HorarioFuncionamento, ConfiguracaoAgendaUsuario, FilaDiaCalendario, HorarioAtendimentoUsuario
from cadastros.models import TipoAtendimento, FilaAtendimento
from clients.models import Client
from patients.models import Pet
from django.contrib.auth.models import User


def _is_time_between(target, start, end):
    """Retorna True se target estiver no intervalo [start, end)"""
    if not (start and end and target):
        return False
    return (start <= target) and (target < end)


def _validate_agendamento_allowed(data_agendamento, horario, duracao_minutos, veterinario, exclude_agendamento_id=None):
    """Valida se é permitido criar/editar agendamento na data/horário informados.

    Regras:
    - Se houver veterinário com `escala_fixa`, usar os horários semanais do veterinário.
    - Caso contrário (escala_variavel ou sem veterinário), usar horários de funcionamento da clínica.
    - Para agendamentos sem horário (horario is None), apenas verificar se a clínica está aberta naquele dia.
    - Para agendamentos com horário, verificar que o horário esteja dentro do intervalo permitido
      e não colida com agendamentos existentes do mesmo veterinário.
    """
    # Obter weekday para HorarioFuncionamento (model usa 0=Segunda..6=Domingo)
    weekday_model = data_agendamento.weekday()  # 0=Monday
    # Para HorarioAtendimentoUsuario (0=Domingo..6=Sábado) convertemos
    weekday_usuario = (weekday_model + 1) % 7

    horario_inicio = None
    horario_fim = None

    # Se houver veterinário, tentar obter configuração
    if veterinario:
        try:
            config = veterinario.config_agenda
            if config.tipo_atendimento == 'escala_fixa':
                horario_dia = config.horarios_semanais.filter(dia_semana=weekday_usuario, trabalha=True).first()
                if not horario_dia or not horario_dia.horario_inicio or not horario_dia.horario_fim:
                    return False, 'Veterinário não atende neste dia'
                horario_inicio = horario_dia.horario_inicio
                horario_fim = horario_dia.horario_fim
        except ConfiguracaoAgendaUsuario.DoesNotExist:
            pass

    # Se não determinamos horários pelo veterinário, usar horário da clínica
    if not horario_inicio or not horario_fim:
        horario_clinica = HorarioFuncionamento.objects.filter(dia_semana=weekday_model, ativo=True).first()
        if not horario_clinica:
            return False, 'Clínica não funciona neste dia'
        horario_inicio = horario_clinica.horario_inicio
        horario_fim = horario_clinica.horario_fim

    # Se é agendamento sem horário, validar que temos horários válidos
    # (significa que o veterinário trabalha neste dia ou a clínica funciona)
    if not horario:
        # Se tem veterinário com escala fixa, verificamos se ele trabalha
        if veterinario:
            try:
                config = veterinario.config_agenda
                if config.tipo_atendimento == 'escala_fixa':
                    # Já validamos acima - se chegou aqui com horario_inicio/fim,
                    # significa que ele trabalha neste dia
                    return True, None
            except ConfiguracaoAgendaUsuario.DoesNotExist:
                pass
        return True, None

    # Validar que o horário está dentro do intervalo permitido
    if not _is_time_between(horario, horario_inicio, horario_fim):
        return False, 'Horário fora do horário de atendimento'

    # Verificar colisões com outros agendamentos do mesmo veterinário
    if veterinario:
        inicio_dt = datetime.combine(data_agendamento, horario)
        fim_dt = inicio_dt + timedelta(minutes=int(duracao_minutos or 0))

        conflitos = Agendamento.objects.filter(
            veterinario=veterinario,
            data=data_agendamento,
        ).exclude(status='cancelado')

        if exclude_agendamento_id:
            conflitos = conflitos.exclude(id=exclude_agendamento_id)

        for ag in conflitos:
            if not ag.horario:
                continue
            ag_inicio = datetime.combine(ag.data, ag.horario)
            ag_fim = ag_inicio + timedelta(minutes=ag.duracao_minutos or 0)
            # overlap check
            if (inicio_dt < ag_fim) and (ag_inicio < fim_dt):
                return False, 'Horário já reservado para o veterinário'

    return True, None


@login_required
def agenda_view(request):
    """View principal da agenda"""
    tipos_atendimento = TipoAtendimento.objects.filter(ativo=True)
    filas = FilaAtendimento.objects.all()
    
    context = {
        'tipos_atendimento': tipos_atendimento,
        'filas': filas,
    }
    return render(request, 'scheduling/agenda.html', context)


@login_required
def configuracao_view(request):
    """View de configuração da agenda"""
    horarios = HorarioFuncionamento.objects.all().order_by('dia_semana')
    usuarios = User.objects.filter(is_active=True)
    
    context = {
        'horarios': horarios,
        'usuarios': usuarios,
        'is_admin': request.user.is_superuser,
    }
    return render(request, 'scheduling/configuracao.html', context)


@login_required
@require_GET
def get_eventos_api(request):
    """API para retornar eventos do calendário"""
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    if not start or not end:
        return JsonResponse({'error': 'Parâmetros start e end são obrigatórios'}, status=400)
    
    # Converter strings para objetos date
    start_date = datetime.fromisoformat(start.replace('Z', '+00:00')).date()
    end_date = datetime.fromisoformat(end.replace('Z', '+00:00')).date()
    
    # Buscar agendamentos no período
    agendamentos = Agendamento.objects.filter(
        data__gte=start_date,
        data__lte=end_date
    ).select_related('animal', 'cliente', 'tipo_atendimento', 'fila', 'veterinario')
    
    # Formatar eventos para o calendário
    eventos = []
    for agendamento in agendamentos:
        # Verificar se tem horário ou é all-day
        if agendamento.horario:
            # Combinar data e horário mantendo timezone local para preservar a data correta
            # Usando timezone.make_aware para criar datetime timezone-aware
            naive_datetime = datetime.combine(agendamento.data, agendamento.horario)
            # Tornar timezone-aware assumindo timezone local do Django
            start_datetime = timezone.make_aware(naive_datetime, timezone.get_current_timezone())
            end_datetime = start_datetime + timedelta(minutes=agendamento.duracao_minutos)
            all_day = False
        else:
            # Agendamento sem horário - all-day
            # Para eventos all-day, usar apenas a data sem horário
            start_datetime = timezone.make_aware(
                datetime.combine(agendamento.data, datetime_time.min),
                timezone.get_current_timezone()
            )
            end_datetime = timezone.make_aware(
                datetime.combine(agendamento.data, datetime_time.max),
                timezone.get_current_timezone()
            )
            all_day = True
        
        # Cores por status
        cores_status = {
            'agendado': '#3788d8',
            'espera': '#f59f00',
            'em_atendimento': '#206bc4',
            'atendido': '#2fb344',
            'cancelado': '#d63939',
            'atrasado': '#ae3ec9',
        }
        
        eventos.append({
            'id': str(agendamento.id),
            'title': f'{agendamento.cliente.nome_completo} - {agendamento.animal.nome}',
            'start': start_datetime.isoformat(),
            'end': end_datetime.isoformat(),
            'allDay': all_day,
            'backgroundColor': cores_status.get(agendamento.status, '#3788d8'),
            'color': cores_status.get(agendamento.status, '#3788d8'),
            'resourceIds': [str(agendamento.fila.id)] if agendamento.fila else [],
            'resourceId': str(agendamento.fila.id) if agendamento.fila else None,
            'extendedProps': {
                'cliente': agendamento.cliente.nome_completo,
                'animal': agendamento.animal.nome,
                'tipoAtendimento': agendamento.tipo_atendimento.nome,
                'tipo': agendamento.tipo_atendimento.nome,
                'status': agendamento.status,
                'status_display': agendamento.get_status_display(),
                'celular': agendamento.celular_cliente,
                'observacoes': agendamento.observacoes,
                'veterinario': agendamento.veterinario.get_full_name() if agendamento.veterinario else '',
                'horario': agendamento.horario.strftime('%H:%M') if agendamento.horario else 'sem-horario',
                'duracaoMinutos': agendamento.duracao_minutos,
                'dataHoraInicio': start_datetime.isoformat() if not all_day else None,
            }
        })
    
    return JsonResponse(eventos, safe=False)


@login_required
def get_agendamento_api(request, pk):
    """API para obter detalhes de um agendamento específico"""
    try:
        agendamento = get_object_or_404(Agendamento, id=pk)
        
        return JsonResponse({
            'id': agendamento.id,
            'tipo_atendimento_id': agendamento.tipo_atendimento.id if agendamento.tipo_atendimento else None,
            'tipo_atendimento_nome': agendamento.tipo_atendimento.nome if agendamento.tipo_atendimento else '',
            'fila_id': agendamento.fila.id if agendamento.fila else None,
            'fila_nome': agendamento.fila.nome if agendamento.fila else '',
            'veterinario_id': agendamento.veterinario.id if agendamento.veterinario else None,
            'veterinario_nome': agendamento.veterinario.get_full_name() if agendamento.veterinario else '',
            'data': agendamento.data.isoformat() if agendamento.data else None,
            'horario': agendamento.horario.strftime('%H:%M') if agendamento.horario else 'sem-horario',
            'duracao_minutos': agendamento.duracao_minutos,
            'duracao_display': f'{agendamento.duracao_minutos} min' if agendamento.duracao_minutos else '',
            'cliente_id': agendamento.cliente.id if agendamento.cliente else None,
            'cliente_nome': agendamento.cliente.nome_completo if agendamento.cliente else '',
            'animal_id': agendamento.animal.id if agendamento.animal else None,
            'animal_nome': agendamento.animal.nome if agendamento.animal else '',
            'celular_cliente': agendamento.celular_cliente or '',
            'celular_whatsapp': agendamento.cliente.celular_whatsapp if agendamento.cliente else False,
            'status': agendamento.status,
            'observacoes': agendamento.observacoes or '',
            'data_hora_chegada': agendamento.data_hora_chegada.isoformat() if agendamento.data_hora_chegada else None,
            'data_hora_inicio_atendimento': agendamento.data_hora_inicio_atendimento.isoformat() if agendamento.data_hora_inicio_atendimento else None,
            'data_hora_fim_atendimento': agendamento.data_hora_fim_atendimento.isoformat() if agendamento.data_hora_fim_atendimento else None,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def criar_agendamento_api(request):
    """API para criar novo agendamento"""
    try:
        data = json.loads(request.body)
        
        # Validar dados obrigatórios
        campos_obrigatorios = ['tipo_atendimento_id', 'data', 'horario', 'duracao_minutos', 
                              'cliente_id', 'animal_id']
        for campo in campos_obrigatorios:
            if campo not in data:
                return JsonResponse({'error': f'Campo {campo} é obrigatório'}, status=400)
        
        # Buscar objetos relacionados
        tipo_atendimento = get_object_or_404(TipoAtendimento, id=data['tipo_atendimento_id'])
        cliente = get_object_or_404(Client, id=data['cliente_id'])
        animal = get_object_or_404(Pet, id=data['animal_id'])
        
        # Fila opcional
        fila = None
        if data.get('fila_id'):
            fila = get_object_or_404(FilaAtendimento, id=data['fila_id'])
        
        # Veterinário opcional
        veterinario = None
        if data.get('veterinario_id'):
            veterinario = get_object_or_404(User, id=data['veterinario_id'])
        
        # Converter strings de data e hora
        data_agendamento = datetime.strptime(data['data'], '%Y-%m-%d').date()
        
        # Validar se a clínica funciona neste dia
        dia_semana = data_agendamento.weekday()  # 0=Monday
        horario_clinica = HorarioFuncionamento.objects.filter(
            dia_semana=dia_semana,
            ativo=True
        ).first()
        
        if not horario_clinica:
            return JsonResponse({
                'error': 'A clínica não funciona neste dia da semana'
            }, status=400)
        
        # Horário pode ser "sem-horario" ou um horário válido
        horario = None
        if data['horario'] and data['horario'] != 'sem-horario':
            horario = datetime.strptime(data['horario'], '%H:%M').time()
        
        # Validar se é permitido agendar nesta data/horário
        is_allowed, message = _validate_agendamento_allowed(
            data_agendamento, horario, int(data['duracao_minutos']), veterinario
        )
        if not is_allowed:
            return JsonResponse({'error': message}, status=400)
        
        # Criar agendamento
        agendamento = Agendamento.objects.create(
            tipo_atendimento=tipo_atendimento,
            fila=fila,
            data=data_agendamento,
            horario=horario,
            duracao_minutos=int(data['duracao_minutos']),
            cliente=cliente,
            animal=animal,
            veterinario=veterinario,
            celular_cliente=data.get('celular_cliente', ''),
            status=data.get('status', 'agendado'),
            observacoes=data.get('observacoes', ''),
            criado_por=request.user
        )
        
        return JsonResponse({
            'success': True,
            'id': agendamento.id,
            'message': 'Agendamento criado com sucesso'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def editar_agendamento_api(request, pk):
    """API para editar agendamento existente"""
    try:
        agendamento = get_object_or_404(Agendamento, id=pk)
        data = json.loads(request.body)
        
        # Atualizar campos
        if 'tipo_atendimento_id' in data:
            agendamento.tipo_atendimento = get_object_or_404(TipoAtendimento, id=data['tipo_atendimento_id'])
        
        if 'fila_id' in data:
            if data['fila_id']:
                agendamento.fila = get_object_or_404(FilaAtendimento, id=data['fila_id'])
            else:
                agendamento.fila = None
        
        if 'data' in data:
            nova_data = datetime.strptime(data['data'], '%Y-%m-%d').date()
            # Validar se a clínica funciona neste dia
            dia_semana = nova_data.weekday()  # 0=Monday
            horario_clinica = HorarioFuncionamento.objects.filter(
                dia_semana=dia_semana,
                ativo=True
            ).first()
            
            if not horario_clinica:
                return JsonResponse({
                    'error': 'A clínica não funciona neste dia da semana'
                }, status=400)
            
            agendamento.data = nova_data
        
        if 'horario' in data:
            if data['horario'] and data['horario'] != 'sem-horario':
                agendamento.horario = datetime.strptime(data['horario'], '%H:%M').time()
            else:
                agendamento.horario = None
        
        if 'duracao_minutos' in data:
            agendamento.duracao_minutos = int(data['duracao_minutos'])
        
        if 'cliente_id' in data:
            agendamento.cliente = get_object_or_404(Client, id=data['cliente_id'])
        
        if 'animal_id' in data:
            agendamento.animal = get_object_or_404(Pet, id=data['animal_id'])
        
        if 'veterinario_id' in data:
            if data['veterinario_id']:
                agendamento.veterinario = get_object_or_404(User, id=data['veterinario_id'])
            else:
                agendamento.veterinario = None
        
        if 'celular_cliente' in data:
            agendamento.celular_cliente = data['celular_cliente']
        
        if 'status' in data:
            status_anterior = agendamento.status
            novo_status = data['status']
            
            # Atualizar campos de tempo baseado na mudança de status
            if status_anterior != novo_status:
                agora = timezone.now()
                
                # Quando muda para "espera" - marca chegada
                if novo_status == 'espera' and not agendamento.data_hora_chegada:
                    agendamento.data_hora_chegada = agora
                
                # Quando muda para "em_atendimento" - marca início do atendimento
                if novo_status == 'em_atendimento' and not agendamento.data_hora_inicio_atendimento:
                    agendamento.data_hora_inicio_atendimento = agora
                    # Se não marcou chegada ainda, marca agora também
                    if not agendamento.data_hora_chegada:
                        agendamento.data_hora_chegada = agora
                
                # Quando muda para "atendido" - marca fim do atendimento
                if novo_status == 'atendido' and not agendamento.data_hora_fim_atendimento:
                    agendamento.data_hora_fim_atendimento = agora
                    # Se não marcou início do atendimento, marca agora também
                    if not agendamento.data_hora_inicio_atendimento:
                        agendamento.data_hora_inicio_atendimento = agora
                    # Se não marcou chegada, marca agora também
                    if not agendamento.data_hora_chegada:
                        agendamento.data_hora_chegada = agora
            
            agendamento.status = novo_status
        
        if 'observacoes' in data:
            agendamento.observacoes = data['observacoes']
        
        # Validar se é permitido manter este agendamento nas novas condições
        is_allowed, message = _validate_agendamento_allowed(
            agendamento.data, agendamento.horario, agendamento.duracao_minutos,
            agendamento.veterinario, exclude_agendamento_id=agendamento.id
        )
        if not is_allowed:
            return JsonResponse({'error': message}, status=400)
        
        agendamento.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Agendamento atualizado com sucesso'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def deletar_agendamento_api(request, pk):
    """API para deletar agendamento"""
    try:
        agendamento = get_object_or_404(Agendamento, id=pk)
        agendamento.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Agendamento deletado com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def atualizar_ordem_agendamentos_api(request):
    """API para atualizar a ordem dos agendamentos após drag and drop"""
    try:
        data = json.loads(request.body)
        ordem_ids = data.get('ordem_ids', [])
        
        # Atualizar ordem de cada agendamento
        for indice, agendamento_id in enumerate(ordem_ids):
            Agendamento.objects.filter(id=agendamento_id).update(ordem=indice)
        
        return JsonResponse({
            'success': True,
            'message': 'Ordem atualizada com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def get_clientes_api(request):
    """API para autocomplete de clientes"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse([], safe=False)
    
    clientes = Client.objects.filter(
        Q(nome_completo__icontains=query) | 
        Q(cpf__icontains=query) |
        Q(celular__icontains=query)
    )[:10]
    
    results = [{
        'id': c.id,
        'nome_completo': c.nome_completo,
        'cpf': c.cpf or '',
        'celular': c.celular or '',
        'celular_whatsapp': c.celular_whatsapp,
    } for c in clientes]
    
    return JsonResponse(results, safe=False)


@login_required
@require_GET
def get_animais_api(request, cliente_id):
    """API para buscar animais de um cliente"""
    animais = Pet.objects.select_related('especie', 'raca').filter(tutor_id=cliente_id)
    
    results = [{
        'id': a.id,
        'nome': a.nome,
        'especie': str(a.especie) if a.especie else '',
        'raca': str(a.raca) if a.raca else '',
    } for a in animais]
    
    return JsonResponse(results, safe=False)


@login_required
@require_GET
def buscar_clientes_api(request):
    """API para buscar clientes e animais com filtros"""
    cliente_nome = request.GET.get('cliente', '')
    animal_nome = request.GET.get('animal', '')
    telefone = request.GET.get('telefone', '')
    
    # Buscar pets com os filtros
    pets = Pet.objects.select_related('tutor', 'especie', 'raca').all()
    
    if cliente_nome:
        pets = pets.filter(tutor__nome_completo__icontains=cliente_nome)
    
    if animal_nome:
        pets = pets.filter(nome__icontains=animal_nome)
    
    if telefone:
        pets = pets.filter(
            Q(tutor__celular__icontains=telefone)
        )
    
    # Limitar resultados
    pets = pets[:50]
    
    results = []
    for pet in pets:
        results.append({
            'cliente_id': pet.tutor.id,
            'cliente_nome': pet.tutor.nome_completo,
            'animal_id': pet.id,
            'animal_nome': pet.nome,
            'especie': str(pet.especie) if pet.especie else '',
            'telefone': pet.tutor.celular or '',
            'celular_whatsapp': pet.tutor.celular_whatsapp,
        })
    
    return JsonResponse(results, safe=False)


@login_required
@require_GET
def get_cliente_detalhes_api(request, pk):
    """API para buscar detalhes de um cliente"""
    cliente = get_object_or_404(Client, id=pk)
    
    return JsonResponse({
        'id': cliente.id,
        'nome_completo': cliente.nome_completo,
        'cpf': cliente.cpf or '',
        'telefone': cliente.telefone or '',
        'celular': cliente.celular or '',
        'celular_whatsapp': cliente.celular_whatsapp,
    })


@login_required
@require_GET
def get_fila_detalhes_api(request, pk):
    """API para buscar detalhes de uma fila"""
    fila = get_object_or_404(FilaAtendimento, id=pk)
    
    result = {
        'id': fila.id,
        'nome': fila.nome,
        'codigo': fila.codigo,
        'permanente': fila.permanente,
        'atribuido_a': None
    }
    
    if fila.atribuido_a:
        result['atribuido_a'] = {
            'id': fila.atribuido_a.id,
            'nome': f'{fila.atribuido_a.first_name} {fila.atribuido_a.last_name}'.strip() or fila.atribuido_a.username
        }
    
    return JsonResponse(result)


@login_required
@require_GET
def get_veterinarios_api(request):
    """API para buscar lista de veterinários"""
    # Buscar usuários ativos (pode filtrar por grupo se necessário)
    veterinarios = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    
    results = []
    for vet in veterinarios:
        nome = f'{vet.first_name} {vet.last_name}'.strip() or vet.username
        results.append({
            'id': vet.id,
            'nome': nome
        })
    
    return JsonResponse(results, safe=False)


@login_required
@require_GET
def get_filas_dia_api(request, data):
    """API para buscar filas ativas em um dia específico"""
    try:
        data_obj = datetime.strptime(data, '%Y-%m-%d').date()
        
        # Filas permanentes (excluir as que têm registro ativo=False neste dia)
        filas_escondidas_ids = FilaDiaCalendario.objects.filter(
            data=data_obj,
            ativo=False
        ).values_list('fila_id', flat=True)
        
        filas_permanentes = FilaAtendimento.objects.filter(
            permanente=True
        ).exclude(id__in=filas_escondidas_ids)
        
        # Filas não permanentes adicionadas neste dia
        filas_dia = FilaDiaCalendario.objects.filter(
            data=data_obj,
            ativo=True,
            fila__permanente=False  # Excluir filas permanentes para evitar duplicação
        ).select_related('fila')
        
        filas_nao_permanentes = [fd.fila for fd in filas_dia]
        
        # Combinar
        todas_filas = list(filas_permanentes) + filas_nao_permanentes
        
        results = [{
            'id': str(f.id),
            'nome': f.nome,
            'codigo': f.codigo,
            'permanente': f.permanente,
            'atribuido_a_id': f.atribuido_a.id if f.atribuido_a else None
        } for f in todas_filas]
        
        return JsonResponse(results, safe=False)
        
    except ValueError:
        return JsonResponse({'error': 'Data inválida'}, status=400)


@login_required
@require_POST
def adicionar_fila_dia_api(request):
    """API para adicionar fila não permanente em um dia específico"""
    try:
        data = json.loads(request.body)
        
        fila = get_object_or_404(FilaAtendimento, id=data['fila_id'])
        data_obj = datetime.strptime(data['data'], '%Y-%m-%d').date()
        
        # Verificar se já existe
        fila_dia, created = FilaDiaCalendario.objects.get_or_create(
            fila=fila,
            data=data_obj,
            defaults={'criado_por': request.user}
        )
        
        if not created:
            fila_dia.ativo = True
            fila_dia.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Fila adicionada ao dia com sucesso'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def remover_fila_dia_api(request):
    """API para remover/esconder fila de um dia específico (permanente ou não)"""
    try:
        data = json.loads(request.body)
        
        fila = get_object_or_404(FilaAtendimento, id=data['fila_id'])
        data_obj = datetime.strptime(data['data'], '%Y-%m-%d').date()
        
        # Buscar registro existente
        fila_dia = FilaDiaCalendario.objects.filter(
            fila=fila,
            data=data_obj
        ).first()
        
        if fila_dia:
            # Se existe, desativar
            fila_dia.ativo = False
            fila_dia.save()
        else:
            # Se não existe (fila permanente), criar registro com ativo=False para "esconder"
            FilaDiaCalendario.objects.create(
                fila=fila,
                data=data_obj,
                ativo=False
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Fila removida do dia com sucesso'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def get_horarios_api(request):
    """API para buscar horários de funcionamento"""
    horarios = HorarioFuncionamento.objects.all().order_by('dia_semana')
    # Map model dia_semana (HorarioFuncionamento: 0=Segunda,...6=Domingo)
    # to frontend canonical (0=Domingo,1=Segunda,...6=Sábado)
    dias_map = {
        0: 'Segunda-feira',
        1: 'Terça-feira',
        2: 'Quarta-feira',
        3: 'Quinta-feira',
        4: 'Sexta-feira',
        5: 'Sábado',
        6: 'Domingo',
    }

    results = []
    for h in horarios:
        # convert model index -> frontend index
        frontend_dia = (h.dia_semana + 1) % 7
        frontend_display = {
            0: 'Domingo',
            1: 'Segunda-feira',
            2: 'Terça-feira',
            3: 'Quarta-feira',
            4: 'Quinta-feira',
            5: 'Sexta-feira',
            6: 'Sábado',
        }.get(frontend_dia, dias_map.get(h.dia_semana, ''))

        results.append({
            'id': h.id,
            'dia_semana': frontend_dia,
            'dia_semana_display': frontend_display,
            'horario_inicio': h.horario_inicio.strftime('%H:%M'),
            'horario_fim': h.horario_fim.strftime('%H:%M'),
            'ativo': h.ativo,
        })
    
    return JsonResponse(results, safe=False)


@login_required
@require_POST
def editar_horario_api(request, pk):
    """API para editar horário de funcionamento"""
    try:
        horario = get_object_or_404(HorarioFuncionamento, id=pk)
        data = json.loads(request.body)
        
        if 'horario_inicio' in data:
            horario.horario_inicio = datetime.strptime(data['horario_inicio'], '%H:%M').time()
        
        if 'horario_fim' in data:
            horario.horario_fim = datetime.strptime(data['horario_fim'], '%H:%M').time()
        
        if 'ativo' in data:
            horario.ativo = data['ativo']
        
        horario.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Horário atualizado com sucesso'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def get_usuarios_config_api(request):
    """API para buscar configurações de usuários"""
    usuarios = User.objects.filter(is_active=True)
    
    results = []
    for usuario in usuarios:
        try:
            config = usuario.config_agenda
        except ConfiguracaoAgendaUsuario.DoesNotExist:
            # Criar configuração padrão se não existir
            config = ConfiguracaoAgendaUsuario.objects.create(usuario=usuario)
        
        # Obter avatar e perfil do userprofile
        avatar_url = None
        perfil_display = 'Usuário'
        try:
            if hasattr(usuario, 'userprofile'):
                if usuario.userprofile.avatar:
                    avatar_url = usuario.userprofile.avatar.url
                perfil_display = usuario.userprofile.get_perfil_display()
        except:
            pass
        
        # Buscar horários semanais se escala fixa
        horarios_semanais = []
        if config.tipo_atendimento == 'escala_fixa':
            for dia in range(7):
                horario_dia = config.horarios_semanais.filter(dia_semana=dia).first()
                if horario_dia and horario_dia.trabalha:
                    horarios_semanais.append({
                        'dia_semana': horario_dia.dia_semana,
                        'dia_semana_display': horario_dia.get_dia_semana_display(),
                        'horario_inicio': horario_dia.horario_inicio.strftime('%H:%M') if horario_dia.horario_inicio else '',
                        'horario_fim': horario_dia.horario_fim.strftime('%H:%M') if horario_dia.horario_fim else ''
                    })
        
        results.append({
            'id': config.id,
            'usuario_id': usuario.id,
            'usuario_nome': usuario.get_full_name() or usuario.username,
            'usuario_avatar': avatar_url,
            'usuario_perfil': perfil_display,
            'tipo_atendimento': config.tipo_atendimento,
            'tipo_atendimento_display': config.get_tipo_atendimento_display(),
            'permissao_agenda': config.permissao_agenda,
            'permissao_agenda_display': config.get_permissao_agenda_display(),
            'horario_inicio': config.horario_inicio.strftime('%H:%M') if config.horario_inicio else '',
            'horario_fim': config.horario_fim.strftime('%H:%M') if config.horario_fim else '',
            'ativo': config.ativo,
            'horarios_semanais': horarios_semanais
        })
    
    return JsonResponse(results, safe=False)


@login_required
@require_GET
def get_usuario_config_api(request, pk):
    """API para buscar configuração de um usuário específico"""
    try:
        config = get_object_or_404(ConfiguracaoAgendaUsuario, id=pk)
        
        # Buscar horários semanais
        horarios_semanais = []
        for dia in range(7):  # 0 = domingo, 6 = sábado
            horario_dia = config.horarios_semanais.filter(dia_semana=dia).first()
            if horario_dia:
                horarios_semanais.append({
                    'dia_semana': horario_dia.dia_semana,
                    'dia_semana_display': horario_dia.get_dia_semana_display(),
                    'horario_inicio': horario_dia.horario_inicio.strftime('%H:%M') if horario_dia.horario_inicio else '',
                    'horario_fim': horario_dia.horario_fim.strftime('%H:%M') if horario_dia.horario_fim else '',
                    'trabalha': horario_dia.trabalha
                })
            else:
                # Se não existe, usar valores padrão
                horarios_semanais.append({
                    'dia_semana': dia,
                    'dia_semana_display': dict(HorarioAtendimentoUsuario.DIAS_SEMANA).get(dia, ''),
                    'horario_inicio': '',
                    'horario_fim': '',
                    'trabalha': True
                })
        
        result = {
            'id': config.id,
            'usuario_id': config.usuario.id,
            'usuario_nome': config.usuario.get_full_name() or config.usuario.username,
            'tipo_atendimento': config.tipo_atendimento,
            'tipo_atendimento_display': config.get_tipo_atendimento_display(),
            'permissao_agenda': config.permissao_agenda,
            'permissao_agenda_display': config.get_permissao_agenda_display(),
            'horario_inicio': config.horario_inicio.strftime('%H:%M') if config.horario_inicio else '',
            'horario_fim': config.horario_fim.strftime('%H:%M') if config.horario_fim else '',
            'ativo': config.ativo,
            'horarios_semanais': horarios_semanais
        }
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def editar_usuario_config_api(request, pk):
    """API para editar configuração de usuário"""
    try:
        config = get_object_or_404(ConfiguracaoAgendaUsuario, id=pk)
        data = json.loads(request.body)
        
        if 'tipo_atendimento' in data:
            config.tipo_atendimento = data['tipo_atendimento']
        
        if 'permissao_agenda' in data:
            config.permissao_agenda = data['permissao_agenda']
        
        if 'horario_inicio' in data:
            if data['horario_inicio']:
                config.horario_inicio = datetime.strptime(data['horario_inicio'], '%H:%M').time()
            else:
                config.horario_inicio = None
        
        if 'horario_fim' in data:
            if data['horario_fim']:
                config.horario_fim = datetime.strptime(data['horario_fim'], '%H:%M').time()
            else:
                config.horario_fim = None
        
        if 'ativo' in data:
            config.ativo = data['ativo']
        
        config.save()
        
        # Salvar horários semanais se fornecidos
        if 'horarios_semanais' in data:
            for horario_data in data['horarios_semanais']:
                dia_semana = horario_data.get('dia_semana')
                horario_inicio = horario_data.get('horario_inicio')
                horario_fim = horario_data.get('horario_fim')
                trabalha = horario_data.get('trabalha', True)
                
                # Buscar ou criar horário para este dia
                horario, created = HorarioAtendimentoUsuario.objects.get_or_create(
                    config_usuario=config,
                    dia_semana=dia_semana,
                    defaults={
                        'horario_inicio': datetime.strptime(horario_inicio, '%H:%M').time() if horario_inicio else None,
                        'horario_fim': datetime.strptime(horario_fim, '%H:%M').time() if horario_fim else None,
                        'trabalha': trabalha
                    }
                )
                
                if not created:
                    # Atualizar existente
                    if horario_inicio:
                        horario.horario_inicio = datetime.strptime(horario_inicio, '%H:%M').time()
                    else:
                        horario.horario_inicio = None
                    
                    if horario_fim:
                        horario.horario_fim = datetime.strptime(horario_fim, '%H:%M').time()
                    else:
                        horario.horario_fim = None
                    
                    horario.trabalha = trabalha
                    horario.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Configuração atualizada com sucesso'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def salvar_horarios_api(request):
    """API para salvar todos os horários de funcionamento de uma vez"""
    try:
        data = json.loads(request.body)
        horarios_data = data.get('horarios', [])
        
        for horario_data in horarios_data:
            # frontend uses 0=Domingo,1=Segunda,...6=Sábado
            # model HorarioFuncionamento uses 0=Segunda,...6=Domingo
            dia_front = horario_data.get('dia_semana')
            model_dia = (dia_front + 6) % 7

            horario = HorarioFuncionamento.objects.filter(dia_semana=model_dia).first()
            if not horario:
                horario = HorarioFuncionamento.objects.create(dia_semana=model_dia)

            if 'horario_inicio' in horario_data and horario_data['horario_inicio']:
                horario.horario_inicio = datetime.strptime(horario_data['horario_inicio'], '%H:%M').time()

            if 'horario_fim' in horario_data and horario_data['horario_fim']:
                horario.horario_fim = datetime.strptime(horario_data['horario_fim'], '%H:%M').time()

            if 'ativo' in horario_data:
                horario.ativo = horario_data['ativo']

            horario.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Horários salvos com sucesso'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def get_horarios_disponiveis_api(request):
    """API para buscar horários disponíveis para agendamento"""
    try:
        data_str = request.GET.get('data')
        veterinario_id = request.GET.get('veterinario_id')
        
        if not data_str:
            return JsonResponse({'error': 'Parâmetro data é obrigatório'}, status=400)
        
        data_agendamento = datetime.strptime(data_str, '%Y-%m-%d').date()
        dia_semana = data_agendamento.weekday()  # 0=Segunda, 6=Domingo
        
        # Converter para formato do HorarioAtendimentoUsuario (0=Domingo, 6=Sábado)
        dia_semana_usuario = (dia_semana + 1) % 7
        
        # Determinar horários base (clínica ou veterinário)
        horario_inicio = None
        horario_fim = None
        
        if veterinario_id:
            # Buscar configuração do veterinário
            try:
                veterinario = User.objects.get(id=veterinario_id, is_active=True)
                config = veterinario.config_agenda
                
                # Se escala fixa, usar horários específicos do veterinário
                if config.tipo_atendimento == 'escala_fixa':
                    # Buscar horário do dia específico
                    horario_dia = config.horarios_semanais.filter(
                        dia_semana=dia_semana_usuario,
                        trabalha=True
                    ).first()
                    
                    if horario_dia and horario_dia.horario_inicio and horario_dia.horario_fim:
                        horario_inicio = horario_dia.horario_inicio
                        horario_fim = horario_dia.horario_fim
                    else:
                        # Veterinário não trabalha neste dia
                        return JsonResponse({
                            'horarios': [],
                            'message': 'Veterinário não atende neste dia da semana'
                        })
                
                # Se escala variável ou não realiza, usar horários da clínica
                elif config.tipo_atendimento in ['escala_variavel', 'nao_realiza']:
                    # Buscar horários de funcionamento da clínica
                    # Converter dia_semana (0=Seg) para HorarioFuncionamento (0=Seg, 6=Dom)
                    horario_clinica = HorarioFuncionamento.objects.filter(
                        dia_semana=dia_semana,
                        ativo=True
                    ).first()
                    
                    if horario_clinica:
                        horario_inicio = horario_clinica.horario_inicio
                        horario_fim = horario_clinica.horario_fim
                        
            except (User.DoesNotExist, ConfiguracaoAgendaUsuario.DoesNotExist):
                # Sem veterinário válido, usar horários da clínica
                pass
        
        # Se não encontrou horários do veterinário, usar horários da clínica
        if not horario_inicio or not horario_fim:
            horario_clinica = HorarioFuncionamento.objects.filter(
                dia_semana=dia_semana,
                ativo=True
            ).first()
            
            if horario_clinica:
                horario_inicio = horario_clinica.horario_inicio
                horario_fim = horario_clinica.horario_fim
            else:
                # Clínica não funciona neste dia
                return JsonResponse({
                    'horarios': [],
                    'message': 'Clínica não funciona neste dia da semana'
                })
        
        # Gerar todos os slots de 15 minutos no intervalo
        slots_disponiveis = []
        hora_atual = datetime.combine(data_agendamento, horario_inicio)
        hora_fim = datetime.combine(data_agendamento, horario_fim)
        
        while hora_atual < hora_fim:
            slots_disponiveis.append(hora_atual.time())
            hora_atual += timedelta(minutes=15)
        
        # Buscar agendamentos existentes para o veterinário na data
        if veterinario_id:
            agendamentos = Agendamento.objects.filter(
                data=data_agendamento,
                veterinario_id=veterinario_id,
                horario__isnull=False
            ).exclude(
                status='cancelado'
            )
        else:
            # Sem veterinário específico, não filtrar por agendamentos
            agendamentos = []
        
        # Remover horários ocupados
        horarios_ocupados = set()
        for agendamento in agendamentos:
            if agendamento.horario:
                # Marcar o horário de início como ocupado
                horarios_ocupados.add(agendamento.horario)
                
                # Marcar também os slots durante a duração do agendamento
                hora_inicio = datetime.combine(data_agendamento, agendamento.horario)
                hora_fim_ag = hora_inicio + timedelta(minutes=agendamento.duracao_minutos)
                
                slot_atual = hora_inicio
                while slot_atual < hora_fim_ag:
                    horarios_ocupados.add(slot_atual.time())
                    slot_atual += timedelta(minutes=15)
        
        # Filtrar slots disponíveis
        horarios_finais = [
            h.strftime('%H:%M') 
            for h in slots_disponiveis 
            if h not in horarios_ocupados
        ]
        
        return JsonResponse({
            'horarios': horarios_finais,
            'horario_inicio': horario_inicio.strftime('%H:%M'),
            'horario_fim': horario_fim.strftime('%H:%M')
        })
        
    except ValueError:
        return JsonResponse({'error': 'Data inválida'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def get_dias_fechados_api(request):
    """API para retornar os dias da semana em que a clínica está fechada"""
    try:
        # Buscar todos os horários de funcionamento ativos
        horarios_ativos = HorarioFuncionamento.objects.filter(ativo=True).values_list('dia_semana', flat=True)
        
        # Dias da semana: 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta, 5=Sábado, 6=Domingo
        todos_dias = set(range(7))
        dias_abertos = set(horarios_ativos)
        dias_fechados = list(todos_dias - dias_abertos)
        
        # Converter para formato JavaScript: 0=Domingo, 1=Segunda, ..., 6=Sábado
        # HorarioFuncionamento: 0=Segunda, ..., 6=Domingo
        # Precisamos mapear: Segunda(0) -> 1, Terça(1) -> 2, ..., Domingo(6) -> 0
        dias_fechados_js = [(dia + 1) % 7 for dia in dias_fechados]
        
        return JsonResponse({
            'dias_fechados': dias_fechados_js,
            'message': 'Dias fechados carregados com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def imprimir_fila_view(request):
    """View para gerar PDF de impressão de uma fila específica"""
    try:
        from weasyprint import HTML, CSS
        from django.conf import settings
        import os
        
        fila_id = request.GET.get('fila_id')
        data_str = request.GET.get('data')
        
        if not fila_id or not data_str:
            return JsonResponse({'error': 'Parâmetros fila_id e data são obrigatórios'}, status=400)
        
        # Buscar fila
        fila = get_object_or_404(FilaAtendimento, id=fila_id)
        
        # Converter data
        data_agendamento = datetime.strptime(data_str, '%Y-%m-%d').date()
        
        # Buscar agendamentos da fila nesse dia
        agendamentos = Agendamento.objects.filter(
            fila_id=fila_id,
            data=data_agendamento
        ).exclude(status='cancelado').order_by('horario', 'ordem')
        
        # Buscar dados da unidade para logo
        from cadastros.models import DadosUnidade
        try:
            dados_unidade = DadosUnidade.objects.first()
        except:
            dados_unidade = None
        
        context = {
            'fila': fila,
            'data': data_agendamento,
            'agendamentos': agendamentos,
            'dados_unidade': dados_unidade,
            'usuario': request.user,
            'data_impressao': timezone.now(),
            'is_pdf': True  # Flag para indicar que é geração de PDF
        }
        
        # Renderizar template como string
        html_string = render_to_string('scheduling/imprimir_fila.html', context, request=request)
        
        # Gerar PDF
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf_file = html.write_pdf()
        
        # Criar resposta HTTP com PDF
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="agenda_{fila.nome}_{data_agendamento.strftime("%Y%m%d")}.pdf"'
        
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

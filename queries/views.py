from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q
from datetime import date, datetime, timedelta

from medical_records.models import DoseVacinaRegistro, ProtocoloVacinaRegistro, Atendimento
from patients.models import Pet
from clients.models import Client


@login_required
def vacinacao_view(request):
    """Página de consulta de vacinação"""
    try:
        from cadastros.models import ProtocoloVacina
        protocolos = ProtocoloVacina.objects.select_related('vacina').order_by('vacina__nome', 'nome')
    except Exception:
        protocolos = []
    return render(request, 'queries/vacinacao.html', {'protocolos': protocolos})


@login_required
def aniversarios_view(request):
    """Página de consulta de aniversários"""
    return render(request, 'queries/aniversarios.html', {})


@login_required
@require_GET
def api_vacinacao(request):
    """API para buscar doses de vacina com filtros"""
    data_inicio_str = request.GET.get('data_inicio', '')
    data_fim_str = request.GET.get('data_fim', '')
    status_filtro = request.GET.get('status', '')
    tipo_filtro = request.GET.get('tipo', '')
    protocolo_id = request.GET.get('protocolo_id', '')

    hoje = date.today()

    try:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date() if data_inicio_str else hoje
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date() if data_fim_str else hoje + timedelta(days=6)
    except ValueError:
        data_inicio = hoje
        data_fim = hoje + timedelta(days=6)

    qs = DoseVacinaRegistro.objects.select_related(
        'protocolo_registro__pet__tutor',
        'protocolo_registro__protocolo__vacina',
    ).filter(
        data_programada__range=(data_inicio, data_fim)
    )

    if status_filtro == 'programada':
        qs = qs.filter(data_aplicacao__isnull=True, data_programada__gte=hoje)
    elif status_filtro == 'aplicada':
        qs = qs.filter(data_aplicacao__isnull=False)
    elif status_filtro == 'atrasada':
        qs = qs.filter(data_aplicacao__isnull=True, data_programada__lt=hoje)

    if protocolo_id:
        qs = qs.filter(protocolo_registro__protocolo__id=protocolo_id)

    if tipo_filtro in ('vacinas', 'antiparasitario', 'vermifugos'):
        try:
            qs = qs.filter(protocolo_registro__protocolo__vacina__tipo=tipo_filtro)
        except Exception:
            pass

    qs = qs.order_by('data_programada', 'protocolo_registro__pet__tutor__nome_completo')

    resultados = []
    for dose in qs:
        pet = dose.protocolo_registro.pet
        tutor = pet.tutor
        protocolo = dose.protocolo_registro.protocolo
        vacina = protocolo.vacina

        status_label = 'Aplicada' if dose.data_aplicacao else ('Atrasada' if dose.data_programada < hoje else 'Programada')
        status_class = 'aplicada' if dose.data_aplicacao else ('atrasada' if dose.data_programada < hoje else 'programada')

        aplicacao_str = ''
        if dose.data_aplicacao:
            aplicacao_str = dose.data_aplicacao.strftime('%d/%m/%Y %H:%M')

        resultados.append({
            'id': dose.id,
            'data_programada': dose.data_programada.strftime('%d/%m/%Y'),
            'cliente_nome': tutor.nome_completo,
            'cliente_codigo': getattr(tutor, 'codigo', ''),
            'animal_nome': pet.nome,
            'animal_codigo': getattr(pet, 'codigo', ''),
            'vacina_nome': vacina.nome,
            'tipo': vacina.tipo,
            'tipo_display': vacina.get_tipo_display(),
            'protocolo_nome': protocolo.nome,
            'numero_dose': dose.numero_dose,
            'qtd_doses': protocolo.aplicacao,
            'status': status_class,
            'status_label': status_label,
            'data_aplicacao': aplicacao_str,
            'telefone': getattr(tutor, 'telefone', '') or '',
            'animal_id': pet.id,
        })

    return JsonResponse({
        'success': True,
        'resultados': resultados,
        'total': len(resultados),
        'data_inicio': data_inicio.strftime('%d/%m/%Y'),
        'data_fim': data_fim.strftime('%d/%m/%Y'),
    })


@login_required
@require_GET
def api_vacinacao_resumo(request):
    """API para resumo de vacinação (contadores por status)"""
    data_inicio_str = request.GET.get('data_inicio', '')
    data_fim_str = request.GET.get('data_fim', '')

    hoje = date.today()
    try:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date() if data_inicio_str else hoje
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date() if data_fim_str else hoje + timedelta(days=6)
    except ValueError:
        data_inicio = hoje
        data_fim = hoje + timedelta(days=6)

    qs = DoseVacinaRegistro.objects.filter(data_programada__range=(data_inicio, data_fim))
    total = qs.count()
    aplicadas = qs.filter(data_aplicacao__isnull=False).count()
    programadas = qs.filter(data_aplicacao__isnull=True).count()
    atrasadas = qs.filter(data_aplicacao__isnull=True, data_programada__lt=hoje).count()

    return JsonResponse({
        'success': True,
        'total': total,
        'aplicadas': aplicadas,
        'programadas': programadas,
        'atrasadas': atrasadas,
    })


@login_required
@require_GET
def api_aniversarios(request):
    """API para buscar aniversariantes — retorna eventos para o calendário"""
    data_inicio_str = request.GET.get('data_inicio', '')
    data_fim_str = request.GET.get('data_fim', '')
    tipo = request.GET.get('tipo', 'todos')           # todos | pessoas | animais
    filtro_visita = request.GET.get('filtro_visita', 'ultimos_2_anos')

    hoje = date.today()
    try:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date() if data_inicio_str else hoje
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date() if data_fim_str else hoje + timedelta(days=30)
    except ValueError:
        data_inicio = hoje
        data_fim = hoje + timedelta(days=30)

    # Data-limite para filtro de última visita
    _meses = {'ultimos_3_meses': 3, 'ultimos_6_meses': 6}
    _anos  = {'ultimo_ano': 1, 'ultimos_2_anos': 2, 'ultimos_3_anos': 3, 'ultimos_5_anos': 5}
    filtro_data = None
    if filtro_visita in _meses:
        filtro_data = hoje - timedelta(days=30 * _meses[filtro_visita])
    elif filtro_visita in _anos:
        try:
            filtro_data = hoje.replace(year=hoje.year - _anos[filtro_visita])
        except ValueError:
            filtro_data = hoje - timedelta(days=365 * _anos[filtro_visita])

    # IDs de pets/tutores com visita no período exigido
    pets_com_visita = None
    tutores_com_visita = None
    if filtro_data:
        pets_com_visita = set(
            Atendimento.objects.filter(data_hora__date__gte=filtro_data)
            .values_list('pet_id', flat=True).distinct()
        )
        tutores_com_visita = set(
            Atendimento.objects.filter(data_hora__date__gte=filtro_data)
            .values_list('pet__tutor_id', flat=True).distinct()
        )

    eventos = []

    # ── Animais ──────────────────────────────────────────────────────────────
    if tipo in ('todos', 'animais'):
        pets_qs = Pet.objects.select_related('tutor', 'especie').filter(
            data_nascimento__isnull=False,
            status='vivo',
        )
        if pets_com_visita is not None:
            pets_qs = pets_qs.filter(id__in=pets_com_visita)

        for pet in pets_qs:
            dn = pet.data_nascimento
            for year in range(data_inicio.year, data_fim.year + 1):
                try:
                    bd = dn.replace(year=year)
                except ValueError:
                    bd = date(year, 2, 28)
                if data_inicio <= bd <= data_fim:
                    idade = year - dn.year
                    eventos.append({
                        'id': f'animal_{pet.id}_{year}',
                        'title': pet.nome,
                        'start': bd.isoformat(),
                        'end': (bd + timedelta(days=1)).isoformat(),
                        'allDay': True,
                        'backgroundColor': '#4dabf7',
                        'borderColor': '#339af0',
                        'textColor': '#fff',
                        'extendedProps': {
                            'tipo': 'animal',
                            'animal_id': pet.id,
                            'animal_nome': pet.nome,
                            'especie': pet.especie.nome if pet.especie else '',
                            'cliente_nome': pet.tutor.nome_completo,
                            'cliente_id': pet.tutor.id,
                            'idade': idade,
                            'url': f'/atendimento/animal/{pet.id}/',
                        },
                    })

    # ── Pessoas ───────────────────────────────────────────────────────────────
    if tipo in ('todos', 'pessoas'):
        clientes_qs = Client.objects.filter(
            data_aniversario__isnull=False,
            ativo=True,
        )
        if tutores_com_visita is not None:
            clientes_qs = clientes_qs.filter(id__in=tutores_com_visita)

        for cliente in clientes_qs:
            da = cliente.data_aniversario
            for year in range(data_inicio.year, data_fim.year + 1):
                try:
                    bd = da.replace(year=year)
                except ValueError:
                    bd = date(year, 2, 28)
                if data_inicio <= bd <= data_fim:
                    idade = year - da.year
                    eventos.append({
                        'id': f'pessoa_{cliente.id}_{year}',
                        'title': cliente.nome_completo,
                        'start': bd.isoformat(),
                        'end': (bd + timedelta(days=1)).isoformat(),
                        'allDay': True,
                        'backgroundColor': '#1971c2',
                        'borderColor': '#1864ab',
                        'textColor': '#fff',
                        'extendedProps': {
                            'tipo': 'pessoa',
                            'cliente_id': cliente.id,
                            'cliente_nome': cliente.nome_completo,
                            'idade': idade,
                            'url': f'/clientes/{cliente.id}/',
                        },
                    })

    return JsonResponse({'success': True, 'events': eventos, 'total': len(eventos)})


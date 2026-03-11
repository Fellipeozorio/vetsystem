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
    
    return render(request, 'medical_records/atendimento_clinico_form.html', context)


# API Views para registros da timeline

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime
import json
from .models import (
    Atendimento, Peso, Patologia, Documento, Exame, ExameArquivo,
    Foto, FotoArquivo, VacinaRegistro, Receita, Observacao, Video, Internacao
)


@require_http_methods(["POST"])
@login_required
def salvar_atendimento(request, pet_id):
    """Salvar novo atendimento clínico"""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        
        # Parse data e hora
        data_hora_str = request.POST.get('data_hora')
        if data_hora_str:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
        else:
            data_hora = timezone.now()
        
        # Criar atendimento
        atendimento = Atendimento.objects.create(
            pet=pet,
            tipo_atendimento_id=request.POST.get('tipo_atendimento_id'),
            data_hora=data_hora,
            observacoes=request.POST.get('observacoes', ''),
            detalhes=request.POST.get('detalhes', ''),
            obs_retorno=request.POST.get('obs_retorno', ''),
            usuario=request.user
        )
        
        # Processar datas de retorno
        if request.POST.get('data_retorno'):
            atendimento.data_retorno = request.POST.get('data_retorno')
        if request.POST.get('hora_retorno'):
            atendimento.hora_retorno = request.POST.get('hora_retorno')
        
        # Processar arquivo se enviado
        if 'arquivo' in request.FILES:
            atendimento.arquivo = request.FILES['arquivo']
        
        atendimento.save()
        
        return JsonResponse({
            'success': True,
            'id': atendimento.id,
            'message': 'Atendimento salvo com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@login_required
def salvar_peso(request, pet_id):
    """Salvar registro de peso"""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        
        data_hora_str = request.POST.get('data_hora')
        if data_hora_str:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
        else:
            data_hora = timezone.now()
        
        peso = Peso.objects.create(
            pet=pet,
            data_hora=data_hora,
            peso=request.POST.get('peso'),
            condicao_corporal=request.POST.get('condicao_corporal', ''),
            observacoes=request.POST.get('observacoes', ''),
            usuario=request.user
        )
        
        return JsonResponse({
            'success': True,
            'id': peso.id,
            'message': 'Peso salvo com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@login_required
def salvar_patologia(request, pet_id):
    """Salvar registro de patologia"""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        
        data_hora_str = request.POST.get('data_hora')
        if data_hora_str:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
        else:
            data_hora = timezone.now()
        
        patologia = Patologia.objects.create(
            pet=pet,
            data_hora=data_hora,
            diagnostico=request.POST.get('diagnostico'),
            cid=request.POST.get('cid', ''),
            gravidade=request.POST.get('gravidade', ''),
            observacoes=request.POST.get('observacoes', ''),
            usuario=request.user
        )
        
        return JsonResponse({
            'success': True,
            'id': patologia.id,
            'message': 'Patologia salva com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@login_required
def salvar_documento(request, pet_id):
    """Salvar documento"""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        
        data_hora_str = request.POST.get('data_hora')
        if data_hora_str:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
        else:
            data_hora = timezone.now()
        
        documento = Documento.objects.create(
            pet=pet,
            data_hora=data_hora,
            tipo=request.POST.get('tipo', ''),
            titulo=request.POST.get('titulo'),
            descricao=request.POST.get('descricao', ''),
            arquivo=request.FILES.get('arquivo'),
            usuario=request.user
        )
        
        return JsonResponse({
            'success': True,
            'id': documento.id,
            'message': 'Documento salvo com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@login_required
def salvar_exame(request, pet_id):
    """Salvar exame"""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        
        data_hora_str = request.POST.get('data_hora')
        if data_hora_str:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
        else:
            data_hora = timezone.now()
        
        exame = Exame.objects.create(
            pet=pet,
            data_hora=data_hora,
            tipo=request.POST.get('tipo', ''),
            nome=request.POST.get('nome'),
            resultado=request.POST.get('resultado', ''),
            usuario=request.user
        )
        
        # Processar arquivos múltiplos
        arquivos = request.FILES.getlist('arquivos')
        for arquivo in arquivos:
            ExameArquivo.objects.create(
                exame=exame,
                arquivo=arquivo
            )
        
        return JsonResponse({
            'success': True,
            'id': exame.id,
            'message': 'Exame salvo com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@login_required
def salvar_fotos(request, pet_id):
    """Salvar fotos"""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        
        data_hora_str = request.POST.get('data_hora')
        if data_hora_str:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
        else:
            data_hora = timezone.now()
        
        foto = Foto.objects.create(
            pet=pet,
            data_hora=data_hora,
            titulo=request.POST.get('titulo'),
            descricao=request.POST.get('descricao', ''),
            usuario=request.user
        )
        
        # Processar múltiplas fotos
        arquivos = request.FILES.getlist('arquivos')
        for arquivo in arquivos:
            FotoArquivo.objects.create(
                foto=foto,
                arquivo=arquivo
            )
        
        return JsonResponse({
            'success': True,
            'id': foto.id,
            'message': 'Fotos salvas com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@login_required
def salvar_vacina(request, pet_id):
    """Salvar vacina"""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        
        data_hora_str = request.POST.get('data_hora')
        if data_hora_str:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
        else:
            data_hora = timezone.now()
        
        vacina = VacinaRegistro.objects.create(
            pet=pet,
            data_hora=data_hora,
            nome=request.POST.get('nome'),
            lote=request.POST.get('lote', ''),
            fabricante=request.POST.get('fabricante', ''),
            observacoes=request.POST.get('observacoes', ''),
            usuario=request.user
        )
        
        if request.POST.get('proxima_dose'):
            vacina.proxima_dose = request.POST.get('proxima_dose')
            vacina.save()
        
        return JsonResponse({
            'success': True,
            'id': vacina.id,
            'message': 'Vacina salva com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@login_required
def salvar_receita(request, pet_id):
    """Salvar receita"""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        
        data_hora_str = request.POST.get('data_hora')
        if data_hora_str:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
        else:
            data_hora = timezone.now()
        
        receita = Receita.objects.create(
            pet=pet,
            data_hora=data_hora,
            tipo=request.POST.get('tipo', ''),
            prescricao=request.POST.get('prescricao'),
            observacoes=request.POST.get('observacoes', ''),
            usuario=request.user
        )
        
        if request.POST.get('validade'):
            receita.validade = request.POST.get('validade')
            receita.save()
        
        return JsonResponse({
            'success': True,
            'id': receita.id,
            'message': 'Receita salva com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@login_required
def salvar_observacao(request, pet_id):
    """Salvar observação"""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        
        data_hora_str = request.POST.get('data_hora')
        if data_hora_str:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
        else:
            data_hora = timezone.now()
        
        observacao = Observacao.objects.create(
            pet=pet,
            data_hora=data_hora,
            titulo=request.POST.get('titulo'),
            texto=request.POST.get('texto'),
            categoria=request.POST.get('categoria', ''),
            usuario=request.user
        )
        
        return JsonResponse({
            'success': True,
            'id': observacao.id,
            'message': 'Observação salva com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@login_required
def salvar_video(request, pet_id):
    """Salvar vídeo"""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        
        data_hora_str = request.POST.get('data_hora')
        if data_hora_str:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
        else:
            data_hora = timezone.now()
        
        video = Video.objects.create(
            pet=pet,
            data_hora=data_hora,
            titulo=request.POST.get('titulo'),
            descricao=request.POST.get('descricao', ''),
            arquivo=request.FILES.get('arquivo'),
            usuario=request.user
        )
        
        return JsonResponse({
            'success': True,
            'id': video.id,
            'message': 'Vídeo salvo com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@login_required
def salvar_internacao(request, pet_id):
    """Salvar internação"""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        
        data_hora_str = request.POST.get('data_hora')
        if data_hora_str:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
        else:
            data_hora = timezone.now()
        
        internacao = Internacao.objects.create(
            pet=pet,
            data_hora=data_hora,
            status=request.POST.get('status'),
            gravidade=request.POST.get('gravidade', ''),
            motivo=request.POST.get('motivo'),
            data_entrada=request.POST.get('data_entrada'),
            observacoes=request.POST.get('observacoes', ''),
            usuario=request.user
        )
        
        if request.POST.get('previsao_alta'):
            internacao.previsao_alta = request.POST.get('previsao_alta')
            internacao.save()
        
        return JsonResponse({
            'success': True,
            'id': internacao.id,
            'message': 'Internação salva com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["DELETE"])
@login_required
def deletar_registro(request, pet_id, tipo, registro_id):
    """Deletar registro da timeline"""
    try:
        # Mapear tipo para modelo
        modelos = {
            'atendimento': Atendimento,
            'peso': Peso,
            'patologia': Patologia,
            'documento': Documento,
            'exame': Exame,
            'fotos': Foto,
            'vacina': VacinaRegistro,
            'receita': Receita,
            'observacoes': Observacao,
            'video': Video,
            'internacao': Internacao
        }
        
        modelo = modelos.get(tipo)
        if not modelo:
            return JsonResponse({
                'success': False,
                'error': 'Tipo de registro inválido'
            }, status=400)
        
        # Buscar e deletar
        registro = get_object_or_404(modelo, id=registro_id, pet_id=pet_id)
        registro.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Registro excluído com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


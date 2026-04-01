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
    from cadastros.models import DadosUnidade
    
    pet = get_object_or_404(Pet, id=pet_id)
    
    # Buscar dados da clínica/unidade (singleton)
    try:
        clinica = DadosUnidade.objects.first()
    except DadosUnidade.DoesNotExist:
        clinica = None
    
    context = {
        'pet': pet,
        'cliente': pet.tutor,
        'clinica': clinica,
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
    """Salvar novo atendimento clínico ou atualizar existente"""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        
        # Verificar se é edição
        atendimento_id = request.POST.get('atendimento_id')
        if atendimento_id:
            atendimento = get_object_or_404(Atendimento, id=atendimento_id, pet=pet)
        else:
            atendimento = Atendimento(pet=pet, usuario=request.user)
        
        # Parse data e hora
        data_hora_str = request.POST.get('data_hora')
        if data_hora_str:
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
        else:
            data_hora = timezone.now()
        
        # Atualizar campos
        atendimento.tipo_atendimento_id = request.POST.get('tipo_atendimento_id')
        atendimento.data_hora = data_hora
        atendimento.observacoes = request.POST.get('observacoes', '')
        atendimento.detalhes = request.POST.get('detalhes', '')
        atendimento.obs_retorno = request.POST.get('obs_retorno', '')
        
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


@require_http_methods(["GET"])
@login_required
def listar_timeline(request, pet_id):
    """Listar todos os registros da timeline de um pet"""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        registros = []
        
        # Buscar todos os tipos de registros
        for atendimento in Atendimento.objects.filter(pet=pet).select_related('tipo_atendimento', 'usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'atendimento',
                'id': atendimento.id,
                'titulo': atendimento.observacoes or 'Atendimento',
                'descricao': atendimento.tipo_atendimento.nome if atendimento.tipo_atendimento else 'Atendimento',
                'data': atendimento.data_hora.isoformat(),
                'usuario': atendimento.usuario.get_full_name() or atendimento.usuario.username,
                'usuario_avatar': atendimento.usuario.userprofile.avatar.url if hasattr(atendimento.usuario, 'userprofile') and atendimento.usuario.userprofile.avatar else None
            })
        
        for peso in Peso.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'peso',
                'id': peso.id,
                'titulo': f'{peso.peso} kg',
                'descricao': peso.condicao_corporal or 'Peso registrado',
                'data': peso.data_hora.isoformat(),
                'usuario': peso.usuario.get_full_name() or peso.usuario.username,
                'usuario_avatar': peso.usuario.userprofile.avatar.url if hasattr(peso.usuario, 'userprofile') and peso.usuario.userprofile.avatar else None
            })
        
        for patologia in Patologia.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'patologia',
                'id': patologia.id,
                'titulo': patologia.diagnostico,
                'descricao': f'Gravidade: {patologia.gravidade}' if patologia.gravidade else 'Patologia registrada',
                'data': patologia.data_hora.isoformat(),
                'usuario': patologia.usuario.get_full_name() or patologia.usuario.username,
                'usuario_avatar': patologia.usuario.userprofile.avatar.url if hasattr(patologia.usuario, 'userprofile') and patologia.usuario.userprofile.avatar else None
            })
        
        for documento in Documento.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'documento',
                'id': documento.id,
                'titulo': documento.titulo,
                'descricao': f'Tipo: {documento.tipo}',
                'data': documento.data_hora.isoformat(),
                'usuario': documento.usuario.get_full_name() or documento.usuario.username,
                'usuario_avatar': documento.usuario.userprofile.avatar.url if hasattr(documento.usuario, 'userprofile') and documento.usuario.userprofile.avatar else None
            })
        
        for exame in Exame.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'exame',
                'id': exame.id,
                'titulo': exame.nome,
                'descricao': f'Tipo: {exame.tipo}',
                'data': exame.data_hora.isoformat(),
                'usuario': exame.usuario.get_full_name() or exame.usuario.username,
                'usuario_avatar': exame.usuario.userprofile.avatar.url if hasattr(exame.usuario, 'userprofile') and exame.usuario.userprofile.avatar else None
            })
        
        for foto in Foto.objects.filter(pet=pet).select_related('usuario').prefetch_related('arquivos').order_by('-data_hora'):
            num_arquivos = foto.arquivos.count()
            registros.append({
                'tipo': 'fotos',
                'id': foto.id,
                'titulo': foto.titulo,
                'descricao': f'{num_arquivos} foto(s)',
                'data': foto.data_hora.isoformat(),
                'usuario': foto.usuario.get_full_name() or foto.usuario.username,
                'usuario_avatar': foto.usuario.userprofile.avatar.url if hasattr(foto.usuario, 'userprofile') and foto.usuario.userprofile.avatar else None
            })
        
        for vacina in VacinaRegistro.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'vacina',
                'id': vacina.id,
                'titulo': vacina.nome,
                'descricao': f'Lote: {vacina.lote}' if vacina.lote else 'Vacina aplicada',
                'data': vacina.data_hora.isoformat(),
                'usuario': vacina.usuario.get_full_name() or vacina.usuario.username,
                'usuario_avatar': vacina.usuario.userprofile.avatar.url if hasattr(vacina.usuario, 'userprofile') and vacina.usuario.userprofile.avatar else None
            })
        
        for receita in Receita.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'receita',
                'id': receita.id,
                'titulo': f'Receita: {receita.tipo}',
                'descricao': receita.prescricao[:100] if receita.prescricao else 'Receita',
                'data': receita.data_hora.isoformat(),
                'usuario': receita.usuario.get_full_name() or receita.usuario.username,
                'usuario_avatar': receita.usuario.userprofile.avatar.url if hasattr(receita.usuario, 'userprofile') and receita.usuario.userprofile.avatar else None
            })
        
        for observacao in Observacao.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'observacoes',
                'id': observacao.id,
                'titulo': observacao.titulo,
                'descricao': observacao.texto[:100] if observacao.texto else 'Observação',
                'data': observacao.data_hora.isoformat(),
                'usuario': observacao.usuario.get_full_name() or observacao.usuario.username,
                'usuario_avatar': observacao.usuario.userprofile.avatar.url if hasattr(observacao.usuario, 'userprofile') and observacao.usuario.userprofile.avatar else None
            })
        
        for video in Video.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'video',
                'id': video.id,
                'titulo': video.titulo,
                'descricao': video.arquivo.name if video.arquivo else 'Vídeo',
                'data': video.data_hora.isoformat(),
                'usuario': video.usuario.get_full_name() or video.usuario.username,
                'usuario_avatar': video.usuario.userprofile.avatar.url if hasattr(video.usuario, 'userprofile') and video.usuario.userprofile.avatar else None
            })
        
        for internacao in Internacao.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'internacao',
                'id': internacao.id,
                'titulo': f'Internação: {internacao.status}',
                'descricao': internacao.motivo[:100] if internacao.motivo else 'Internação',
                'data': internacao.data_hora.isoformat(),
                'usuario': internacao.usuario.get_full_name() or internacao.usuario.username,
                'usuario_avatar': internacao.usuario.userprofile.avatar.url if hasattr(internacao.usuario, 'userprofile') and internacao.usuario.userprofile.avatar else None
            })
        
        # Ordenar todos os registros por data (mais recente primeiro)
        registros.sort(key=lambda x: x['data'], reverse=True)
        
        return JsonResponse({
            'success': True,
            'registros': registros
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["GET"])
@login_required
def obter_registro(request, pet_id, tipo, registro_id):
    """Obter detalhes de um registro específico para edição"""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        
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
        
        # Buscar registro
        registro = get_object_or_404(modelo, id=registro_id, pet_id=pet_id)
        
        # Montar dados de resposta baseado no tipo
        dados = {
            'success': True,
            'tipo': tipo,
            'id': registro.id,
            'data_hora': registro.data_hora.strftime('%Y-%m-%dT%H:%M') if hasattr(registro, 'data_hora') else None
        }
        
        # Dados específicos por tipo
        if tipo == 'atendimento':
            dados.update({
                'tipo_atendimento_id': registro.tipo_atendimento_id,
                'observacoes': registro.observacoes or '',
                'detalhes': registro.detalhes or '',
                'obs_retorno': registro.obs_retorno or '',
                'data_retorno': registro.data_retorno or '',
                'hora_retorno': registro.hora_retorno or ''
            })
        elif tipo == 'peso':
            dados.update({
                'peso': str(registro.peso),
                'condicao_corporal': registro.condicao_corporal or '',
                'observacoes': registro.observacoes or ''
            })
        elif tipo == 'patologia':
            dados.update({
                'diagnostico': registro.diagnostico,
                'cid': registro.cid or '',
                'gravidade': registro.gravidade or '',
                'observacoes': registro.observacoes or ''
            })
        elif tipo == 'documento':
            dados.update({
                'tipo_doc': registro.tipo or '',
                'titulo': registro.titulo,
                'descricao': registro.descricao or ''
            })
        elif tipo == 'exame':
            dados.update({
                'tipo_exame': registro.tipo or '',
                'nome': registro.nome,
                'resultado': registro.resultado or ''
            })
        elif tipo == 'fotos':
            dados.update({
                'titulo': registro.titulo,
                'descricao': registro.descricao or ''
            })
        elif tipo == 'vacina':
            dados.update({
                'nome': registro.nome,
                'lote': registro.lote or '',
                'fabricante': registro.fabricante or '',
                'proxima_dose': registro.proxima_dose or '',
                'observacoes': registro.observacoes or ''
            })
        elif tipo == 'receita':
            dados.update({
                'tipo_receita': registro.tipo or '',
                'prescricao': registro.prescricao,
                'validade': registro.validade or '',
                'observacoes': registro.observacoes or ''
            })
        elif tipo == 'observacoes':
            dados.update({
                'titulo': registro.titulo,
                'texto': registro.texto,
                'categoria': registro.categoria or ''
            })
        elif tipo == 'video':
            dados.update({
                'titulo': registro.titulo,
                'descricao': registro.descricao or ''
            })
        elif tipo == 'internacao':
            dados.update({
                'status': registro.status,
                'gravidade': registro.gravidade or '',
                'motivo': registro.motivo,
                'data_entrada': registro.data_entrada,
                'previsao_alta': registro.previsao_alta or '',
                'observacoes': registro.observacoes or ''
            })
        
        return JsonResponse(dados)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from patients.models import Pet
from clients.models import Client
from cadastros.models import Especie, Raca, Pelagem, Patologia as PatologiaCadastro, ModeloDocumento as ModeloDocumentoCadastro


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
            data_hora = timezone.make_aware(datetime.strptime(data_hora_str[:16], '%Y-%m-%dT%H:%M'))
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
            data_hora = timezone.make_aware(datetime.strptime(data_hora_str[:16], '%Y-%m-%dT%H:%M'))
        else:
            data_hora = timezone.now()
        
        peso_id = request.POST.get('peso_id')
        peso_valor = request.POST.get('peso', '').replace(',', '.')
        if peso_id:
            peso = get_object_or_404(Peso, id=peso_id, pet=pet)
            peso.data_hora = data_hora
            peso.peso = peso_valor
            peso.observacoes = request.POST.get('observacoes', '')
            peso.save()
        else:
            peso = Peso.objects.create(
                pet=pet,
                data_hora=data_hora,
                peso=peso_valor,
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
            data_hora = timezone.make_aware(datetime.strptime(data_hora_str[:16], '%Y-%m-%dT%H:%M'))
        else:
            data_hora = timezone.now()
        
        patologia_id = request.POST.get('patologia_id')
        patologia_cadastro_id = request.POST.get('patologia_cadastro_id')
        patologia_cadastro = None
        diagnostico_nome = request.POST.get('diagnostico', '')
        if patologia_cadastro_id:
            patologia_cadastro = get_object_or_404(PatologiaCadastro, id=patologia_cadastro_id)
            diagnostico_nome = patologia_cadastro.nome

        if patologia_id:
            patologia = get_object_or_404(Patologia, id=patologia_id, pet=pet)
            patologia.data_hora = data_hora
            patologia.diagnostico = diagnostico_nome
            patologia.patologia_cadastro = patologia_cadastro
            patologia.cid = request.POST.get('cid', '')
            patologia.gravidade = request.POST.get('gravidade', '')
            patologia.observacoes = request.POST.get('observacoes', '')
            patologia.save()
        else:
            patologia = Patologia.objects.create(
                pet=pet,
                data_hora=data_hora,
                diagnostico=diagnostico_nome,
                patologia_cadastro=patologia_cadastro,
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
            data_hora = timezone.make_aware(datetime.strptime(data_hora_str[:16], '%Y-%m-%dT%H:%M'))
        else:
            data_hora = timezone.now()

        modelo_documento_id = request.POST.get('modelo_documento_id') or None
        modelo = None
        if modelo_documento_id:
            modelo = ModeloDocumentoCadastro.objects.filter(id=modelo_documento_id, ativo=True).first()

        conteudo = request.POST.get('conteudo', '')
        titulo = request.POST.get('titulo', '') or (modelo.nome if modelo else '')

        documento_id = request.POST.get('documento_id')
        if documento_id:
            documento = get_object_or_404(Documento, id=documento_id, pet=pet)
            documento.data_hora = data_hora
            documento.modelo_documento = modelo
            documento.conteudo = conteudo
            documento.titulo = titulo
            documento.save()
        else:
            documento = Documento.objects.create(
                pet=pet,
                data_hora=data_hora,
                modelo_documento=modelo,
                conteudo=conteudo,
                titulo=titulo,
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
            data_hora = timezone.make_aware(datetime.strptime(data_hora_str[:16], '%Y-%m-%dT%H:%M'))
        else:
            data_hora = timezone.now()
        
        exame_id = request.POST.get('exame_id')
        if exame_id:
            exame = get_object_or_404(Exame, id=exame_id, pet=pet)
            exame.data_hora = data_hora
            exame.tipo = request.POST.get('tipo', '')
            exame.nome = request.POST.get('nome')
            exame.resultado = request.POST.get('resultado', '')
            exame.save()
        else:
            exame = Exame.objects.create(
                pet=pet,
                data_hora=data_hora,
                tipo=request.POST.get('tipo', ''),
                nome=request.POST.get('nome'),
                resultado=request.POST.get('resultado', ''),
                usuario=request.user
            )

        # Processar arquivos múltiplos (sempre adiciona, não substitui)
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
            data_hora = timezone.make_aware(datetime.strptime(data_hora_str[:16], '%Y-%m-%dT%H:%M'))
        else:
            data_hora = timezone.now()
        
        fotos_id = request.POST.get('fotos_id')
        if fotos_id:
            foto = get_object_or_404(Foto, id=fotos_id, pet=pet)
            foto.data_hora = data_hora
            foto.titulo = request.POST.get('titulo')
            foto.descricao = request.POST.get('descricao', '')
            foto.save()
        else:
            foto = Foto.objects.create(
                pet=pet,
                data_hora=data_hora,
                titulo=request.POST.get('titulo'),
                descricao=request.POST.get('descricao', ''),
                usuario=request.user
            )

        # Processar múltiplas fotos (sempre adiciona, não substitui)
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
            data_hora = timezone.make_aware(datetime.strptime(data_hora_str[:16], '%Y-%m-%dT%H:%M'))
        else:
            data_hora = timezone.now()
        
        vacina_id = request.POST.get('vacina_id')
        if vacina_id:
            vacina = get_object_or_404(VacinaRegistro, id=vacina_id, pet=pet)
            vacina.data_hora = data_hora
            vacina.nome = request.POST.get('nome')
            vacina.lote = request.POST.get('lote', '')
            vacina.fabricante = request.POST.get('fabricante', '')
            vacina.observacoes = request.POST.get('observacoes', '')
            vacina.proxima_dose = request.POST.get('proxima_dose') or None
            vacina.save()
        else:
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
            data_hora = timezone.make_aware(datetime.strptime(data_hora_str[:16], '%Y-%m-%dT%H:%M'))
        else:
            data_hora = timezone.now()
        
        receita_id = request.POST.get('receita_id')
        if receita_id:
            receita = get_object_or_404(Receita, id=receita_id, pet=pet)
            receita.data_hora = data_hora
            receita.tipo = request.POST.get('tipo', '')
            receita.prescricao = request.POST.get('prescricao')
            receita.observacoes = request.POST.get('observacoes', '')
            receita.validade = request.POST.get('validade') or None
            receita.save()
        else:
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
            data_hora = timezone.make_aware(datetime.strptime(data_hora_str[:16], '%Y-%m-%dT%H:%M'))
        else:
            data_hora = timezone.now()
        
        observacoes_id = request.POST.get('observacoes_id')
        if observacoes_id:
            observacao = get_object_or_404(Observacao, id=observacoes_id, pet=pet)
            observacao.data_hora = data_hora
            observacao.titulo = request.POST.get('titulo')
            observacao.texto = request.POST.get('texto')
            observacao.categoria = request.POST.get('categoria', '')
            observacao.save()
        else:
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
            data_hora = timezone.make_aware(datetime.strptime(data_hora_str[:16], '%Y-%m-%dT%H:%M'))
        else:
            data_hora = timezone.now()
        
        video_id = request.POST.get('video_id')
        if video_id:
            video = get_object_or_404(Video, id=video_id, pet=pet)
            video.data_hora = data_hora
            video.titulo = request.POST.get('titulo')
            video.descricao = request.POST.get('descricao', '')
            if 'arquivo' in request.FILES:
                video.arquivo = request.FILES['arquivo']
            video.save()
        else:
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
            data_hora = timezone.make_aware(datetime.strptime(data_hora_str[:16], '%Y-%m-%dT%H:%M'))
        else:
            data_hora = timezone.now()
        
        internacao_id = request.POST.get('internacao_id')
        if internacao_id:
            internacao = get_object_or_404(Internacao, id=internacao_id, pet=pet)
            internacao.data_hora = data_hora
            internacao.status = request.POST.get('status')
            internacao.gravidade = request.POST.get('gravidade', '')
            internacao.motivo = request.POST.get('motivo')
            if request.POST.get('data_entrada'):
                internacao.data_entrada = request.POST.get('data_entrada')
            internacao.previsao_alta = request.POST.get('previsao_alta') or None
            internacao.observacoes = request.POST.get('observacoes', '')
            internacao.save()
        else:
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
                'data': timezone.localtime(atendimento.data_hora).isoformat(),
                'usuario': atendimento.usuario.get_full_name() or atendimento.usuario.username,
                'usuario_avatar': atendimento.usuario.userprofile.avatar.url if hasattr(atendimento.usuario, 'userprofile') and atendimento.usuario.userprofile.avatar else None
            })
        
        for peso in Peso.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'peso',
                'id': peso.id,
                'titulo': f'{peso.peso} kg',
                'descricao': f"{str(peso.peso).replace('.', ',')} kg",
                'data': timezone.localtime(peso.data_hora).isoformat(),
                'usuario': peso.usuario.get_full_name() or peso.usuario.username,
                'usuario_avatar': peso.usuario.userprofile.avatar.url if hasattr(peso.usuario, 'userprofile') and peso.usuario.userprofile.avatar else None
            })
        
        for patologia in Patologia.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'patologia',
                'id': patologia.id,
                'titulo': patologia.diagnostico,
                'descricao': f'Gravidade: {patologia.gravidade}' if patologia.gravidade else 'Patologia registrada',
                'data': timezone.localtime(patologia.data_hora).isoformat(),
                'usuario': patologia.usuario.get_full_name() or patologia.usuario.username,
                'usuario_avatar': patologia.usuario.userprofile.avatar.url if hasattr(patologia.usuario, 'userprofile') and patologia.usuario.userprofile.avatar else None
            })
        
        for documento in Documento.objects.filter(pet=pet).select_related('usuario', 'modelo_documento').order_by('-data_hora'):
            registros.append({
                'tipo': 'documento',
                'id': documento.id,
                'titulo': documento.modelo_documento.nome if documento.modelo_documento else documento.titulo,
                'descricao': documento.modelo_documento.nome if documento.modelo_documento else 'Documento',
                'data': timezone.localtime(documento.data_hora).isoformat(),
                'usuario': documento.usuario.get_full_name() or documento.usuario.username,
                'usuario_avatar': documento.usuario.userprofile.avatar.url if hasattr(documento.usuario, 'userprofile') and documento.usuario.userprofile.avatar else None
            })
        
        for exame in Exame.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'exame',
                'id': exame.id,
                'titulo': exame.nome,
                'descricao': f'Tipo: {exame.tipo}',
                'data': timezone.localtime(exame.data_hora).isoformat(),
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
                'data': timezone.localtime(foto.data_hora).isoformat(),
                'usuario': foto.usuario.get_full_name() or foto.usuario.username,
                'usuario_avatar': foto.usuario.userprofile.avatar.url if hasattr(foto.usuario, 'userprofile') and foto.usuario.userprofile.avatar else None
            })
        
        for vacina in VacinaRegistro.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'vacina',
                'id': vacina.id,
                'titulo': vacina.nome,
                'descricao': f'Lote: {vacina.lote}' if vacina.lote else 'Vacina aplicada',
                'data': timezone.localtime(vacina.data_hora).isoformat(),
                'usuario': vacina.usuario.get_full_name() or vacina.usuario.username,
                'usuario_avatar': vacina.usuario.userprofile.avatar.url if hasattr(vacina.usuario, 'userprofile') and vacina.usuario.userprofile.avatar else None
            })
        
        for receita in Receita.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'receita',
                'id': receita.id,
                'titulo': f'Receita: {receita.tipo}',
                'descricao': receita.prescricao[:100] if receita.prescricao else 'Receita',
                'data': timezone.localtime(receita.data_hora).isoformat(),
                'usuario': receita.usuario.get_full_name() or receita.usuario.username,
                'usuario_avatar': receita.usuario.userprofile.avatar.url if hasattr(receita.usuario, 'userprofile') and receita.usuario.userprofile.avatar else None
            })
        
        for observacao in Observacao.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'observacoes',
                'id': observacao.id,
                'titulo': observacao.titulo,
                'descricao': observacao.texto[:100] if observacao.texto else 'Observação',
                'data': timezone.localtime(observacao.data_hora).isoformat(),
                'usuario': observacao.usuario.get_full_name() or observacao.usuario.username,
                'usuario_avatar': observacao.usuario.userprofile.avatar.url if hasattr(observacao.usuario, 'userprofile') and observacao.usuario.userprofile.avatar else None
            })
        
        for video in Video.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'video',
                'id': video.id,
                'titulo': video.titulo,
                'descricao': video.arquivo.name if video.arquivo else 'Vídeo',
                'data': timezone.localtime(video.data_hora).isoformat(),
                'usuario': video.usuario.get_full_name() or video.usuario.username,
                'usuario_avatar': video.usuario.userprofile.avatar.url if hasattr(video.usuario, 'userprofile') and video.usuario.userprofile.avatar else None
            })
        
        for internacao in Internacao.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'internacao',
                'id': internacao.id,
                'titulo': f'Internação: {internacao.status}',
                'descricao': internacao.motivo[:100] if internacao.motivo else 'Internação',
                'data': timezone.localtime(internacao.data_hora).isoformat(),
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
            'data_hora': timezone.localtime(registro.data_hora).strftime('%Y-%m-%dT%H:%M') if hasattr(registro, 'data_hora') else None
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
                'patologia_cadastro_id': registro.patologia_cadastro_id or '',
                'patologia_cadastro_descricao': registro.patologia_cadastro.descricao if registro.patologia_cadastro and registro.patologia_cadastro.descricao else '',
                'cid': registro.cid or '',
                'gravidade': registro.gravidade or '',
                'observacoes': registro.observacoes or ''
            })
        elif tipo == 'documento':
            dados.update({
                'modelo_documento_id': registro.modelo_documento_id or '',
                'conteudo': registro.conteudo or '',
                'titulo': registro.titulo or ''
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


@require_http_methods(["POST"])
@login_required
def imprimir_documento_view(request):
    """Gera PDF de documento usando xhtml2pdf a partir dos dados enviados via POST JSON."""
    try:
        from xhtml2pdf import pisa
        from io import BytesIO
        import base64
        import os
        import re
        from django.utils import timezone as tz

        data = json.loads(request.body)
        modelo   = data.get('modelo', {})
        pet      = data.get('pet', {})
        cliente  = data.get('cliente', {})
        dc       = data.get('clinica', {})
        conteudo = data.get('conteudo', '')
        encerramento = data.get('encerramento', '')
        agora = tz.localtime(tz.now())

        # ── Logo em base64 (evita problemas com xhtml2pdf acessando URL relativa) ──
        logo_tag = ''
        try:
            from cadastros.models import DadosUnidade
            du = DadosUnidade.objects.first()
            if du and du.logomarca:
                logo_path = du.logomarca.path
                if os.path.exists(logo_path):
                    ext = os.path.splitext(logo_path)[1].lower().lstrip('.')
                    mime = 'jpeg' if ext in ('jpg', 'jpeg') else ext
                    with open(logo_path, 'rb') as f:
                        logo_bytes = f.read()
                    b64 = base64.b64encode(logo_bytes).decode()
                    try:
                        from PIL import Image as _PILImg
                        from io import BytesIO as _PILBuf
                        _pil = _PILImg.open(_PILBuf(logo_bytes))
                        _iw, _ih = _pil.size
                        _scale = min(120 / _iw, 60 / _ih, 1.0)
                        _lw, _lh = int(_iw * _scale), int(_ih * _scale)
                        logo_tag = f'<img src="data:image/{mime};base64,{b64}" width="{_lw}" height="{_lh}">'
                    except Exception:
                        logo_tag = f'<img src="data:image/{mime};base64,{b64}" style="max-width:120px;max-height:80px;">'
        except Exception:
            pass

        # ── Cabeçalho ──
        fones  = ' / '.join(filter(None, [dc.get('telefone'), dc.get('celular')]))
        end_parts = [dc.get('endereco'), dc.get('bairro')]
        if dc.get('cidade') and dc.get('estado'):
            end_parts.append(f"{dc['cidade']}/{dc['estado']}")
        elif dc.get('cidade') or dc.get('estado'):
            end_parts.append(dc.get('cidade') or dc.get('estado'))
        end_str = ', '.join(filter(None, end_parts))

        mc = modelo.get('modelo_cabecalho', 0)
        if mc == 1:
            cab_html = f'''<table width="100%" style="border:0.5px solid #ccc;margin-bottom:8px;"><tr>
                <td style="padding:3px 4px;vertical-align:top;">{logo_tag}</td>
                <td style="padding:3px 4px;vertical-align:top;" align="right">
                    <p style="font-size:19px;font-weight:bold;color:#333;margin:0 0 1px 0;">{dc.get("nome","")}</p>
                    <p style="font-size:13px;color:#666;margin:0 0 0.3px 0;">{end_str}</p>
                    {f'<p style="font-size:13px;color:#666;margin:0 0 0.3px 0;">{fones}</p>' if fones else ''}
                </td>
            </tr></table>'''
        elif mc == 2:
            cab_html = f'''<table width="100%" style="border:0.5px solid #ccc;margin-bottom:8px;"><tr>
                <td style="padding:3px 4px;vertical-align:top;">{logo_tag}</td>
                <td style="padding:3px 4px;vertical-align:top;" align="right">
                    <p style="font-size:19px;font-weight:bold;color:#333;margin:0 0 1px 0;">{dc.get("nome","")}</p>
                    {f'<p style="font-size:13px;color:#666;margin:0 0 0.3px 0;">{dc["cnpj"]}</p>' if dc.get("cnpj") else ''}
                    {f'<p style="font-size:13px;color:#666;margin:0 0 0.3px 0;">{dc["crmv"]}</p>' if dc.get("crmv") else ''}
                    <p style="font-size:13px;color:#666;margin:0 0 0.3px 0;">{end_str}</p>
                    {f'<p style="font-size:13px;color:#666;margin:0 0 0.3px 0;">{fones}</p>' if fones else ''}
                    {f'<p style="font-size:13px;color:#666;margin:0;">{dc["email"]}</p>' if dc.get("email") else ''}
                </td>
            </tr></table>'''
        elif mc == 3:
            cab_html = f'<table width="100%" style="border:0.5px solid #ccc;margin-bottom:8px;"><tr><td style="padding:3px 4px;text-align:center;">{logo_tag}</td></tr></table>'
        else:
            cab_html = ''

        # ── Idade do animal ──
        idade_animal = 'não informada'
        if pet.get('data_nascimento'):
            from datetime import date
            try:
                nasc = date.fromisoformat(pet['data_nascimento'])
                hoje = agora.date()
                anos  = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
                meses = (hoje.month - nasc.month) % 12
                txt = ''
                if anos > 0:
                    txt = f"{anos} {'anos' if anos > 1 else 'ano'}"
                if meses > 0:
                    txt += (' e ' if txt else '') + f"{meses} {'meses' if meses > 1 else 'mês'}"
                idade_animal = txt or 'Menos de 1 mês'
            except Exception:
                pass
        elif pet.get('idade_estimada'):
            idade_animal = f"{pet['idade_estimada']} ano(s) estimado(s)"

        # ── Info paciente ──
        mip = modelo.get('modelo_info_paciente', 0)
        if mip == 1:
            info_html = f'''<table width="100%" style="border:0.5px solid #ccc;margin-bottom:30px;"><tr>
                <td width="50%" style="padding:3px 5px;vertical-align:top;">
                    <p style="font-size:13px;font-weight:600;color:#333;margin:0;line-height:1;">Dados do Animal</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Nome:</b> {pet.get("nome","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Espécie:</b> {pet.get("especie_nome","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Raça:</b> {pet.get("raca_nome","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Sexo:</b> {pet.get("sexo_display","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Idade:</b> {idade_animal}</p>
                </td>
                <td width="50%" style="padding:3px 5px;vertical-align:top;">
                    <p style="font-size:13px;font-weight:600;color:#333;margin:0;line-height:1;">Responsável</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Nome:</b> {cliente.get("nome_completo","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>CPF:</b> {cliente.get("cpf","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Celular:</b> {cliente.get("celular","")}</p>
                </td>
            </tr></table>'''
        elif mip == 2:
            info_html = f'''<table width="100%" style="border:0.5px solid #ccc;margin-bottom:30px;"><tr>
                <td width="50%" style="padding:3px 5px;vertical-align:top;">
                    <p style="font-size:13px;font-weight:600;color:#333;margin:0;line-height:1;">Dados do Animal</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Nome:</b> {pet.get("nome","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Espécie:</b> {pet.get("especie_nome","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Raça:</b> {pet.get("raca_nome","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Sexo:</b> {pet.get("sexo_display","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Idade:</b> {idade_animal}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Peso:</b> {pet.get("peso","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Microchip:</b> {pet.get("microchip","")}</p>
                </td>
                <td width="50%" style="padding:3px 5px;vertical-align:top;">
                    <p style="font-size:13px;font-weight:600;color:#333;margin:0;line-height:1;">Dados do Responsável</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Nome:</b> {cliente.get("nome_completo","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>CPF:</b> {cliente.get("cpf","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Celular:</b> {cliente.get("celular","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Endereço:</b> {cliente.get("endereco_completo","")}</p>
                    <p style="font-size:11px;color:#555;margin:0;line-height:1;"><b>Cidade/UF:</b> {cliente.get("cidade","")}/{cliente.get("estado","")}</p>
                </td>
            </tr></table>'''
        else:
            info_html = ''

        # ── Rodapé ──
        mr = modelo.get('modelo_rodape', 0)
        if mr == 1:
            rodape_html = f'''<table width="100%" style="border-top:1px solid #aaa;border-collapse:collapse;"><tr>
  <td style="font-size:12px;color:#666;padding:3px 0 0 0;">Impresso em: {agora.strftime("%d/%m/%Y")} às {agora.strftime("%H:%M")}</td>
  <td align="center" style="font-size:12px;color:#666;padding:3px 0 0 0;">Por: {request.user.get_full_name() or request.user.username}</td>
  <td align="right" style="font-size:12px;color:#666;padding:3px 0 0 0;">P&#225;gina <pdf:pagenumber/> de <pdf:pagecount/></td>
</tr></table>'''
        else:
            rodape_html = ''

        # ── HTML final ──
        nome_doc = modelo.get('nome', 'Documento')
        _titulo_table = f'<table width="100%" style="border:0.5px solid #ccc;margin-bottom:8px;"><tr><td style="padding:6px 8px;text-align:center;font-size:19px;font-weight:bold;text-transform:uppercase;color:#333;">{nome_doc}</td></tr></table>'
        if cab_html:
            # header: logo + small spacer + título (repetido em todas as páginas)
            _header_content = cab_html + '<div style="height:1mm;font-size:1px;line-height:1px;"> </div>' + _titulo_table
            # Adjust frame/margin to fit logo + title without creating large gap
            _header_frame_height = '44mm'
            _page_margin_top = '47mm'
        else:
            # apenas título no header
            _header_content = _titulo_table
            _header_frame_height = '20mm'
            _page_margin_top = '32mm'

        html = f'''<!DOCTYPE html>
<html xmlns:pdf="http://namespaces.reportlab.com/reportlab/html/pdf/1">
<head>
  <meta charset="UTF-8">
  <style>
    @page {{
      size: A4;
      margin: {_page_margin_top} 15mm 18mm 15mm;
            @frame header_frame {{
                -pdf-frame-content: header_content;
                left: 15mm;
                width: 180mm;
                top: 4mm;
                height: {_header_frame_height};
            }}
      @frame footer_frame {{
        -pdf-frame-content: footer_content;
        left: 15mm;
        width: 180mm;
        top: 279mm;
        height: 15mm;
      }}
    }}
    body {{ font-family: Helvetica, Arial, sans-serif; font-size: 13px; color: #333; line-height:0.5; }}
    table {{ border-collapse: collapse; }}
    td, th {{ border: none; vertical-align: top; padding: 0; }}
    p {{ margin: 0; }}
    #footer_content {{ font-size: 12px; color: #666; }}
  </style>
</head>
<body>
    <div id="header_content">{_header_content}</div>
    {info_html if info_html else ''}
  <div style="font-size:13px;margin-bottom:10px;">{conteudo}</div>
  {f'<div style="font-size:13px;">{encerramento}</div>' if encerramento else ''}
  {f'<div id="footer_content">{rodape_html}</div>' if rodape_html else ''}
</body>
</html>'''

        buffer = BytesIO()
        status = pisa.CreatePDF(html, dest=buffer, encoding='utf-8')
        if status.err:
            return JsonResponse({'error': 'Erro ao gerar PDF'}, status=500)

        # Monta nome de arquivo sanitizado
        _modelo_nome = (modelo.get('nome') if isinstance(modelo, dict) else None) or nome_doc or 'Documento'
        _animal_nome = (pet.get('nome') if isinstance(pet, dict) else '') or ''
        _file_base = re.sub(r'[\\/*?:"<>|]', '', f'{_modelo_nome} - {_animal_nome}'.strip())
        filename = f'{_file_base or "Documento"}.pdf'

        # Armazena PDF temporariamente no cache com token único;
        # o popup abre a URL /atendimento/pdf/<token>/<filename> onde o
        # Chrome lê o último segmento como nome do arquivo.
        import uuid as _uuid
        from django.core.cache import cache as _cache
        _token = str(_uuid.uuid4())
        buffer.seek(0)
        _cache.set(f'pdf_temp_{_token}', buffer.read(), timeout=300)
        from urllib.parse import quote as _quote
        pdf_url = f'/atendimento/pdf/{_token}/{_quote(filename)}'
        return JsonResponse({'url': pdf_url})

    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)


@login_required
def servir_pdf_temp_view(request, token, filename):
    """Serve PDF temporário armazenado em cache. A URL contém o nome real do arquivo
    para que o Chrome PDF viewer use esse nome ao salvar/baixar."""
    from django.core.cache import cache as _cache
    from django.http import HttpResponse
    import re as _re
    # Sanitiza token para evitar injeção de chave no cache
    if not _re.match(r'^[0-9a-f\-]{36}$', token):
        return HttpResponse('Inválido', status=400)
    pdf_bytes = _cache.get(f'pdf_temp_{token}')
    if not pdf_bytes:
        return HttpResponse('PDF não encontrado ou expirado.', status=404)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from patients.models import Pet
from clients.models import Client
from cadastros.models import Especie, Raca, Pelagem, Patologia as PatologiaCadastro, ModeloDocumento as ModeloDocumentoCadastro, ModeloReceita as ModeloReceitaCadastro


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
    from cadastros.models import DadosUnidade, Exame as ExameCadastro
    
    pet = get_object_or_404(Pet, id=pet_id)
    
    # Buscar dados da clínica/unidade (singleton)
    try:
        clinica = DadosUnidade.objects.first()
    except DadosUnidade.DoesNotExist:
        clinica = None
    
    exames_cadastro = ExameCadastro.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'pet': pet,
        'cliente': pet.tutor,
        'clinica': clinica,
        'exames_cadastro': exames_cadastro,
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
    Foto, FotoArquivo, VacinaRegistro, Receita, Observacao, ObservacaoAnexo, Video, Internacao,
    ProtocoloVacinaRegistro, DoseVacinaRegistro
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
        from cadastros.models import Exame as ExameCadastro
        pet = get_object_or_404(Pet, id=pet_id)
        
        data_hora_str = request.POST.get('data_hora')
        if data_hora_str:
            data_hora = timezone.make_aware(datetime.strptime(data_hora_str[:16], '%Y-%m-%dT%H:%M'))
        else:
            data_hora = timezone.now()
        
        exame_cadastro_id = request.POST.get('exame_cadastro_id') or None
        exame_cadastro = None
        nome = request.POST.get('nome', '')
        if exame_cadastro_id:
            exame_cadastro = ExameCadastro.objects.filter(pk=exame_cadastro_id).first()
            if exame_cadastro:
                nome = exame_cadastro.nome
        
        exame_id = request.POST.get('exame_id')
        campos = dict(
            data_hora=data_hora,
            tipo=request.POST.get('tipo', ''),
            nome=nome,
            resultado=request.POST.get('resultado', ''),
            exame_cadastro=exame_cadastro,
            itens_resultado=request.POST.get('itens_resultado', ''),
            conclusoes=request.POST.get('conclusoes', ''),
        )
        if exame_id:
            exame = get_object_or_404(Exame, id=exame_id, pet=pet)
            for k, v in campos.items():
                setattr(exame, k, v)
            exame.save()
        else:
            exame = Exame.objects.create(pet=pet, usuario=request.user, **campos)

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


@require_http_methods(["GET"])
@login_required
def obter_atributos_exame(request, pet_id, exame_id):
    """Retorna atributos de um exame com os valores de referência para a espécie/idade do pet."""
    try:
        from cadastros.models import Exame as ExameCadastro, AtributoExame, ReferenciaExame
        from datetime import date

        pet = get_object_or_404(Pet, id=pet_id)
        exame_cadastro = get_object_or_404(ExameCadastro, id=exame_id, ativo=True)

        # Calcular idade em meses
        idade_meses = 0
        if pet.data_nascimento:
            hoje = date.today()
            idade_meses = (hoje.year - pet.data_nascimento.year) * 12 + (hoje.month - pet.data_nascimento.month)

        # Espécie do pet (via raça)
        especie_id = None
        if pet.especie_id:
            especie_id = pet.especie_id
        elif hasattr(pet, 'raca') and pet.raca:
            especie_id = pet.raca.especie_id

        # Listar todas as referências do exame
        todas_referencias = list(
            ReferenciaExame.objects.filter(exame_id=exame_id)
            .order_by('especie__nome', 'nome')
            .values('id', 'nome')
        )
        exame_tem_referencia = len(todas_referencias) > 0

        # Determinar referência a usar: por referencia_id explícito ou auto-match espécie/idade
        referencia_id_param = request.GET.get('referencia_id')
        referencia = None
        if referencia_id_param:
            referencia = ReferenciaExame.objects.filter(
                id=referencia_id_param, exame_id=exame_id
            ).prefetch_related('itens__atributo').first()
        if not referencia and especie_id:
            referencia = ReferenciaExame.objects.filter(
                exame_id=exame_id,
                especie_id=especie_id,
                idade_inicial__lte=idade_meses,
                idade_final__gte=idade_meses,
            ).prefetch_related('itens__atributo').first()
        # Fallback: se ainda sem referência e não havia parâmetro explícito, usar a primeira disponível
        if not referencia and not referencia_id_param:
            referencia = ReferenciaExame.objects.filter(
                exame_id=exame_id
            ).prefetch_related('itens__atributo').order_by('id').first()

        # Mapear itens da referência por atributo_id
        ref_map = {}
        if referencia:
            for item in referencia.itens.all():
                ref_map[item.atributo_id] = {
                    'ref_inicio': item.ref_inicio or '',
                    'ref_fim': item.ref_fim or '',
                }

        atributos = AtributoExame.objects.filter(exame_id=exame_id, ativo=True).order_by('ordem', 'nome')
        resultado = []
        for a in atributos:
            ref = ref_map.get(a.id, {})
            resultado.append({
                'id': a.id,
                'nome': a.nome,
                'unidade': a.unidade or '',
                'tipo_dado': a.tipo_dado,
                'atributo_pai_id': a.atributo_pai_id,
                'ref_inicio': ref.get('ref_inicio', ''),
                'ref_fim': ref.get('ref_fim', ''),
            })

        return JsonResponse({
            'success': True,
            'exame_nome': exame_cadastro.nome,
            'referencia_id': referencia.id if referencia else None,
            'referencia_nome': referencia.nome if referencia else '',
            'exame_tem_referencia': exame_tem_referencia,
            'referencias': todas_referencias,
            'atributos': resultado,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


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

        # Processar múltiplos arquivos a remover
        ids_remover = request.POST.getlist('remover_arquivo')
        if ids_remover:
            FotoArquivo.objects.filter(id__in=ids_remover, foto=foto).delete()

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

        modelo_receita_id = request.POST.get('modelo_receita_id') or None
        modelo = None
        if modelo_receita_id:
            modelo = ModeloReceitaCadastro.objects.filter(id=modelo_receita_id, ativo=True).first()

        conteudo = request.POST.get('conteudo', '')

        receita_id = request.POST.get('receita_id')
        if receita_id:
            receita = get_object_or_404(Receita, id=receita_id, pet=pet)
            receita.data_hora = data_hora
            receita.modelo_receita = modelo
            receita.conteudo = conteudo
            receita.save()
        else:
            receita = Receita.objects.create(
                pet=pet,
                data_hora=data_hora,
                modelo_receita=modelo,
                conteudo=conteudo,
                usuario=request.user
            )

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

        titulo = request.POST.get('titulo', '')
        conteudo = request.POST.get('conteudo', '')

        observacoes_id = request.POST.get('observacoes_id')
        if observacoes_id:
            observacao = get_object_or_404(Observacao, id=observacoes_id, pet=pet)
            observacao.data_hora = data_hora
            observacao.titulo = titulo
            observacao.conteudo = conteudo
            observacao.save()
        else:
            observacao = Observacao.objects.create(
                pet=pet,
                data_hora=data_hora,
                titulo=titulo,
                conteudo=conteudo,
                usuario=request.user
            )

        # Processar anexos removidos
        anexos_remover = request.POST.get('anexos_remover', '')
        if anexos_remover:
            for anexo_id in anexos_remover.split(','):
                anexo_id = anexo_id.strip()
                if anexo_id:
                    try:
                        anexo = ObservacaoAnexo.objects.get(id=anexo_id, observacao=observacao)
                        anexo.arquivo.delete(save=False)
                        anexo.delete()
                    except ObservacaoAnexo.DoesNotExist:
                        pass

        # Processar novos anexos
        for arquivo in request.FILES.getlist('anexos'):
            ObservacaoAnexo.objects.create(
                observacao=observacao,
                arquivo=arquivo,
                nome_original=arquivo.name
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
            remover_arquivo = request.POST.get('remover_arquivo')
            if remover_arquivo and video.arquivo:
                video.arquivo.delete(save=False)
                video.arquivo = ''
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
        
        for exame in Exame.objects.filter(pet=pet).select_related('usuario', 'exame_cadastro').order_by('-data_hora'):
            exame_titulo = exame.nome or (exame.exame_cadastro.nome if exame.exame_cadastro else '') or exame.tipo or 'Exame'
            registros.append({
                'tipo': 'exame',
                'id': exame.id,
                'titulo': exame_titulo,
                'descricao': exame_titulo,
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
                'descricao': foto.titulo,
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
        
        for receita in Receita.objects.filter(pet=pet).select_related('usuario', 'modelo_receita').order_by('-data_hora'):
            titulo = receita.modelo_receita.nome if receita.modelo_receita else 'Receita'
            registros.append({
                'tipo': 'receita',
                'id': receita.id,
                'titulo': titulo,
                'descricao': titulo,
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
                'descricao': video.titulo,
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
        
        # Protocolos de vacina — um item por protocolo (não por dose)
        from datetime import datetime as _dt, date as _date
        today = timezone.localdate()
        for reg in ProtocoloVacinaRegistro.objects.filter(pet=pet).select_related(
            'protocolo__vacina', 'usuario'
        ).prefetch_related('doses').order_by('-data_inicial'):
            usuario_obj = reg.usuario
            vacina_nome = reg.protocolo.vacina.nome
            doses = list(reg.doses.all())

            # Calcular status do protocolo a partir das doses e do status do registro
            if reg.status == 'interrompida':
                status_display = 'Interrompida'
            elif not doses:
                status_display = 'Programada'
            elif all(d.data_aplicacao for d in doses):
                status_display = 'Aplicada'
            elif any(not d.data_aplicacao and d.data_programada < today for d in doses):
                status_display = 'Atrasada'
            else:
                status_display = 'Programada'

            # Dose de referência para o título (próxima pendente ou última aplicada)
            doses_nao_aplicadas = [d for d in doses if not d.data_aplicacao]
            if doses_nao_aplicadas:
                proximas = [d for d in doses_nao_aplicadas if d.data_programada >= today]
                dose_ref = min(proximas, key=lambda d: d.numero_dose) if proximas else min(doses_nao_aplicadas, key=lambda d: d.numero_dose)
            elif doses:
                dose_ref = max(doses, key=lambda d: d.numero_dose)
            else:
                dose_ref = None

            titulo_display = f'{vacina_nome} {dose_ref.numero_dose}° dose' if dose_ref else vacina_nome

            # Data do item: mais recente entre aplicadas; senão criado_em (horário de adicionado)
            datas_aplicacao = [d.data_aplicacao for d in doses if d.data_aplicacao]
            if datas_aplicacao:
                ref_dt = timezone.localtime(max(datas_aplicacao)).isoformat()
            else:
                ref_dt = timezone.localtime(reg.criado_em).isoformat()

            registros.append({
                'tipo': 'vacina-dose',
                'id': reg.id,
                'titulo': titulo_display,
                'descricao': status_display,
                'data': ref_dt,
                'usuario': usuario_obj.get_full_name() or usuario_obj.username,
                'usuario_avatar': usuario_obj.userprofile.avatar.url if hasattr(usuario_obj, 'userprofile') and usuario_obj.userprofile.avatar else None,
                'status': status_display.lower(),
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
def listar_agenda_pet(request, pet_id):
    """Retorna todos os agendamentos do pet para a aba Agenda."""
    from scheduling.models import Agendamento
    from datetime import datetime as _dt_cls, timedelta

    try:
        pet = get_object_or_404(Pet, id=pet_id)

        def _mins(delta):
            if delta is None:
                return None
            total = int(delta.total_seconds() // 60)
            return total if total >= 0 else None

        registros = []
        for a in Agendamento.objects.filter(animal=pet).select_related(
            'tipo_atendimento', 'veterinario', 'fila'
        ).order_by('-data', '-horario'):
            # Data/hora agendada
            if a.horario:
                data_hora_str = f"{a.data.strftime('%d/%m/%Y')} às {a.horario.strftime('%H:%M')}"
            else:
                data_hora_str = a.data.strftime('%d/%m/%Y')

            # Atraso: chegada - horário agendado
            atraso = None
            if a.horario and a.data_hora_chegada:
                agendado_dt = timezone.make_aware(
                    _dt_cls.combine(a.data, a.horario)
                )
                atraso = _mins(a.data_hora_chegada - agendado_dt)

            # Espera: início do atendimento - chegada
            espera = None
            if a.data_hora_chegada and a.data_hora_inicio_atendimento:
                espera = _mins(a.data_hora_inicio_atendimento - a.data_hora_chegada)

            # Atend.: fim - início do atendimento
            duracao_atend = None
            if a.data_hora_inicio_atendimento and a.data_hora_fim_atendimento:
                duracao_atend = _mins(a.data_hora_fim_atendimento - a.data_hora_inicio_atendimento)

            registros.append({
                'id': a.id,
                'data_hora': data_hora_str,
                'tipo': a.tipo_atendimento.nome if a.tipo_atendimento else '',
                'profissional': a.veterinario.get_full_name() if a.veterinario else '',
                'status': a.status,
                'status_display': a.get_status_display(),
                'atraso': atraso,
                'espera': espera,
                'atendimento': duracao_atend,
            })

        return JsonResponse({'success': True, 'registros': registros})

    except Exception as e:
        import traceback
        return JsonResponse({'success': False, 'error': str(e), 'trace': traceback.format_exc()}, status=400)


@require_http_methods(["GET"])
@login_required
def listar_timeline_completa(request, pet_id):
    """Retorna todos os registros com dados completos para a aba Linha do Tempo."""
    try:
        pet = get_object_or_404(Pet, id=pet_id)
        registros = []

        def _avatar(user):
            try:
                return user.userprofile.avatar.url if user.userprofile.avatar else None
            except Exception:
                return None

        def _usuario(user):
            return user.get_full_name() or user.username

        def _dt(dt):
            return timezone.localtime(dt).isoformat()

        # Atendimentos
        for r in Atendimento.objects.filter(pet=pet).select_related('tipo_atendimento', 'usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'atendimento',
                'id': r.id,
                'titulo': r.tipo_atendimento.nome if r.tipo_atendimento else 'Atendimento',
                'data': _dt(r.data_hora),
                'usuario': _usuario(r.usuario),
                'usuario_avatar': _avatar(r.usuario),
                'campos': [
                    {'label': 'Tipo', 'valor': r.tipo_atendimento.nome if r.tipo_atendimento else ''},
                    {'label': 'Observações', 'valor': r.observacoes or '', 'html': True},
                    {'label': 'Detalhes', 'valor': r.detalhes or '', 'html': True},
                    {'label': 'Retorno', 'valor': str(r.data_retorno.strftime('%d/%m/%Y') if r.data_retorno else '')},
                    {'label': 'Obs. Retorno', 'valor': r.obs_retorno or ''},
                ],
            })

        # Pesos
        for r in Peso.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'peso',
                'id': r.id,
                'titulo': f'{str(r.peso).replace(".", ",")} kg',
                'data': _dt(r.data_hora),
                'usuario': _usuario(r.usuario),
                'usuario_avatar': _avatar(r.usuario),
                'campos': [
                    {'label': 'Peso', 'valor': f'{str(r.peso).replace(".", ",")} kg'},
                    {'label': 'Condição Corporal', 'valor': r.condicao_corporal or ''},
                    {'label': 'Observações', 'valor': r.observacoes or ''},
                ],
            })

        # Patologias
        for r in Patologia.objects.filter(pet=pet).select_related('usuario', 'patologia_cadastro').order_by('-data_hora'):
            protocolo_padrao = (r.patologia_cadastro.descricao or '') if r.patologia_cadastro else ''
            registros.append({
                'tipo': 'patologia',
                'id': r.id,
                'titulo': r.diagnostico,
                'data': _dt(r.data_hora),
                'usuario': _usuario(r.usuario),
                'usuario_avatar': _avatar(r.usuario),
                'campos': [
                    {'label': 'Diagnóstico', 'valor': r.diagnostico},
                    {'label': 'CID', 'valor': r.cid or ''},
                    {'label': 'Gravidade', 'valor': r.gravidade or ''},
                    {'label': 'Protocolo padrão', 'valor': protocolo_padrao},
                    {'label': 'Observações', 'valor': r.observacoes or ''},
                ],
            })

        # Documentos
        for r in Documento.objects.filter(pet=pet).select_related('usuario', 'modelo_documento').order_by('-data_hora'):
            registros.append({
                'tipo': 'documento',
                'id': r.id,
                'titulo': r.modelo_documento.nome if r.modelo_documento else r.titulo or 'Documento',
                'data': _dt(r.data_hora),
                'usuario': _usuario(r.usuario),
                'usuario_avatar': _avatar(r.usuario),
                'campos': [
                    {'label': 'Modelo', 'valor': r.modelo_documento.nome if r.modelo_documento else r.titulo or ''},
                    {'label': 'Conteúdo', 'valor': r.conteudo or '', 'html': True},
                ],
            })

        # Exames
        from cadastros.models import ReferenciaExame as RefExameCadastro
        from datetime import date as _date
        import json as _json

        # Calcular idade do pet em meses (para buscar referência correta)
        _idade_meses = 0
        if pet.data_nascimento:
            _hoje = _date.today()
            _idade_meses = (_hoje.year - pet.data_nascimento.year) * 12 + (_hoje.month - pet.data_nascimento.month)
        _especie_id = pet.especie_id or (pet.raca.especie_id if hasattr(pet, 'raca') and pet.raca else None)

        for r in Exame.objects.filter(pet=pet).select_related('usuario', 'exame_cadastro').order_by('-data_hora'):
            # Montar tabela de itens resultado
            tabela_html = ''
            if r.itens_resultado:
                try:
                    itens = _json.loads(r.itens_resultado)
                    if itens:
                        # Buscar referências para este exame/pet
                        ref_map = {}
                        if r.exame_cadastro_id:
                            referencia = None
                            if _especie_id:
                                referencia = RefExameCadastro.objects.filter(
                                    exame_id=r.exame_cadastro_id,
                                    especie_id=_especie_id,
                                    idade_inicial__lte=_idade_meses,
                                    idade_final__gte=_idade_meses,
                                ).prefetch_related('itens__atributo').first()
                            if not referencia:
                                referencia = RefExameCadastro.objects.filter(
                                    exame_id=r.exame_cadastro_id
                                ).prefetch_related('itens__atributo').order_by('id').first()
                            if referencia:
                                for item in referencia.itens.all():
                                    ref_inicio = item.ref_inicio or ''
                                    ref_fim = item.ref_fim or ''
                                    if ref_inicio and ref_fim:
                                        ref_map[item.atributo_id] = f'{ref_inicio} – {ref_fim}'
                                    elif ref_inicio:
                                        ref_map[item.atributo_id] = ref_inicio
                                    elif ref_fim:
                                        ref_map[item.atributo_id] = ref_fim

                        linhas = ''
                        for item in itens:
                            nome = item.get('nome', '')
                            resultado_val = item.get('resultado', '')
                            unidade = item.get('unidade', '')
                            atributo_id = item.get('atributo_id')
                            ref_val = ref_map.get(atributo_id, '') if atributo_id else ''
                            resultado_com_unidade = f'{resultado_val} {unidade}'.strip() if unidade else resultado_val
                            linhas += (
                                f'<tr>'
                                f'<td style="padding:3px 6px;border:1px solid #dee2e6;">{nome}</td>'
                                f'<td style="padding:3px 6px;border:1px solid #dee2e6;">{resultado_com_unidade}</td>'
                                f'<td style="padding:3px 6px;border:1px solid #dee2e6;color:#6c757d;">{ref_val}</td>'
                                f'</tr>'
                            )
                        tabela_html = (
                            '<table style="width:100%;border-collapse:collapse;font-size:0.78rem;">'
                            '<thead><tr style="background:#f8f9fa;">'
                            '<th style="padding:3px 6px;border:1px solid #dee2e6;text-align:left;">Atributo</th>'
                            '<th style="padding:3px 6px;border:1px solid #dee2e6;text-align:left;">Resultado</th>'
                            '<th style="padding:3px 6px;border:1px solid #dee2e6;text-align:left;">Referência</th>'
                            '</tr></thead>'
                            f'<tbody>{linhas}</tbody>'
                            '</table>'
                        )
                except Exception:
                    pass

            campos = [
                {'label': 'Nome', 'valor': r.nome},
                {'label': 'Tipo', 'valor': r.tipo or ''},
            ]
            if tabela_html:
                campos.append({'label': 'Atributos', 'valor': tabela_html, 'html': True})
            if r.conclusoes:
                campos.append({'label': 'Conclusões', 'valor': r.conclusoes, 'html': True})

            registros.append({
                'tipo': 'exame',
                'id': r.id,
                'titulo': r.nome or r.tipo or 'Exame',
                'data': _dt(r.data_hora),
                'usuario': _usuario(r.usuario),
                'usuario_avatar': _avatar(r.usuario),
                'campos': campos,
            })

        # Fotos
        for r in Foto.objects.filter(pet=pet).select_related('usuario').prefetch_related('arquivos').order_by('-data_hora'):
            fotos_list = [a.arquivo.url for a in r.arquivos.all()]
            registros.append({
                'tipo': 'fotos',
                'id': r.id,
                'titulo': r.titulo,
                'data': _dt(r.data_hora),
                'usuario': _usuario(r.usuario),
                'usuario_avatar': _avatar(r.usuario),
                'campos': [
                    {'label': 'Título', 'valor': r.titulo},
                    {'label': 'Descrição', 'valor': r.descricao or ''},
                ],
                'fotos': fotos_list,
            })

        # Vacinas
        for r in VacinaRegistro.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'vacina',
                'id': r.id,
                'titulo': r.nome,
                'data': _dt(r.data_hora),
                'usuario': _usuario(r.usuario),
                'usuario_avatar': _avatar(r.usuario),
                'campos': [
                    {'label': 'Vacina', 'valor': r.nome},
                    {'label': 'Fabricante', 'valor': r.fabricante or ''},
                    {'label': 'Aplicação', 'valor': timezone.localtime(r.data_hora).strftime('%d/%m/%Y %H:%M')},
                    {'label': 'Lote', 'valor': r.lote or ''},
                    {'label': 'Próxima Dose', 'valor': r.proxima_dose.strftime('%d/%m/%Y') if r.proxima_dose else ''},
                    {'label': 'Observações', 'valor': r.observacoes or ''},
                ],
            })

        # Receitas
        for r in Receita.objects.filter(pet=pet).select_related('usuario', 'modelo_receita').order_by('-data_hora'):
            registros.append({
                'tipo': 'receita',
                'id': r.id,
                'titulo': r.modelo_receita.nome if r.modelo_receita else 'Receita',
                'data': _dt(r.data_hora),
                'usuario': _usuario(r.usuario),
                'usuario_avatar': _avatar(r.usuario),
                'campos': [
                    {'label': 'Modelo', 'valor': r.modelo_receita.nome if r.modelo_receita else ''},
                    {'label': 'Conteúdo', 'valor': r.conteudo or r.prescricao or '', 'html': True},
                ],
            })

        # Observações
        for r in Observacao.objects.filter(pet=pet).select_related('usuario').prefetch_related('anexos').order_by('-data_hora'):
            anexos_list = [
                {'url': a.arquivo.url, 'nome': a.nome_original or a.arquivo.name.split('/')[-1]}
                for a in r.anexos.all()
            ]
            registros.append({
                'tipo': 'observacoes',
                'id': r.id,
                'titulo': r.titulo,
                'data': _dt(r.data_hora),
                'usuario': _usuario(r.usuario),
                'usuario_avatar': _avatar(r.usuario),
                'campos': [
                    {'label': 'Título', 'valor': r.titulo},
                    {'label': 'Observação', 'valor': r.conteudo or r.texto or '', 'html': True},
                ],
                'anexos': anexos_list,
            })

        # Vídeos
        for r in Video.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            try:
                arquivo_url = r.arquivo.url if r.arquivo else ''
            except Exception:
                arquivo_url = ''
            registros.append({
                'tipo': 'video',
                'id': r.id,
                'titulo': r.titulo,
                'data': _dt(r.data_hora),
                'usuario': _usuario(r.usuario),
                'usuario_avatar': _avatar(r.usuario),
                'campos': [
                    {'label': 'Título', 'valor': r.titulo},
                    {'label': 'Descrição', 'valor': r.descricao or ''},
                ],
                'video_url': arquivo_url,
            })

        # Internações
        for r in Internacao.objects.filter(pet=pet).select_related('usuario').order_by('-data_hora'):
            registros.append({
                'tipo': 'internacao',
                'id': r.id,
                'titulo': f'Internação – {r.get_status_display() if hasattr(r, "get_status_display") else r.status}',
                'data': _dt(r.data_hora),
                'usuario': _usuario(r.usuario),
                'usuario_avatar': _avatar(r.usuario),
                'campos': [
                    {'label': 'Status', 'valor': r.status or ''},
                    {'label': 'Gravidade', 'valor': r.gravidade or ''},
                    {'label': 'Motivo', 'valor': r.motivo or ''},
                    {'label': 'Entrada', 'valor': str(r.data_entrada) if r.data_entrada else ''},
                    {'label': 'Previsão Alta', 'valor': str(r.previsao_alta) if r.previsao_alta else ''},
                    {'label': 'Observações', 'valor': r.observacoes or ''},
                ],
            })

        # Protocolos de vacina (aplicados via protocolo)
        today = timezone.localdate()
        for reg in ProtocoloVacinaRegistro.objects.filter(pet=pet).select_related(
            'protocolo__vacina', 'usuario'
        ).prefetch_related('doses').order_by('-data_inicial'):
            usuario_obj = reg.usuario
            vacina_nome = reg.protocolo.vacina.nome
            protocolo_nome = reg.protocolo.nome
            doses = list(reg.doses.all())

            if reg.status == 'interrompida':
                status_display = 'Interrompida'
            elif not doses:
                status_display = 'Programada'
            elif all(d.data_aplicacao for d in doses):
                status_display = 'Aplicada'
            elif any(not d.data_aplicacao and d.data_programada < today for d in doses):
                status_display = 'Atrasada'
            else:
                status_display = 'Programada'

            datas_aplicacao = [d.data_aplicacao for d in doses if d.data_aplicacao]
            if datas_aplicacao:
                ref_dt = timezone.localtime(max(datas_aplicacao)).isoformat()
            else:
                ref_dt = timezone.localtime(reg.criado_em).isoformat()

            # Frequency info
            aplicacao_val = reg.protocolo.aplicacao
            intervalo_dias = reg.protocolo.intervalo_dias
            if aplicacao_val == 'indeterminado':
                freq_text = f'Tempo indeterminado, a cada {intervalo_dias} dias'
            else:
                freq_text = f'{aplicacao_val} doses a cada {intervalo_dias} dias'

            # Doses table
            dose_rows = ''
            for d in sorted(doses, key=lambda x: x.numero_dose):
                prog = d.data_programada.strftime('%d/%m/%Y') if d.data_programada else ''
                aplic = timezone.localtime(d.data_aplicacao).strftime('%d/%m/%Y %H:%M') if d.data_aplicacao else ''
                dose_rows += (
                    f'<tr>'
                    f'<td>{d.numero_dose}\u00aa</td>'
                    f'<td>{prog}</td>'
                    f'<td>{aplic}</td>'
                    f'<td>{d.laboratorio or ""}</td>'
                    f'<td>{d.lote or ""}</td>'
                    f'<td></td>'
                    f'</tr>'
                )
            tabela_html = (
                f'<p style="margin:0 0 6px 0"><strong>Posologia:</strong> {freq_text}</p>'
                f'<table class="lt-exam-table"><thead><tr>'
                f'<th>Dose</th><th>Programa\u00e7\u00e3o</th><th>Aplica\u00e7\u00e3o</th>'
                f'<th>Laborat\u00f3rio</th><th>Lote</th><th>A\u00e7\u00f5es</th>'
                f'</tr></thead><tbody>{dose_rows}</tbody></table>'
            )

            try:
                avatar_url = usuario_obj.userprofile.avatar.url if usuario_obj.userprofile.avatar else None
            except Exception:
                avatar_url = None

            registros.append({
                'tipo': 'vacina-dose',
                'id': reg.id,
                'titulo': f'{vacina_nome} \u2013 {protocolo_nome}',
                'data': ref_dt,
                'usuario': usuario_obj.get_full_name() or usuario_obj.username,
                'usuario_avatar': avatar_url,
                'campos': [{'label': 'Doses', 'valor': tabela_html, 'html': True}],
                'status': status_display.lower(),
            })

        registros.sort(key=lambda x: x['data'], reverse=True)
        return JsonResponse({'success': True, 'registros': registros})

    except Exception as e:
        import traceback
        return JsonResponse({'success': False, 'error': str(e), 'trace': traceback.format_exc()}, status=400)


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
                'resultado': registro.resultado or '',
                'exame_cadastro_id': registro.exame_cadastro_id or '',
                'itens_resultado': registro.itens_resultado or '',
                'conclusoes': registro.conclusoes or '',
            })
        elif tipo == 'fotos':
            arquivos_fotos = [
                {'id': a.id, 'url': a.arquivo.url, 'nome': a.arquivo.name.split('/')[-1]}
                for a in registro.arquivos.all()
            ]
            dados.update({
                'titulo': registro.titulo,
                'descricao': registro.descricao or '',
                'arquivos': arquivos_fotos,
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
                'modelo_receita_id': registro.modelo_receita_id or '',
                'conteudo': registro.conteudo or '',
            })
        elif tipo == 'observacoes':
            anexos_list = [
                {'id': a.id, 'url': a.arquivo.url, 'nome': a.nome_original or a.arquivo.name.split('/')[-1]}
                for a in registro.anexos.all()
            ]
            dados.update({
                'titulo': registro.titulo,
                'conteudo': registro.conteudo or registro.texto or '',
                'anexos': anexos_list,
            })
        elif tipo == 'video':
            try:
                arquivo_url = registro.arquivo.url if registro.arquivo else ''
            except Exception:
                arquivo_url = ''
            try:
                arquivo_nome = registro.arquivo.name.split('/')[-1] if registro.arquivo else ''
            except Exception:
                arquivo_nome = ''
            dados.update({
                'titulo': registro.titulo,
                'descricao': registro.descricao or '',
                'arquivo_url': arquivo_url,
                'arquivo_nome': arquivo_nome,
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


@require_http_methods(["POST"])
@login_required
def imprimir_receita_view(request):
    """Gera PDF de receita usando xhtml2pdf (igual ao de documento)."""
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

        mr = modelo.get('modelo_rodape', 0)
        if mr == 1:
            rodape_html = f'''<table width="100%" style="border-top:1px solid #aaa;border-collapse:collapse;"><tr>
  <td style="font-size:12px;color:#666;padding:3px 0 0 0;">Impresso em: {agora.strftime("%d/%m/%Y")} às {agora.strftime("%H:%M")}</td>
  <td align="center" style="font-size:12px;color:#666;padding:3px 0 0 0;">Por: {request.user.get_full_name() or request.user.username}</td>
  <td align="right" style="font-size:12px;color:#666;padding:3px 0 0 0;">P&#225;gina <pdf:pagenumber/> de <pdf:pagecount/></td>
</tr></table>'''
        else:
            rodape_html = ''

        nome_doc = modelo.get('nome', 'Receita')
        _titulo_table = f'<table width="100%" style="border:0.5px solid #ccc;margin-bottom:0;"><tr><td style="padding:5px 8px;text-align:center;font-size:19px;font-weight:bold;text-transform:uppercase;color:#333;">RECEITA</td></tr></table>'
        if cab_html:
            _header_content = cab_html + '<div style="height:1mm;font-size:1px;line-height:1px;"> </div>' + _titulo_table
            _header_frame_height = '44mm'
            _page_margin_top = '38mm'
        else:
            _header_content = _titulo_table
            _header_frame_height = '13mm'
            _page_margin_top = '18mm'

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

        _modelo_nome = (modelo.get('nome') if isinstance(modelo, dict) else None) or nome_doc or 'Receita'
        _animal_nome = (pet.get('nome') if isinstance(pet, dict) else '') or ''
        _file_base = re.sub(r'[\\/*?:"<>|]', '', f'{_modelo_nome} - {_animal_nome}'.strip())
        filename = f'{_file_base or "Receita"}.pdf'

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


# ========== VACCINE PROTOCOL VIEWS ==========

@require_http_methods(["GET"])
@login_required
def listar_tipos_vacina(request, pet_id):
    """Retorna os tipos de vacina distintos que possuem protocolos cadastrados"""
    from cadastros.models import Vacina
    tipos_com_protocolo = (
        Vacina.objects
        .filter(ativo=True, protocolos__isnull=False)
        .values_list('tipo', flat=True)
        .distinct()
        .order_by('tipo')
    )
    # Mapeia valor -> label usando as choices do model
    choices_map = dict(Vacina.TIPO_CHOICES)
    resultado = [
        {'value': t, 'label': choices_map.get(t, t)}
        for t in tipos_com_protocolo
    ]
    return JsonResponse({'success': True, 'tipos': resultado})


def listar_vacinas_disponiveis(request, pet_id):
    """Lista vacinas e protocolos disponíveis para o pet, filtrados por tipo"""
    from cadastros.models import Vacina
    tipo = request.GET.get('tipo', '')

    vacinas = Vacina.objects.filter(ativo=True)
    if tipo:
        vacinas = vacinas.filter(tipo=tipo)

    resultados = []
    for vacina in vacinas.order_by('nome'):
        for protocolo in vacina.protocolos.order_by('nome'):
            resultados.append({
                'protocolo_id': protocolo.id,
                'vacina_nome': vacina.nome,
                'protocolo_nome': protocolo.nome,
                'aplicacao': protocolo.aplicacao,
                'intervalo_dias': protocolo.intervalo_dias,
                'label': f'{vacina.nome} — {protocolo.nome}',
            })

    return JsonResponse({'success': True, 'protocolos': resultados})


@require_http_methods(["GET"])
@login_required
def listar_protocolos_vacina(request, pet_id):
    """Lista registros de protocolos de vacina do pet"""
    pet = get_object_or_404(Pet, id=pet_id)
    registros = ProtocoloVacinaRegistro.objects.filter(pet=pet).select_related(
        'protocolo__vacina'
    ).order_by('-data_inicial')

    lista = []
    for r in registros:
        lista.append({
            'id': r.id,
            'vacina_nome': r.protocolo.vacina.nome,
            'protocolo_nome': r.protocolo.nome,
            'aplicacao': r.protocolo.aplicacao,
            'intervalo_dias': r.protocolo.intervalo_dias,
            'data_inicial': r.data_inicial.strftime('%d/%m/%Y'),
            'status': r.status,
        })

    return JsonResponse({'success': True, 'registros': lista})


@require_http_methods(["POST"])
@login_required
def salvar_protocolo_vacina(request, pet_id):
    """Criar novo registro de protocolo de vacina com doses"""
    from cadastros.models import ProtocoloVacina
    from datetime import date, timedelta
    pet = get_object_or_404(Pet, id=pet_id)

    protocolo_id = request.POST.get('protocolo_id')
    data_inicial_str = request.POST.get('data_inicial')

    if not protocolo_id or not data_inicial_str:
        return JsonResponse({'success': False, 'error': 'Campos obrigatórios não preenchidos'}, status=400)

    protocolo = get_object_or_404(ProtocoloVacina, id=protocolo_id)
    try:
        data_inicial = date.fromisoformat(data_inicial_str)
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Data inválida'}, status=400)

    registro = ProtocoloVacinaRegistro.objects.create(
        pet=pet,
        protocolo=protocolo,
        data_inicial=data_inicial,
        status='programada',
        usuario=request.user,
    )

    num_doses = int(protocolo.aplicacao) if protocolo.aplicacao != 'indeterminado' else 1
    for i in range(num_doses):
        data_dose = data_inicial + timedelta(days=protocolo.intervalo_dias * i)
        DoseVacinaRegistro.objects.create(
            protocolo_registro=registro,
            numero_dose=i + 1,
            data_programada=data_dose,
            status='programada',
        )

    return JsonResponse({
        'success': True,
        'id': registro.id,
        'message': 'Protocolo criado com sucesso!',
    })


@require_http_methods(["GET"])
@login_required
def detalhe_protocolo_vacina(request, pet_id, protocolo_id):
    """Detalhes de um registro de protocolo de vacina"""
    registro = get_object_or_404(ProtocoloVacinaRegistro, id=protocolo_id, pet_id=pet_id)
    protocolo = registro.protocolo

    doses = []
    for dose in registro.doses.all():
        doses.append({
            'id': dose.id,
            'numero_dose': dose.numero_dose,
            'data_programada': dose.data_programada.strftime('%d/%m/%Y'),
            'data_programada_iso': dose.data_programada.strftime('%Y-%m-%d'),
            'data_aplicacao': timezone.localtime(dose.data_aplicacao).strftime('%d/%m/%Y %H:%M') if dose.data_aplicacao else '',
            'data_aplicacao_iso': timezone.localtime(dose.data_aplicacao).strftime('%Y-%m-%dT%H:%M') if dose.data_aplicacao else '',
            'laboratorio': dose.laboratorio,
            'lote': dose.lote,
            'status': dose.status,
        })

    return JsonResponse({
        'success': True,
        'id': registro.id,
        'vacina_nome': protocolo.vacina.nome,
        'protocolo_nome': protocolo.nome,
        'aplicacao': protocolo.aplicacao,
        'intervalo_dias': protocolo.intervalo_dias,
        'data_inicial': registro.data_inicial.strftime('%d/%m/%Y'),
        'status': registro.status,
        'doses': doses,
    })


@require_http_methods(["POST"])
@login_required
def interromper_protocolo_vacina(request, pet_id, protocolo_id):
    """Interromper protocolo de vacina"""
    registro = get_object_or_404(ProtocoloVacinaRegistro, id=protocolo_id, pet_id=pet_id)
    registro.status = 'interrompida'
    registro.save()
    return JsonResponse({'success': True})


@require_http_methods(["POST"])
@login_required
def retomar_protocolo_vacina(request, pet_id, protocolo_id):
    """Retomar protocolo de vacina interrompido"""
    registro = get_object_or_404(ProtocoloVacinaRegistro, id=protocolo_id, pet_id=pet_id)
    registro.status = 'programada'
    registro.save()
    return JsonResponse({'success': True})


@require_http_methods(["POST", "DELETE"])
@login_required
def deletar_protocolo_vacina(request, pet_id, protocolo_id):
    """Excluir protocolo de vacina e suas doses"""
    registro = get_object_or_404(ProtocoloVacinaRegistro, id=protocolo_id, pet_id=pet_id)
    registro.delete()
    return JsonResponse({'success': True})


@require_http_methods(["POST"])
@login_required
def salvar_dose_vacina(request, pet_id, dose_id):
    """Salvar dados de uma dose de vacina (aplicação, laboratório, lote)"""
    dose = get_object_or_404(DoseVacinaRegistro, id=dose_id, protocolo_registro__pet_id=pet_id)

    data_aplicacao_str = request.POST.get('data_aplicacao', '')
    data_programada_str = request.POST.get('data_programada', '')
    dose.laboratorio = request.POST.get('laboratorio', '')
    dose.lote = request.POST.get('lote', '')

    if data_programada_str:
        try:
            from datetime import date as _date
            dose.data_programada = _date.fromisoformat(data_programada_str)
        except ValueError:
            pass

    if data_aplicacao_str:
        try:
            dose.data_aplicacao = timezone.make_aware(
                datetime.strptime(data_aplicacao_str[:16], '%Y-%m-%dT%H:%M')
            )
            dose.status = 'aplicada'
        except ValueError:
            pass
    else:
        dose.data_aplicacao = None
        dose.status = 'programada'

    dose.save()
    # Retornar dados atualizados para o JS atualizar o item na timeline
    vacina_nome = dose.protocolo_registro.protocolo.vacina.nome
    data_display = timezone.localtime(dose.data_aplicacao).isoformat() if dose.data_aplicacao else None
    return JsonResponse({
        'success': True,
        'message': 'Dose salva com sucesso!',
        'dose_id': dose.id,
        'vacina_nome': vacina_nome,
        'data_aplicacao_iso': data_display,
        'status': dose.status,
    })


@require_http_methods(["POST"])
@login_required
def excluir_dose_vacina(request, pet_id, dose_id):
    """Excluir uma dose de vacina de um protocolo"""
    dose = get_object_or_404(DoseVacinaRegistro, id=dose_id, protocolo_registro__pet_id=pet_id)
    dose.delete()
    return JsonResponse({'success': True})


@require_http_methods(["GET"])
@login_required
def detalhe_dose_vacina(request, pet_id, dose_id):
    """Detalhes de uma dose para preenchimento do formulário"""
    dose = get_object_or_404(DoseVacinaRegistro, id=dose_id, protocolo_registro__pet_id=pet_id)
    registro = dose.protocolo_registro
    protocolo = registro.protocolo
    usuario = registro.usuario

    return JsonResponse({
        'success': True,
        'id': dose.id,
        'protocolo_registro_id': registro.id,
        'vacina_nome': protocolo.vacina.nome,
        'protocolo_nome': protocolo.nome,
        'numero_dose': dose.numero_dose,
        'data_programada': dose.data_programada.strftime('%Y-%m-%d'),
        'data_programada_display': dose.data_programada.strftime('%d/%m/%Y'),
        'data_aplicacao': timezone.localtime(dose.data_aplicacao).strftime('%Y-%m-%dT%H:%M') if dose.data_aplicacao else '',
        'laboratorio': dose.laboratorio,
        'lote': dose.lote,
        'status': dose.status,
        'usuario': usuario.get_full_name() or usuario.username,
    })


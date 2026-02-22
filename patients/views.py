from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Pet
from clients.models import Client


@login_required
@require_http_methods(["POST"])
def pet_create_ajax(request):
    """Criar animal via AJAX."""
    try:
        # Dados obrigatórios
        tutor_id = request.POST.get('tutor_id')
        nome = request.POST.get('nome')
        sexo = request.POST.get('sexo')
        especie_id = request.POST.get('especie')
        
        if not all([tutor_id, nome, sexo, especie_id]):
            return JsonResponse({
                'success': False,
                'error': 'Campos obrigatórios não preenchidos'
            })
        
        # Buscar tutor
        tutor = get_object_or_404(Client, pk=tutor_id)
        
        # Criar animal
        pet = Pet()
        pet.tutor = tutor
        pet.nome = nome
        pet.sexo = sexo
        pet.especie_id = especie_id
        
        # Campos opcionais
        raca_id = request.POST.get('raca')
        if raca_id:
            pet.raca_id = raca_id
        
        pelagem_id = request.POST.get('pelagem')
        if pelagem_id:
            pet.pelagem_id = pelagem_id
        
        # Esterilização (não aplicar se sexo for indeterminado)
        esterilizacao = request.POST.get('esterilizacao')
        if esterilizacao and sexo != 'I':
            pet.esterilizacao = esterilizacao
        
        # Data de nascimento
        data_nascimento = request.POST.get('data_nascimento')
        if data_nascimento:
            pet.data_nascimento = data_nascimento
        
        # Microchip
        microchip = request.POST.get('microchip')
        if microchip:
            pet.microchip = microchip
        
        # Marcações
        marcacoes = request.POST.get('marcacoes')
        if marcacoes:
            pet.marcacoes = marcacoes
        
        # Pedigree
        pedigree = request.POST.get('pedigree') == 'true'
        pet.pedigree = pedigree
        
        numero_pedigree = request.POST.get('numero_pedigree')
        if numero_pedigree:
            pet.numero_pedigree = numero_pedigree
        
        # Foto (se enviada)
        if 'foto' in request.FILES:
            foto = request.FILES['foto']
            pet.foto = foto
        
        pet.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Animal {pet.nome} cadastrado com sucesso!',
            'pet_id': pet.id,
            'pet_codigo': pet.codigo
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def pet_detail_ajax(request, pet_id):
    """Retornar detalhes do animal via AJAX."""
    try:
        pet = get_object_or_404(Pet, pk=pet_id)
        
        # Preparar dados para retorno
        data = {
            'success': True,
            'pet': {
                'id': pet.id,
                'codigo': pet.codigo,
                'nome': pet.nome,
                'sexo': pet.sexo,
                'sexo_display': pet.get_sexo_display(),
                'esterilizacao': pet.esterilizacao,
                'data_nascimento': pet.data_nascimento.strftime('%d/%m/%Y') if pet.data_nascimento else None,
                'data_nascimento_raw': pet.data_nascimento.strftime('%Y-%m-%d') if pet.data_nascimento else None,
                'especie': pet.especie.nome if pet.especie else None,
                'especie_id': pet.especie.id if pet.especie else None,
                'raca': pet.raca.nome if pet.raca else None,
                'raca_id': pet.raca.id if pet.raca else None,
                'pelagem': pet.pelagem.nome if pet.pelagem else None,
                'pelagem_id': pet.pelagem.id if pet.pelagem else None,
                'microchip': pet.microchip,
                'marcacoes': pet.marcacoes,
                'marcacoes_list': pet.get_marcacoes_list(),
                'pedigree': pet.pedigree,
                'numero_pedigree': pet.numero_pedigree,
                'foto': pet.foto.url if pet.foto else None,
                'avatar_icon': pet.get_avatar_icon(),
                'status': pet.status,
                'tutor_id': pet.tutor.id,
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def pet_edit_ajax(request, pet_id):
    """Editar animal via AJAX."""
    try:
        pet = get_object_or_404(Pet, pk=pet_id)
        
        # Atualizar campos
        pet.nome = request.POST.get('nome', pet.nome)
        pet.sexo = request.POST.get('sexo', pet.sexo)
        pet.status = request.POST.get('status', pet.status)
        
        # Espécie (obrigatória)
        especie_id = request.POST.get('especie')
        if especie_id:
            pet.especie_id = especie_id
        
        # Campos opcionais
        raca_id = request.POST.get('raca')
        if raca_id:
            pet.raca_id = raca_id
        else:
            pet.raca = None
        
        pelagem_id = request.POST.get('pelagem')
        if pelagem_id:
            pet.pelagem_id = pelagem_id
        else:
            pet.pelagem = None
        
        # Esterilização
        esterilizacao = request.POST.get('esterilizacao')
        if esterilizacao and pet.sexo != 'I':
            pet.esterilizacao = esterilizacao
        else:
            pet.esterilizacao = None
        
        # Data de nascimento
        data_nascimento = request.POST.get('data_nascimento')
        if data_nascimento:
            pet.data_nascimento = data_nascimento
        else:
            pet.data_nascimento = None
        
        # Microchip
        pet.microchip = request.POST.get('microchip', '')
        
        # Marcações
        marcacoes = request.POST.get('marcacoes')
        if marcacoes:
            pet.marcacoes = marcacoes
        else:
            pet.marcacoes = ''
        
        # Pedigree
        pedigree = request.POST.get('pedigree') == 'true'
        pet.pedigree = pedigree
        
        numero_pedigree = request.POST.get('numero_pedigree')
        if numero_pedigree:
            pet.numero_pedigree = numero_pedigree
        else:
            pet.numero_pedigree = ''
        
        # Verificar se deve remover foto
        remove_foto = request.POST.get('remove_foto') == 'true'
        if remove_foto:
            if pet.foto:
                pet.foto.delete(save=False)  # Deletar arquivo físico
                pet.foto = None
        # Foto (se enviada nova)
        elif 'foto' in request.FILES:
            foto = request.FILES['foto']
            pet.foto = foto
        
        pet.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Animal {pet.nome} atualizado com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def pet_delete_ajax(request, pet_id):
    """Excluir animal via AJAX."""
    try:
        pet = get_object_or_404(Pet, pk=pet_id)
        pet_nome = pet.nome
        pet.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Animal {pet_nome} excluído com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def pet_transfer_ajax(request, pet_id):
    """Transferir animal para outro responsável via AJAX."""
    try:
        pet = get_object_or_404(Pet, pk=pet_id)
        novo_responsavel_id = request.POST.get('novo_responsavel')
        
        if not novo_responsavel_id:
            return JsonResponse({
                'success': False,
                'message': 'Novo responsável não informado'
            })
        
        # Buscar novo responsável
        novo_responsavel = get_object_or_404(Client, pk=novo_responsavel_id)
        
        # Guardar nome do responsável anterior para a mensagem
        responsavel_anterior = pet.tutor.nome_completo
        
        # Transferir
        pet.tutor = novo_responsavel
        pet.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Animal {pet.nome} transferido de {responsavel_anterior} para {novo_responsavel.nome_completo} com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

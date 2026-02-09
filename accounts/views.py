from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from .models import UserProfile
from .forms import UserProfileForm, UserEditForm, CustomPasswordChangeForm
from django.urls import reverse


def can_manage_users(user):
    """Verifica se o usuário tem permissão para gerenciar usuários"""
    required_perms = [
        'auth.add_permission',
        'auth.change_permission',
        'auth.delete_permission',
        'auth.view_permission'
    ]
    return user.is_superuser or user.has_perms(required_perms)


@login_required
def profile_view(request):
    """View para visualizar o perfil do usuário"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'user': request.user,
        'profile': profile,
        'can_manage_users': can_manage_users(request.user),
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile_view(request):
    """View para editar o perfil do usuário"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile, user=request.user)
    
    context = {
        'form': form,
        'profile': profile,
        'can_manage_users': can_manage_users(request.user),
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def change_password_view(request):
    """View para alterar a senha do usuário"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Sua senha foi alterada com sucesso!')
            return redirect('accounts:profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'can_manage_users': can_manage_users(request.user),
    }
    return render(request, 'accounts/change_password.html', context)


@login_required
def user_list_view(request):
    """View para listar e gerenciar usuários (apenas para quem tem permissão)"""
    
    # Verificar permissão
    if not can_manage_users(request.user):
        messages.error(request, 'Acesso restrito. Você não tem permissão para gerenciar usuários.')
        return redirect('accounts:profile')
    
    # Busca
    search = request.GET.get('search', '')
    users = User.objects.select_related('userprofile').all()
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Paginação
    paginator = Paginator(users.order_by('username'), 10)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)
    
    # Todos os grupos para o modal
    all_groups = Group.objects.all().order_by('name')
    
    context = {
        'users': users_page,
        'search': search,
        'all_groups': all_groups,
        'can_manage_users': True,
    }
    return render(request, 'accounts/user_list.html', context)


@login_required
def user_edit_view(request, user_id):
    """View para editar um usuário específico (apenas para quem tem permissão)"""
    
    # Verificar permissão
    if not can_manage_users(request.user):
        messages.error(request, 'Acesso restrito. Você não tem permissão para gerenciar usuários.')
        return redirect('accounts:profile')
    
    editing_user = get_object_or_404(User, pk=user_id)
    
    # Tentar obter o perfil existente
    try:
        profile = UserProfile.objects.get(user=editing_user)
    except UserProfile.DoesNotExist:
        # Se não existe perfil, usuário foi criado incorretamente
        messages.error(request, f'Usuário {editing_user.username} não possui perfil válido. Por favor, recrie o usuário.')
        return redirect('accounts:user_list')
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, request.FILES, instance=profile, editing_user=editing_user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuário {editing_user.username} atualizado com sucesso!')
            return redirect('accounts:user_list')
    else:
        form = UserEditForm(instance=profile, editing_user=editing_user)
    
    # Dados para os quadros de seleção
    all_groups = Group.objects.all().order_by('name')
    current_group = editing_user.groups.first()
    all_permissions = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')
    
    # Agrupar permissões por app
    permissions_by_app = {}
    for perm in all_permissions:
        app_label = perm.content_type.app_label
        if app_label not in permissions_by_app:
            permissions_by_app[app_label] = []
        permissions_by_app[app_label].append(perm)
    
    context = {
        'form': form,
        'editing_user': editing_user,
        'profile': profile,
        'all_groups': all_groups,
        'current_group': current_group,
        'all_permissions': all_permissions,
        'permissions_by_app': permissions_by_app,
        'user_permissions': editing_user.user_permissions.all(),
        'can_manage_users': True,
    }
    return render(request, 'accounts/user_edit.html', context)


@login_required
def get_group_permissions(request, group_id):
    """API para obter permissões de um grupo (AJAX)"""
    if not can_manage_users(request.user):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    try:
        group = Group.objects.get(pk=group_id)
        permissions = [{'id': perm.id, 'name': perm.name} for perm in group.permissions.all()]
        return JsonResponse({'permissions': permissions})
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Grupo não encontrado'}, status=404)


@login_required
def user_create_view(request):
    """View para criar um novo usuário"""
    
    # Verificar permissão
    if not can_manage_users(request.user):
        messages.error(request, 'Acesso restrito. Você não tem permissão para gerenciar usuários.')
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        # Criar usuário
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        if not username or not password:
            messages.error(request, 'Usuário e senha são obrigatórios.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, f'Já existe um usuário com o nome "{username}".')
        else:
            # Criar o usuário
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            
            # Criar perfil (será usado depois para adicionar CPF, etc)
            UserProfile.objects.create(user=user)
            
            messages.success(request, f'Usuário {username} criado com sucesso! Agora configure o perfil.')
            return redirect('accounts:user_edit', user_id=user.id)
    
    # Dados para o template
    all_groups = Group.objects.all().order_by('name')
    
    context = {
        'all_groups': all_groups,
        'can_manage_users': True,
    }
    return render(request, 'accounts/user_create.html', context)


@login_required
def check_user_permission(request):
    """View para verificar se o usuário tem permissão (usada pelo JavaScript)"""
    has_permission = can_manage_users(request.user)
    return JsonResponse({'has_permission': has_permission})


@login_required
def user_create_ajax(request):
    """View para criar usuário via AJAX com envio de email"""
    
    # Verificar permissão
    if not can_manage_users(request.user):
        return JsonResponse({'success': False, 'error': 'Você não tem permissão para criar usuários.'})
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        cpf = request.POST.get('cpf', '').strip()
        email = request.POST.get('email', '').strip()
        group_id = request.POST.get('group', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        # Validações
        if not username:
            return JsonResponse({'success': False, 'error': 'Nome de usuário é obrigatório.'})
        
        if not cpf:
            return JsonResponse({'success': False, 'error': 'CPF é obrigatório.'})
        
        if not email:
            return JsonResponse({'success': False, 'error': 'Email é obrigatório.'})
        
        if not group_id:
            return JsonResponse({'success': False, 'error': 'Grupo é obrigatório.'})
        
        # Remover formatação do CPF antes de validar
        cpf_numbers = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf_numbers) != 11:
            return JsonResponse({'success': False, 'error': 'CPF deve ter 11 dígitos.'})
        
        # Verificar duplicatas ANTES de criar qualquer coisa
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': f'Já existe um usuário com o nome "{username}".'})
        
        if UserProfile.objects.filter(cpf=cpf_numbers).exists():
            return JsonResponse({'success': False, 'error': 'Já existe um usuário com este CPF.'})
        
        # Email pode ser duplicado - não validar unicidade de email
        
        # Verificar se o grupo existe antes de criar
        try:
            group = Group.objects.get(pk=group_id)
        except Group.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Grupo selecionado não existe.'})
        
        # Tudo validado - agora criar o usuário
        try:
            # Desconectar signals temporariamente para evitar criação automática de profile sem CPF
            from django.db.models.signals import post_save
            from django.db import transaction
            
            with transaction.atomic():
                # Desconectar signals
                post_save.disconnect(sender=User, dispatch_uid='create_user_profile')
                post_save.disconnect(sender=User, dispatch_uid='save_user_profile')
                
                try:
                    # Criar usuário com senha temporária inutilizável
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=True
                    )
                    user.set_unusable_password()  # Senha será definida pelo link de reset
                    user.save()
                    
                    # Criar perfil manualmente com CPF
                    UserProfile.objects.create(user=user, cpf=cpf_numbers)
                    
                    # Adicionar ao grupo dentro da transação
                    user.groups.add(group)
                    # Copiar permissões do grupo para user_permissions para que apareçam no admin
                    try:
                        perms = list(group.permissions.all())
                        if perms:
                            user.user_permissions.add(*perms)
                    except Exception:
                        pass
                finally:
                    # Reconectar signals
                    from accounts.models import create_user_profile, save_user_profile
                    post_save.connect(create_user_profile, sender=User, dispatch_uid='create_user_profile')
                    post_save.connect(save_user_profile, sender=User, dispatch_uid='save_user_profile')
            
            # Gerar token de reset de senha
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Construir link de reset usando URL nomeada
            reset_path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            reset_link = request.build_absolute_uri(reset_path)
            
            # Enviar email
            subject = 'Bem-vindo(a) ao VetSystem - Crie sua senha'
            message = f"""
Olá {user.first_name or user.username},

Você foi cadastrado(a) no sistema VetSystem.

Para começar a usar o sistema, você precisa criar sua senha de acesso.
Clique no link abaixo para criar sua senha:

{reset_link}

Este link é válido por 24 horas.

Atenciosamente,
Equipe VetSystem
            """
            
            email_sent = False
            email_error = None
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                email_sent = True
            except Exception as e:
                email_error = str(e)
                # Log do erro mas não falha a criação
            
            if email_sent:
                return JsonResponse({
                    'success': True, 
                    'message': f'Usuário "{username}" criado com sucesso! Um email foi enviado para {email} com instruções para criar a senha.'
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': f'Usuário "{username}" criado com sucesso, mas não foi possível enviar o email. Por favor, crie a senha manualmente pelo painel administrativo.'
                })
                
        except Exception as e:
            # Se der erro, deletar o usuário se foi criado
            if 'user' in locals():
                try:
                    user.delete()
                except:
                    pass
            return JsonResponse({'success': False, 'error': f'Erro ao criar usuário: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido.'})


@login_required
def user_delete_view(request, user_id):
    """View para excluir um usuário"""
    
    # Verificar permissão
    if not can_manage_users(request.user):
        messages.error(request, 'Você não tem permissão para excluir usuários.')
        return redirect('accounts:profile')
    
    # Não permitir excluir a si mesmo
    if request.user.id == user_id:
        messages.error(request, 'Você não pode excluir seu próprio usuário.')
        return redirect('accounts:user_list')
    
    user = get_object_or_404(User, pk=user_id)
    username = user.username

    # Suportar exclusão via AJAX retornando JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            user.delete()
            return JsonResponse({'success': True, 'message': f'Usuário "{username}" excluído com sucesso.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Erro ao excluir usuário: {str(e)}'})

    # POST normal - sempre redirecionar
    if request.method == 'POST':
        try:
            user.delete()
            messages.success(request, f'Usuário "{username}" excluído com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir usuário: {str(e)}')
        return redirect('accounts:user_list')

    # GET - redirecionar também
    return redirect('accounts:user_list')


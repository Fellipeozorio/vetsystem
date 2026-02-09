from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group, Permission
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline para editar perfil do usuário junto com os dados do User"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Informações do Perfil'
    fk_name = 'user'
    fields = ('cpf', 'celular', 'crmv', 'mapa', 'avatar')


class CustomUserAdmin(BaseUserAdmin):
    """Admin customizado para User com perfil inline"""
    inlines = (UserProfileInline,)
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_cpf', 'get_group', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'userprofile__cpf')
    list_select_related = ('userprofile',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('username', 'password')
        }),
        ('Dados Pessoais', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Datas Importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name'),
        }),
    )

    def get_cpf(self, instance):
        """Exibe CPF formatado na listagem"""
        if hasattr(instance, 'userprofile') and instance.userprofile.cpf:
            return instance.userprofile.get_cpf_formatted()
        return '-'
    get_cpf.short_description = 'CPF'
    get_cpf.admin_order_field = 'userprofile__cpf'
    
    def get_group(self, instance):
        """Exibe o primeiro grupo do usuário"""
        groups = instance.groups.all()
        if groups.exists():
            return groups.first().name
        return '-'
    get_group.short_description = 'Grupo'

    def get_inline_instances(self, request, obj=None):
        """Só mostra inline quando editando usuário existente"""
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

    def save_related(self, request, form, formsets, change):
        """Sincroniza `user_permissions` com a união de permissões explícitas selecionadas
        no formulário e permissões derivadas dos grupos atribuídos.
        Isso garante que ao adicionar/remover grupos no Admin as permissões reflitam
        corretamente os grupos atuais sem perder permissões explicitamente definidas.
        """
        super().save_related(request, form, formsets, change)
        user = form.instance
        try:
            # Permissões explicitamente selecionadas no formulário (m2m do admin)
            explicit_perms = form.cleaned_data.get('user_permissions') if hasattr(form, 'cleaned_data') else None
            if explicit_perms is None:
                explicit_perms = user.user_permissions.all()

            # Permissões derivadas dos grupos atuais do usuário
            group_perms = Permission.objects.filter(group__in=user.groups.all()).distinct()

            # União: manter permissões explícitas + permissões dos grupos
            final_perms = set(explicit_perms) | set(group_perms)

            # Aplicar no usuário (substitui quaisquer permissões que não estejam
            # na união explícita+grupos)
            user.user_permissions.set(list(final_perms))
        except Exception:
            # Não bloquear o fluxo do admin caso algo falhe aqui
            pass

    class Media:
        js = ("/static/accounts/js/admin_group_permissions.js",)


# Desregistrar os modelos padrão do Django admin
admin.site.unregister(User)
admin.site.unregister(Group)

# Registrar modelos customizados no app accounts
admin.site.register(User, CustomUserAdmin)
admin.site.register(Group, BaseGroupAdmin)

# Customizar títulos do admin
admin.site.site_header = 'VetSystem - Administração'
admin.site.site_title = 'VetSystem Admin'
admin.site.index_title = 'Painel de Controle'

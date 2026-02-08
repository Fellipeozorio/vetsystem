from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_cpf')
    list_select_related = ('userprofile',)

    def get_cpf(self, instance):
        return instance.userprofile.get_cpf_formatted() if hasattr(instance, 'userprofile') else '-'
    get_cpf.short_description = 'CPF'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(UserAdmin, self).get_inline_instances(request, obj)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_cpf', 'celular', 'crmv', 'mapa')
    search_fields = ('user__username', 'user__email', 'cpf', 'celular')
    raw_id_fields = ('user',)

    def get_cpf(self, obj):
        return obj.get_cpf_formatted()
    get_cpf.short_description = 'CPF'

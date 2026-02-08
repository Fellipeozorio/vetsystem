from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator
import re


def validate_cpf(value):
    """Valida formato do CPF (apenas números, 11 dígitos)"""
    cpf = re.sub(r'\D', '', value)
    if len(cpf) != 11:
        from django.core.exceptions import ValidationError
        raise ValidationError('CPF deve ter 11 dígitos.')
    return cpf


class UserProfile(models.Model):
    """Perfil estendido do usuário com informações adicionais"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    cpf = models.CharField(
        max_length=14,
        unique=True,
        blank=False,
        null=False,
        verbose_name="CPF",
        help_text="Formato: 000.000.000-00"
    )
    celular = models.CharField(
        max_length=15,
        blank=True,
        verbose_name="Celular",
        help_text="Formato: (11) 99999-9999"
    )
    crmv = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="CRMV",
        help_text="Ex: CRMV-SP 12345"
    )
    mapa = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Registro MAPA",
        help_text="Ex: MAPA 123456"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name="Foto de Perfil"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuários"
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"
    
    def get_avatar_url(self):
        """Retorna a URL do avatar ou gera um avatar padrão com iniciais"""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        else:
            name = self.user.get_full_name() or self.user.username
            return f"https://ui-avatars.com/api/?name={name}&size=150&background=206bc4&color=fff"
    
    def get_display_name(self):
        """Retorna o nome completo ou username"""
        return self.user.get_full_name() or self.user.username
    
    def get_primary_group(self):
        """Retorna o primeiro grupo do usuário ou None"""
        groups = self.user.groups.all()
        return groups.first() if groups.exists() else None
    
    def get_cpf_formatted(self):
        """Retorna o CPF formatado"""
        if self.cpf:
            cpf = re.sub(r'\D', '', self.cpf)
            if len(cpf) == 11:
                return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return self.cpf or ""
    
    def save(self, *args, **kwargs):
        # Formatar CPF antes de salvar
        if self.cpf:
            self.cpf = re.sub(r'\D', '', self.cpf)
            if len(self.cpf) == 11:
                self.cpf = f"{self.cpf[:3]}.{self.cpf[3:6]}.{self.cpf[6:9]}-{self.cpf[9:]}"
        super().save(*args, **kwargs)


@receiver(post_save, sender=User, dispatch_uid='create_user_profile')
def create_user_profile(sender, instance, created, **kwargs):
    """Cria automaticamente um UserProfile quando um usuário é criado"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User, dispatch_uid='save_user_profile')
def save_user_profile(sender, instance, **kwargs):
    """Garante que o UserProfile seja salvo quando o usuário é salvo"""
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
    else:
        UserProfile.objects.get_or_create(user=instance)

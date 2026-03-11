from django import forms
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.forms import PasswordChangeForm
from .models import UserProfile
import re


class UserProfileForm(forms.ModelForm):
    """Formulário para edição do perfil do usuário"""
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label="Nome",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label="Sobrenome",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'})
    )
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com', 'required': 'required'})
    )

    class Meta:
        model = UserProfile
        fields = ['avatar', 'cpf', 'celular', 'crmv', 'mapa']
        labels = {
            'avatar': 'Foto de Perfil',
            'cpf': 'CPF',
            'celular': 'Celular',
            'crmv': 'CRMV',
            'mapa': 'MAPA'
        }
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000.000.000-00',
                'maxlength': '14',
                'data-mask': '000.000.000-00'
            }),
            'celular': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999',
                'maxlength': '15'
            }),
            'crmv': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: CRMV-SP 12345'
            }),
            'mapa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: MAPA 123456'
            }),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            # Remove caracteres não numéricos
            cpf_digits = re.sub(r'\D', '', cpf)
            
            if len(cpf_digits) != 11:
                raise forms.ValidationError('CPF deve ter 11 dígitos.')
            
            # Verificar se já existe outro usuário com este CPF
            profile_id = self.instance.id if self.instance else None
            existing = UserProfile.objects.filter(cpf__iregex=r'^[0-9.-]*$').exclude(id=profile_id)
            
            for profile in existing:
                if profile.cpf:
                    existing_digits = re.sub(r'\D', '', profile.cpf)
                    if existing_digits == cpf_digits:
                        raise forms.ValidationError('Já existe um usuário cadastrado com este CPF.')
            
            # Formatar CPF
            formatted_cpf = f"{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:]}"
            return formatted_cpf
        return cpf

    def clean_celular(self):
        celular = self.cleaned_data.get('celular')
        if celular:
            # Remove caracteres não numéricos
            celular_digits = re.sub(r'\D', '', celular)
            
            if len(celular_digits) < 10 or len(celular_digits) > 11:
                raise forms.ValidationError('Celular deve ter 10 ou 11 dígitos (com DDD).')
            
            # Formatar celular
            if len(celular_digits) == 10:
                formatted = f"({celular_digits[:2]}) {celular_digits[2:6]}-{celular_digits[6:]}"
            else:
                formatted = f"({celular_digits[:2]}) {celular_digits[2:7]}-{celular_digits[7:]}"
            return formatted
        return celular

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Atualizar os campos do User
        profile.user.first_name = self.cleaned_data.get('first_name', '')
        profile.user.last_name = self.cleaned_data.get('last_name', '')
        profile.user.email = self.cleaned_data.get('email', '')
        
        if commit:
            profile.user.save()
            profile.save()
        
        return profile


class UserEditForm(forms.ModelForm):
    """Formulário para edição de usuário pelo admin"""
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label="Nome",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label="Sobrenome",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'required': 'required'})
    )
    is_active = forms.BooleanField(
        required=False,
        label="Usuário ativo",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_superuser = forms.BooleanField(
        required=False,
        label="Administrador do Sistema",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Administradores têm acesso total ao sistema e ao painel administrativo."
    )
    
    # Campo para grupo (apenas um)
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label="Grupo",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_group'
        })
    )
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        label="Permissões do usuário",
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'id': 'id_permissions_chosen',
            'size': '10'
        })
    )

    class Meta:
        model = UserProfile
        fields = ['sexo', 'perfil', 'cpf', 'celular', 'crmv', 'mapa', 'avatar']
        widgets = {
            'sexo': forms.Select(attrs={'class': 'form-select', 'id': 'id_sexo'}),
            'perfil': forms.Select(attrs={'class': 'form-select', 'id': 'id_perfil'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'celular': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 99999-9999'}),
            'crmv': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CRMV-SP 12345'}),
            'mapa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: MAPA 123456'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('editing_user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['is_active'].initial = user.is_active
            self.fields['is_superuser'].initial = user.is_superuser
            # Grupo (apenas um)
            self.fields['group'].initial = user.groups.first()
            self.fields['user_permissions'].initial = user.user_permissions.all()

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            cpf_digits = re.sub(r'\D', '', cpf)
            if len(cpf_digits) != 11:
                raise forms.ValidationError('CPF deve ter 11 dígitos.')
            
            # Verificar duplicidade
            profile_id = self.instance.id if self.instance else None
            for profile in UserProfile.objects.exclude(id=profile_id):
                if profile.cpf:
                    existing_digits = re.sub(r'\D', '', profile.cpf)
                    if existing_digits == cpf_digits:
                        raise forms.ValidationError('Já existe um usuário cadastrado com este CPF.')
            
            return f"{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:]}"
        return cpf

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = self.cleaned_data.get('email', '')
        user.is_active = self.cleaned_data.get('is_active', True)
        # is_superuser implica is_staff
        is_super = self.cleaned_data.get('is_superuser', False)
        user.is_superuser = is_super
        user.is_staff = is_super
        
        if commit:
            user.save()
            profile.save()
            
            # Atualizar grupo (apenas um)
            user.groups.clear()
            group = self.cleaned_data.get('group')
            if group:
                user.groups.add(group)
            
            # Atualizar permissões
            user.user_permissions.set(self.cleaned_data.get('user_permissions', []))
        
        return profile


class CustomPasswordChangeForm(PasswordChangeForm):
    """Formulário customizado para alteração de senha com estilos Tabler"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})

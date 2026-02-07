# Core views for VetSystem
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView, 
    PasswordResetCompleteView
)
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse_lazy


@login_required
def dashboard_view(request):
    """Dashboard view showing system overview."""
    return render(request, 'core/dashboard.html')


def logout_view(request):
    """Logout view that supports GET requests."""
    logout(request)
    return redirect('login')


class CustomPasswordResetView(PasswordResetView):
    """View customizada para solicitar redefinição de senha"""
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.txt'
    html_email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    form_class = PasswordResetForm

    def form_valid(self, form):
        # Verificar se o email existe no sistema
        email = form.cleaned_data['email']
        users = User.objects.filter(email=email)
        
        if not users.exists():
            messages.error(self.request, 'Este email não está cadastrado no sistema.')
            return self.form_invalid(form)
        
        # Usar o comportamento padrão do Django para enviar email
        response = super().form_valid(form)
        
        # Adicionar mensagem de sucesso
        messages.success(
            self.request, 
            f'Um email com instruções para redefinir sua senha foi enviado para {email}. '
            f'Verifique sua caixa de entrada e spam.'
        )
        
        return response


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """View para confirmar envio do email de redefinição"""
    template_name = 'registration/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """View para criar nova senha"""
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """View para confirmar sucesso da redefinição"""
    template_name = 'registration/password_reset_complete.html'

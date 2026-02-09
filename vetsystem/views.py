from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)


@login_required
def dashboard_view(request):
    """View principal do dashboard"""
    context = {
        'user': request.user,
    }
    return render(request, 'core/dashboard.html', context)


def logout_view(request):
    """View para logout"""
    logout(request)
    return redirect('login')


class CustomPasswordResetView(PasswordResetView):
    """View customizada para reset de senha"""
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = '/accounts/password_reset/done/'
    html_email_template_name = 'registration/password_reset_email.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_name'] = 'VetSystem'
        return context


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """View customizada para confirmação de envio do email de reset"""
    template_name = 'registration/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """View customizada para definir nova senha"""
    template_name = 'registration/password_reset_confirm.html'
    success_url = '/accounts/reset/done/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.validlink:
            context['validlink'] = True
        return context


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """View customizada para confirmação de reset completo"""
    template_name = 'registration/password_reset_complete.html'

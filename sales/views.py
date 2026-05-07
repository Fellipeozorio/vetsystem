from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def ponto_de_venda(request):
    return render(request, 'sales/ponto_de_venda.html', {})


@login_required
def minhas_vendas(request):
    return render(request, 'sales/minhas_vendas.html', {})


@login_required
def consulta_vendas(request):
    return render(request, 'sales/consulta_vendas.html', {})


@login_required
def pacotes_vendidos(request):
    return render(request, 'sales/pacotes_vendidos.html', {})


@login_required
def lista_de_precos(request):
    return render(request, 'sales/lista_de_precos.html', {})


@login_required
def ranking_de_precos(request):
    return render(request, 'sales/ranking_de_precos.html', {})


@login_required
def modelo_orcamento(request):
    return render(request, 'sales/modelo_orcamento.html', {})


@login_required
def modelo_demonstrativo(request):
    return render(request, 'sales/modelo_demonstrativo.html', {})


@login_required
def configuracoes(request):
    return render(request, 'sales/configuracoes.html', {})


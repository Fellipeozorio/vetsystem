import json
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from .models import Brand, Product


# ─── Produtos e Serviços ──────────────────────────────────────────────────────

@login_required
def produtos_servicos(request):
    qs = Product.objects.all()

    hoje = date.today()
    limite_60 = hoje + timedelta(days=60)

    # Busca simples (nome / código / código de barras)
    query = request.GET.get('q', '').strip()
    if query:
        qs = qs.filter(
            Q(nome__icontains=query) |
            Q(codigo__icontains=query) |
            Q(codigo_barras__icontains=query)
        )

    # Filtros avançados
    active_filters = {}
    f_nome = request.GET.get('filter_nome', '').strip()
    f_codigo = request.GET.get('filter_codigo', '').strip()
    f_barcode = request.GET.get('filter_codigo_barras', '').strip()
    f_marca = request.GET.get('filter_marca', '').strip()
    f_tipo = request.GET.get('filter_tipo', '').strip()
    f_ativo = request.GET.get('filter_ativo', '').strip()
    f_situacao = request.GET.get('filter_situacao', '').strip()
    f_pendencia = request.GET.get('filter_pendencia', '').strip()
    f_validade = request.GET.get('filter_validade', '').strip()

    if f_nome:
        qs = qs.filter(nome__icontains=f_nome)
        active_filters['nome'] = f_nome
    if f_codigo:
        qs = qs.filter(codigo__icontains=f_codigo)
        active_filters['codigo'] = f_codigo
    if f_barcode:
        qs = qs.filter(codigo_barras__icontains=f_barcode)
        active_filters['codigo_barras'] = f_barcode
    if f_marca:
        qs = qs.filter(marca_id=f_marca)
        active_filters['marca'] = f_marca
    if f_tipo:
        qs = qs.filter(tipo=f_tipo)
        active_filters['tipo'] = f_tipo
    if f_ativo:
        qs = qs.filter(ativo=(f_ativo == 'True'))
        active_filters['ativo'] = f_ativo
    if f_pendencia:
        qs = qs.filter(pendencia_fiscal=True)
        active_filters['pendencia'] = f_pendencia
    if f_validade:
        # validade filter can be 'vencida' or 'vencendo'
        if f_validade == 'vencida':
            qs = qs.filter(validade__lt=hoje)
        elif f_validade == 'vencendo':
            qs = qs.filter(validade__gte=hoje, validade__lte=limite_60)
        active_filters['validade'] = f_validade

    # Stats (from all products)
    todos = Product.objects.all()

    qtd_pendencia_fiscal = todos.filter(pendencia_fiscal=True).count()
    qtd_validade_vencida = todos.filter(validade__lt=hoje).count()
    qtd_vencendo_60 = todos.filter(validade__gte=hoje, validade__lte=limite_60).count()

    # Filtro de situação (pós-queryset pois é calculada)
    produtos_list = list(qs.select_related('marca'))
    if f_situacao:
        produtos_list = [p for p in produtos_list if p.situacao_estoque() == f_situacao]
        active_filters['situacao'] = f_situacao

    paginator = Paginator(produtos_list, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    marcas = Brand.objects.filter(ativo=True)

    # AJAX: salvar produto
    if request.method == 'POST':
        return _salvar_produto(request)

    return render(request, 'inventory/produtos_servicos.html', {
        'page_obj': page_obj,
        'query': query,
        'active_filters': active_filters,
        'marcas': marcas,
        'qtd_pendencia_fiscal': qtd_pendencia_fiscal,
        'qtd_validade_vencida': qtd_validade_vencida,
        'qtd_vencendo_60': qtd_vencendo_60,
    })


@login_required
@require_http_methods(['POST'])
def produto_save(request):
    return _salvar_produto(request)


@login_required
@require_http_methods(['GET'])
def produto_detail(request, pk):
    produto = get_object_or_404(Product, pk=pk)
    data = {
        'id': produto.id,
        'nome': produto.nome,
        'codigo': produto.codigo or '',
        'codigo_barras': produto.codigo_barras or '',
        'tipo': produto.tipo,
        'marca': produto.marca_id or '',
        'preco_custo': str(produto.preco_custo),
        'markup': str(produto.markup),
        'preco_venda': str(produto.preco_venda),
        'estoque_atual': produto.estoque_atual,
        'estoque_minimo': produto.estoque_minimo,
        'estoque_maximo': produto.estoque_maximo,
        'validade': produto.validade.strftime('%Y-%m-%d') if produto.validade else '',
        'fornecedor': produto.fornecedor or '',
        'pendencia_fiscal': produto.pendencia_fiscal,
        'descricao': produto.descricao or '',
        'ativo': produto.ativo,
    }
    return JsonResponse(data)


@login_required
@require_http_methods(['POST'])
def produto_delete(request, pk):
    produto = get_object_or_404(Product, pk=pk)
    produto.delete()
    return JsonResponse({'success': True})


def _salvar_produto(request):
    try:
        data = json.loads(request.body)
        pk = data.get('id')

        campos = {
            'nome': data.get('nome', '').strip(),
            'codigo': data.get('codigo', '').strip() or None,
            'codigo_barras': data.get('codigo_barras', '').strip() or None,
            'tipo': data.get('tipo', 'produto'),
            'marca_id': data.get('marca') or None,
            'preco_custo': data.get('preco_custo') or 0,
            'markup': data.get('markup') or 0,
            'preco_venda': data.get('preco_venda') or 0,
            'estoque_atual': int(data.get('estoque_atual') or 0),
            'estoque_minimo': int(data.get('estoque_minimo') or 0),
            'estoque_maximo': int(data.get('estoque_maximo') or 0),
            'validade': data.get('validade') or None,
            'fornecedor': data.get('fornecedor', '').strip() or None,
            'pendencia_fiscal': bool(data.get('pendencia_fiscal', False)),
            'descricao': data.get('descricao', '').strip() or None,
            'ativo': bool(data.get('ativo', True)),
        }

        if not campos['nome']:
            return JsonResponse({'success': False, 'error': 'Nome é obrigatório.'}, status=400)

        if pk:
            Product.objects.filter(pk=pk).update(**campos)
            produto = Product.objects.get(pk=pk)
        else:
            produto = Product.objects.create(**campos)

        return JsonResponse({'success': True, 'id': produto.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ─── Marcas ───────────────────────────────────────────────────────────────────

@login_required
def marcas(request):
    qs = Brand.objects.all()

    query = request.GET.get('q', '').strip()
    if query:
        qs = qs.filter(nome__icontains=query)

    active_filters = {}
    f_ativo = request.GET.get('filter_ativo', '').strip()
    if f_ativo:
        qs = qs.filter(ativo=(f_ativo == 'True'))
        active_filters['ativo'] = f_ativo

    if request.method == 'POST':
        return _salvar_marca(request)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'inventory/marcas.html', {
        'page_obj': page_obj,
        'query': query,
        'active_filters': active_filters,
    })


@login_required
@require_http_methods(['POST'])
def marca_save(request):
    return _salvar_marca(request)


@login_required
@require_http_methods(['GET'])
def marca_detail(request, pk):
    marca = get_object_or_404(Brand, pk=pk)
    return JsonResponse({'id': marca.id, 'nome': marca.nome, 'ativo': marca.ativo})


@login_required
@require_http_methods(['POST'])
def marca_delete(request, pk):
    marca = get_object_or_404(Brand, pk=pk)
    marca.delete()
    return JsonResponse({'success': True})


def _salvar_marca(request):
    try:
        data = json.loads(request.body)
        pk = data.get('id')
        nome = data.get('nome', '').strip()
        ativo = bool(data.get('ativo', True))

        if not nome:
            return JsonResponse({'success': False, 'error': 'Nome é obrigatório.'}, status=400)

        if pk:
            Brand.objects.filter(pk=pk).update(nome=nome, ativo=ativo)
            marca = Brand.objects.get(pk=pk)
        else:
            marca = Brand.objects.create(nome=nome, ativo=ativo)

        return JsonResponse({'success': True, 'id': marca.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Create your views here.

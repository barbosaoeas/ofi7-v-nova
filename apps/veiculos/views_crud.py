"""
Views CRUD para Veículos (Frontend Web)
"""
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.conf import settings

from .models import Veiculo
from .models_fabricantes import Fabricante, ModeloVeiculo, CorVeiculo
from .forms import VeiculoForm, FabricanteForm, ModeloVeiculoForm, CorVeiculoForm


# ==================== VEÍCULOS ====================

@login_required
def veiculo_list(request):
    """Lista de veículos"""
    query = request.GET.get('q', '')
    
    veiculos = Veiculo.objects.select_related('cliente', 'modelo_veiculo__fabricante').order_by('-criado_em')
    
    if query:
        veiculos = veiculos.filter(
            Q(placa__icontains=query) |
            Q(cliente__nome__icontains=query) |
            Q(modelo_veiculo__nome__icontains=query) |
            Q(marca__icontains=query)
        )
    
    paginator = Paginator(veiculos, 20)
    page = request.GET.get('page', 1)
    veiculos_page = paginator.get_page(page)
    
    context = {'veiculos': veiculos_page, 'query': query}
    return render(request, 'veiculos/veiculo_list.html', context)


@login_required
def veiculo_create(request):
    """Criar novo veículo"""
    if request.method == 'POST':
        form = VeiculoForm(request.POST, request.FILES)
        if form.is_valid():
            veiculo = form.save()
            messages.success(request, f'Veículo "{veiculo.placa}" cadastrado com sucesso!')
            return redirect('veiculos:list')
    else:
        form = VeiculoForm()
    
    context = {'form': form, 'title': 'Novo Veículo'}
    return render(request, 'veiculos/veiculo_form.html', context)


@login_required
def veiculo_update(request, pk):
    """Editar veículo"""
    veiculo = get_object_or_404(Veiculo, pk=pk)
    
    if request.method == 'POST':
        form = VeiculoForm(request.POST, request.FILES, instance=veiculo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Veículo "{veiculo.placa}" atualizado com sucesso!')
            return redirect('veiculos:list')
    else:
        form = VeiculoForm(instance=veiculo)
    
    context = {'form': form, 'title': f'Editar Veículo: {veiculo.placa}', 'veiculo': veiculo}
    return render(request, 'veiculos/veiculo_form.html', context)


@login_required
def veiculo_delete(request, pk):
    """Deletar veículo"""
    veiculo = get_object_or_404(Veiculo, pk=pk)
    
    if request.method == 'POST':
        placa = veiculo.placa
        veiculo.delete()
        messages.success(request, f'Veículo "{placa}" removido com sucesso!')
        return redirect('veiculos:list')
    
    context = {'veiculo': veiculo}
    return render(request, 'veiculos/veiculo_confirm_delete.html', context)


@login_required
def veiculo_detail(request, pk):
    """Detalhes do veículo"""
    veiculo = get_object_or_404(Veiculo.objects.select_related('cliente', 'modelo_veiculo__fabricante'), pk=pk)
    
    context = {'veiculo': veiculo}
    return render(request, 'veiculos/veiculo_detail.html', context)

@login_required
def veiculo_buscar_por_placa(request):
    placa = (request.GET.get('placa') or '').strip()
    placa = re.sub(r'[^A-Za-z0-9]', '', placa).upper()

    if len(placa) != 7:
        return JsonResponse({'ok': False, 'erro': 'Informe uma placa com 7 caracteres.'}, status=400)

    veiculo = Veiculo.objects.select_related(
        'cliente',
        'modelo_veiculo__fabricante',
        'cor_veiculo',
    ).filter(placa=placa).first()

    if not veiculo:
        api_key = (getattr(settings, 'FIPE_PLACAS_API_KEY', '') or '').strip()
        if not api_key:
            return JsonResponse({'ok': True, 'encontrado': False})

        try:
            import json as _json
            from urllib.request import Request, urlopen
            from urllib.error import HTTPError, URLError

            url = f'https://placas.fipeapi.com.br/placas/{placa}?key={api_key}'
            req = Request(url, headers={'User-Agent': 'ofi7/1.0', 'Accept': 'application/json'})
            with urlopen(req, timeout=10) as resp:
                payload = resp.read().decode('utf-8')
            data = _json.loads(payload) if payload else {}

            veic = (((data or {}).get('data') or {}).get('veiculo') or {})
            marca_modelo = veic.get('marca_modelo') or ''
            cor_nome = veic.get('cor') or ''
            ano_str = veic.get('ano') or ''

            ano_fab = None
            ano_mod = None
            if isinstance(ano_str, str) and '/' in ano_str:
                a, b = ano_str.split('/', 1)
                if a.isdigit():
                    ano_fab = int(a)
                if b.isdigit():
                    ano_mod = int(b)
            elif isinstance(ano_str, str) and ano_str.isdigit():
                ano_mod = int(ano_str)

            fabricante_id = None
            modelo_veiculo_id = None
            fabricante_txt = ''
            modelo_txt = ''
            if isinstance(marca_modelo, str) and '/' in marca_modelo:
                fab, mod = marca_modelo.split('/', 1)
                fab = fab.strip()
                mod = mod.strip()
                fabricante_txt = fab
                modelo_txt = mod
                fabricante = Fabricante.objects.filter(nome__iexact=fab).first()
                if fabricante:
                    fabricante_id = fabricante.id
                    modelo = ModeloVeiculo.objects.filter(fabricante=fabricante, nome__iexact=mod).first() or \
                             ModeloVeiculo.objects.filter(fabricante=fabricante, nome__icontains=mod[:20]).first()
                    if modelo:
                        modelo_veiculo_id = modelo.id

            cor_veiculo_id = None
            if cor_nome:
                cor_obj = CorVeiculo.objects.filter(nome__iexact=cor_nome.strip()).first()
                if cor_obj:
                    cor_veiculo_id = cor_obj.id

            return JsonResponse({
                'ok': True,
                'encontrado': False,
                'externo': True,
                'fonte': 'fipeapi',
                'dados': {
                    'placa': placa,
                    'modelo_veiculo_id': modelo_veiculo_id,
                    'cor_veiculo_id': cor_veiculo_id,
                    'ano_fabricacao': ano_fab,
                    'ano_modelo': ano_mod,
                    'fabricante': fabricante_txt,
                    'modelo': modelo_txt,
                    'cor': cor_nome,
                    'sugestao_modelo_texto': marca_modelo,
                    'sugestao_cor_texto': cor_nome,
                }
            })
        except Exception:
            return JsonResponse({'ok': True, 'encontrado': False, 'externo': False})

    return JsonResponse({
        'ok': True,
        'encontrado': True,
        'update_url': reverse('veiculos:update', args=[veiculo.pk]),
        'dados': {
            'placa': veiculo.placa,
            'cliente_id': veiculo.cliente_id,
            'modelo_veiculo_id': veiculo.modelo_veiculo_id,
            'cor_veiculo_id': veiculo.cor_veiculo_id,
            'ano_fabricacao': veiculo.ano_fabricacao,
            'ano_modelo': veiculo.ano_modelo,
            'chassi': veiculo.chassi,
            'renavam': veiculo.renavam,
            'km_atual': veiculo.km_atual,
        }
    })


# ==================== FABRICANTES ====================

@login_required
def fabricante_list(request):
    """Lista de fabricantes"""
    fabricantes = Fabricante.objects.all().order_by('nome')
    
    context = {'fabricantes': fabricantes}
    return render(request, 'veiculos/fabricante_list.html', context)


@login_required
def fabricante_create(request):
    """Criar novo fabricante"""
    if request.method == 'POST':
        form = FabricanteForm(request.POST)
        if form.is_valid():
            fabricante = form.save()
            messages.success(request, f'Fabricante "{fabricante.nome}" cadastrado com sucesso!')
            return redirect('veiculos:fabricante_list')
    else:
        form = FabricanteForm()
    
    context = {'form': form, 'title': 'Novo Fabricante'}
    return render(request, 'veiculos/fabricante_form.html', context)


@login_required
def fabricante_update(request, pk):
    """Editar fabricante"""
    fabricante = get_object_or_404(Fabricante, pk=pk)
    
    if request.method == 'POST':
        form = FabricanteForm(request.POST, instance=fabricante)
        if form.is_valid():
            form.save()
            messages.success(request, f'Fabricante "{fabricante.nome}" atualizado!')
            return redirect('veiculos:fabricante_list')
    else:
        form = FabricanteForm(instance=fabricante)
    
    context = {'form': form, 'title': f'Editar Fabricante: {fabricante.nome}'}
    return render(request, 'veiculos/fabricante_form.html', context)


# ==================== MODELOS ====================

@login_required
def modelo_list(request):
    """Lista de modelos"""
    modelos = ModeloVeiculo.objects.select_related('fabricante').order_by('fabricante__nome', 'nome')
    
    context = {'modelos': modelos}
    return render(request, 'veiculos/modelo_list.html', context)


@login_required
def modelo_create(request):
    """Criar novo modelo"""
    if request.method == 'POST':
        form = ModeloVeiculoForm(request.POST)
        if form.is_valid():
            modelo = form.save()
            messages.success(request, f'Modelo "{modelo}" cadastrado com sucesso!')
            return redirect('veiculos:modelo_list')
    else:
        form = ModeloVeiculoForm()
    
    context = {'form': form, 'title': 'Novo Modelo'}
    return render(request, 'veiculos/modelo_form.html', context)


@login_required
def modelo_update(request, pk):
    """Editar modelo"""
    modelo = get_object_or_404(ModeloVeiculo, pk=pk)
    
    if request.method == 'POST':
        form = ModeloVeiculoForm(request.POST, instance=modelo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Modelo "{modelo}" atualizado!')
            return redirect('veiculos:modelo_list')
    else:
        form = ModeloVeiculoForm(instance=modelo)
    
    context = {'form': form, 'title': f'Editar Modelo: {modelo}'}
    return render(request, 'veiculos/modelo_form.html', context)

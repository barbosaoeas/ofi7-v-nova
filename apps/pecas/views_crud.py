"""
Views CRUD para Peças (Frontend Web)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Peca
from .forms import PecaForm


@login_required
def peca_list(request):
    """Lista de peças com busca e filtros"""
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    pecas = Peca.objects.all().select_related('veiculo')
    
    if query:
        pecas = pecas.filter(
            Q(descricao__icontains=query) |
            Q(veiculo__placa__icontains=query) |
            Q(fornecedor_nome__icontains=query)
        )
    
    if status_filter:
        pecas = pecas.filter(status=status_filter)
    
    paginator = Paginator(pecas, 20)
    page = request.GET.get('page', 1)
    pecas_page = paginator.get_page(page)
    
    context = {
        'pecas': pecas_page,
        'query': query,
        'status_filter': status_filter,
        'status_choices': Peca.STATUS_CHOICES
    }
    return render(request, 'pecas/peca_list.html', context)


@login_required
def peca_create(request):
    """Criar nova peça"""
    if request.method == 'POST':
        form = PecaForm(request.POST)
        if form.is_valid():
            peca = form.save(commit=False)
            peca.solicitado_por = request.user
            peca.save()
            messages.success(request, f'Peça "{peca.descricao}" cadastrada com sucesso!')
            return redirect('pecas:list')
    else:
        initial = {}
        orcamento_id = request.GET.get('orcamento')
        veiculo_id = request.GET.get('veiculo')
        ordem_id = request.GET.get('ordem')
        if orcamento_id:
            initial['orcamento'] = orcamento_id
        if veiculo_id:
            initial['veiculo'] = veiculo_id
        if ordem_id:
            initial['ordem'] = ordem_id
        form = PecaForm(initial=initial)
    
    context = {'form': form, 'title': 'Nova Peça'}
    return render(request, 'pecas/peca_form.html', context)


@login_required
def peca_update(request, pk):
    """Editar peça"""
    peca = get_object_or_404(Peca, pk=pk)
    if request.method == 'POST':
        form = PecaForm(request.POST, instance=peca)
        if form.is_valid():
            form.save()
            messages.success(request, f'Peça "{peca.descricao}" atualizada com sucesso!')
            return redirect('pecas:list')
    else:
        form = PecaForm(instance=peca)
    
    context = {'form': form, 'title': f'Editar Peça: {peca.descricao}', 'peca': peca}
    return render(request, 'pecas/peca_form.html', context)


@login_required
def peca_delete(request, pk):
    """Deletar peça"""
    peca = get_object_or_404(Peca, pk=pk)
    if request.method == 'POST':
        descricao = peca.descricao
        peca.delete()
        messages.success(request, f'Peça "{descricao}" removida com sucesso!')
        return redirect('pecas:list')
    
    context = {'peca': peca}
    return render(request, 'pecas/peca_confirm_delete.html', context)

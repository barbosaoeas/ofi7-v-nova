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
from .services import PecaService


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
    cliente_id = request.GET.get('cliente')
    if request.method == 'POST':
        form = PecaForm(request.POST, cliente_id=cliente_id)
        if form.is_valid():
            peca = form.save(commit=False)
            peca.solicitado_por = request.user
            descricao = (peca.descricao or '').strip()
            if descricao:
                existentes = Peca.objects.filter(descricao__iexact=descricao).exclude(status='cancelada')
                if peca.ordem_id:
                    existentes = existentes.filter(ordem_id=peca.ordem_id)
                if peca.orcamento_id:
                    existentes = existentes.filter(orcamento_id=peca.orcamento_id)
                if not peca.ordem_id and not peca.orcamento_id and peca.veiculo_id:
                    existentes = existentes.filter(veiculo_id=peca.veiculo_id, orcamento__isnull=True, ordem__isnull=True)

                existente = existentes.order_by('-atualizado_em', '-id').first()
            else:
                existente = None

            if existente:
                if peca.veiculo_id:
                    existente.veiculo_id = peca.veiculo_id
                if peca.orcamento_id:
                    existente.orcamento_id = peca.orcamento_id
                if peca.ordem_id:
                    existente.ordem_id = peca.ordem_id
                if peca.fornecedor_tipo:
                    existente.fornecedor_tipo = peca.fornecedor_tipo
                if peca.fornecedor_id:
                    existente.fornecedor_id = peca.fornecedor_id
                if (peca.fornecedor_nome or '').strip():
                    existente.fornecedor_nome = peca.fornecedor_nome
                if peca.quantidade:
                    existente.quantidade = peca.quantidade
                if peca.valor_custo is not None:
                    existente.valor_custo = peca.valor_custo
                if peca.percentual_lucro is not None:
                    existente.percentual_lucro = peca.percentual_lucro
                if peca.prazo_compra:
                    existente.prazo_compra = peca.prazo_compra
                if peca.data_compra:
                    existente.data_compra = peca.data_compra
                if peca.prazo_chegada:
                    existente.prazo_chegada = peca.prazo_chegada
                if (peca.observacao or '').strip():
                    existente.observacao = peca.observacao
                if not existente.solicitado_por_id:
                    existente.solicitado_por = request.user

                existente.save()
                messages.info(request, f'Peça "{existente.descricao}" já existia. Atualizei o registro para evitar duplicação.')
                return redirect('pecas:update', pk=existente.pk)

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
        form = PecaForm(initial=initial, cliente_id=cliente_id)
    
    context = {'form': form, 'title': 'Nova Peça'}
    return render(request, 'pecas/peca_form.html', context)


@login_required
def peca_update(request, pk):
    """Editar peça"""
    peca = get_object_or_404(Peca, pk=pk)
    confirmar = (request.GET.get('confirmar') or '').strip() == '1'
    next_url = (request.GET.get('next') or '').strip()
    if request.method == 'POST':
        form = PecaForm(request.POST, instance=peca)
        if form.is_valid():
            instance = form.save(commit=False)
            if confirmar and not instance.data_recebimento:
                from django.utils import timezone
                instance.data_recebimento = timezone.now()
            instance.save()
            form.save_m2m()
            messages.success(request, f'Peça "{peca.descricao}" atualizada com sucesso!')
            if next_url:
                return redirect(next_url)
            return redirect('pecas:list')
    else:
        form = PecaForm(instance=peca)
    
    context = {'form': form, 'title': f'Editar Peça: {peca.descricao}', 'peca': peca, 'confirmar': confirmar, 'next_url': next_url}
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


@login_required
def peca_marcar_recebida(request, pk):
    if request.method != 'POST':
        return redirect('pecas:update', pk=pk)

    perfil = getattr(request.user, 'perfil', '')
    pode_intervir = request.user.is_superuser or perfil in ['admin', 'gerente', 'supervisor', 'financeiro']
    if not pode_intervir:
        messages.error(request, 'Você não tem permissão para confirmar chegada de peça.')
        return redirect(request.META.get('HTTP_REFERER', 'pecas:list'))

    try:
        PecaService.marcar_como_recebida(pk)
        messages.success(request, 'Chegada confirmada. Peça marcada como recebida.')
    except Exception as e:
        messages.error(request, f'Erro ao confirmar chegada: {str(e)}')

    return redirect(request.META.get('HTTP_REFERER', 'pecas:list'))

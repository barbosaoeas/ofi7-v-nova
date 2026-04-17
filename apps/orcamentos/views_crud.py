"""
Views CRUD para Orçamentos (Django Templates)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
import json
from uuid import uuid4

from apps.veiculos.models import Veiculo
from apps.clientes.models import Cliente
from apps.pecas.models import CatalogoPeca
from .models import Orcamento, OrcamentoItem, EtapaPadrao
from .forms import OrcamentoForm, OrcamentoItemFormSet, OrcamentoTerceiroFormSet, OrcamentoPecaFormSet


# ─────────────────────────── LISTAGEM ───────────────────────────

@login_required
def orcamento_list(request):
    """Lista todos os orçamentos com filtros de status e busca"""
    qs = Orcamento.objects.select_related(
        'cliente', 'veiculo', 'criado_por'
    ).prefetch_related('itens').order_by('-criado_em')

    filtro = request.GET.get('filtro', '') or 'aprovados'

    # Filtro por status
    status_filtro = request.GET.get('status', '')
    if status_filtro:
        qs = qs.filter(status=status_filtro)
    else:
        if filtro == 'aprovados':
            qs = qs.filter(status='aprovado')

    # Busca textual
    busca = request.GET.get('q', '').strip()
    if busca:
        from django.db.models import Q
        qs = qs.filter(
            Q(numero__icontains=busca) |
            Q(cliente__nome__icontains=busca) |
            Q(veiculo__placa__icontains=busca)
        )

    # Contagens por status (para os badges do filtro)
    from django.db.models import Count
    contagens = {
        'todos': Orcamento.objects.count(),
        'rascunho': Orcamento.objects.filter(status='rascunho').count(),
        'enviado': Orcamento.objects.filter(status='enviado').count(),
        'aprovado': Orcamento.objects.filter(status='aprovado').count(),
        'entregue': Orcamento.objects.filter(status='entregue').count(),
        'rejeitado': Orcamento.objects.filter(status='rejeitado').count(),
        'cancelado': Orcamento.objects.filter(status='cancelado').count(),
    }

    context = {
        'orcamentos': qs,
        'filtro': filtro,
        'status_filtro': status_filtro,
        'busca': busca,
        'contagens': contagens,
        'status_choices': Orcamento.STATUS_CHOICES,
    }
    return render(request, 'orcamentos/orcamento_list.html', context)


# ─────────────────────────── CRIAÇÃO ────────────────────────────

@login_required
def orcamento_create(request):
    """Cria um novo orçamento com itens dinâmicos"""
    token_atual = request.session.get('orcamento_create_token')
    if request.method == 'POST':
        token_post = (request.POST.get('_submit_token') or '').strip()
        tokens_usados = request.session.get('orcamento_create_tokens_usados', []) or []
        if token_post and token_post in tokens_usados:
            messages.info(request, 'Este orçamento já foi enviado. Evitei duplicar o registro.')
            return redirect('orcamentos:list')

        form = OrcamentoForm(request.POST)
        formset = OrcamentoItemFormSet(request.POST)
        terceiro_formset = OrcamentoTerceiroFormSet(request.POST)
        peca_formset = OrcamentoPecaFormSet(request.POST)

        if form.is_valid() and formset.is_valid() and terceiro_formset.is_valid() and peca_formset.is_valid():
            with transaction.atomic():
                orcamento = form.save(commit=False)
                orcamento.criado_por = request.user
                orcamento.save()

                formset.instance = orcamento
                formset.save()
                
                terceiro_formset.instance = orcamento
                terceiro_formset.save()

                peca_formset.instance = orcamento
                pecas = peca_formset.save(commit=False)
                for p in pecas:
                    p.solicitado_por = request.user
                    p.orcamento = orcamento
                    p.veiculo = orcamento.veiculo
                    p.save()
                for obj in peca_formset.deleted_objects:
                    obj.delete()

                if orcamento.status in ['aprovado', 'retrabalho']:
                    from apps.ordens.services import OrdemServicoService
                    OrdemServicoService.criar_de_orcamento(orcamento.id, request.user)

                if token_post:
                    tokens_usados = request.session.get('orcamento_create_tokens_usados', []) or []
                    tokens_usados.append(token_post)
                    request.session['orcamento_create_tokens_usados'] = tokens_usados[-10:]
                    request.session.pop('orcamento_create_token', None)

            messages.success(request, f'Orçamento {orcamento.numero} criado com sucesso!')
            return redirect('orcamentos:list')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = OrcamentoForm()
        formset = OrcamentoItemFormSet()
        terceiro_formset = OrcamentoTerceiroFormSet()
        peca_formset = OrcamentoPecaFormSet()
        token_atual = uuid4().hex
        request.session['orcamento_create_token'] = token_atual

    etapas = list(EtapaPadrao.objects.filter(ativo=True).values('id', 'nome').order_by('ordem_default', 'nome'))
    fornecedores = list(Cliente.objects.filter(categoria__in=['fornecedor', 'ambos'], ativo=True).values('id', 'nome', 'atividade_fornecedor').order_by('nome'))
    catalogo_pecas = CatalogoPeca.objects.filter(ativo=True).order_by('descricao')
    catalogo_pecas_json = json.dumps([
        {
            'id': p.id,
            'descricao': p.descricao,
            'fornecedor_tipo': p.fornecedor_tipo,
            'quantidade': p.quantidade,
            'valor_custo': str(p.valor_custo) if p.valor_custo is not None else '',
            'percentual_lucro': str(p.percentual_lucro) if p.percentual_lucro is not None else '30.00',
        }
        for p in catalogo_pecas
    ])
    
    context = {
        'form': form,
        'formset': formset,
        'terceiro_formset': terceiro_formset,
        'peca_formset': peca_formset,
        'titulo': 'Novo Orçamento',
        'is_create': True,
        'submit_token': token_atual,
        'etapas_json': json.dumps(etapas),
        'fornecedores_json': json.dumps(fornecedores),
        'catalogo_pecas': catalogo_pecas,
        'catalogo_pecas_json': catalogo_pecas_json,
    }
    return render(request, 'orcamentos/orcamento_form.html', context)


# ─────────────────────────── EDIÇÃO ─────────────────────────────

@login_required
def orcamento_update(request, pk):
    """Edita um orçamento existente"""
    orcamento = get_object_or_404(Orcamento, pk=pk)

    # Bloqueia edição somente se aprovado E já tem OS com etapas criadas
    tem_os = False
    os_vazia = False
    try:
        os_obj = orcamento.ordem_servico
        tem_os = True
        os_vazia = not os_obj.etapas.exists()
    except Exception:
        pass

    if orcamento.status not in ('rascunho', 'enviado'):
        if orcamento.status in ('aprovado', 'retrabalho') and (not tem_os or os_vazia):
            # Permite editar: aprovado sem OS, ou com OS mas sem etapas ainda
            if os_vazia:
                messages.info(request, '⚠️ A OS foi gerada mas ainda não tem etapas. Adicione os itens abaixo e salve — as etapas serão criadas automaticamente.')
            else:
                messages.info(request, '⚠️ Orçamento aprovado sem etapas. Adicione os itens e salve para gerar a OS.')
        elif orcamento.status in ('aprovado', 'retrabalho') and tem_os and not os_vazia:
            messages.warning(request, 'Este orçamento já possui uma OS com etapas e não pode ser editado. Use a programação da OS para ajustes.')
            return redirect('orcamentos:detail', pk=pk)
        elif orcamento.status not in ('aprovado', 'retrabalho', 'rascunho', 'enviado'):
            messages.warning(request, f'Orçamento com status "{orcamento.get_status_display()}" não pode ser editado.')
            return redirect('orcamentos:detail', pk=pk)

    if request.method == 'POST':
        form = OrcamentoForm(request.POST, instance=orcamento)
        formset = OrcamentoItemFormSet(request.POST, instance=orcamento)
        terceiro_formset = OrcamentoTerceiroFormSet(request.POST, instance=orcamento)
        peca_formset = OrcamentoPecaFormSet(request.POST, instance=orcamento)

        if form.is_valid() and formset.is_valid() and terceiro_formset.is_valid() and peca_formset.is_valid():
            with transaction.atomic():
                orcamento_salvo = form.save()
                formset.save()
                terceiro_formset.save()
                pecas = peca_formset.save(commit=False)
                for p in pecas:
                    if not p.solicitado_por_id:
                        p.solicitado_por = request.user
                    p.orcamento = orcamento_salvo
                    p.veiculo = orcamento_salvo.veiculo
                    p.save()
                for obj in peca_formset.deleted_objects:
                    obj.delete()

                if orcamento_salvo.status in ['aprovado', 'retrabalho']:
                    tem_itens = orcamento_salvo.itens.exists()
                    if tem_itens:
                        from apps.ordens.services import OrdemServicoService
                        try:
                            OrdemServicoService.criar_de_orcamento(orcamento_salvo.id, request.user)
                            messages.success(request, '✅ Etapas criadas e OS gerada!')
                        except ValueError as e:
                            if 'etapas' not in str(e):
                                pass  # OS já tinha etapas — normal
                    else:
                        messages.warning(request, '⚠️ Ainda sem etapas. Adicione etapas de serviço para gerar a OS.')

            messages.success(request, f'Orçamento {orcamento.numero} atualizado!')
            return redirect('orcamentos:list')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = OrcamentoForm(instance=orcamento)
        formset = OrcamentoItemFormSet(instance=orcamento)
        terceiro_formset = OrcamentoTerceiroFormSet(instance=orcamento)
        peca_formset = OrcamentoPecaFormSet(instance=orcamento)

    etapas = list(EtapaPadrao.objects.filter(ativo=True).values('id', 'nome').order_by('ordem_default', 'nome'))
    fornecedores = list(Cliente.objects.filter(categoria__in=['fornecedor', 'ambos'], ativo=True).values('id', 'nome', 'atividade_fornecedor').order_by('nome'))
    catalogo_pecas = CatalogoPeca.objects.filter(ativo=True).order_by('descricao')
    catalogo_pecas_json = json.dumps([
        {
            'id': p.id,
            'descricao': p.descricao,
            'fornecedor_tipo': p.fornecedor_tipo,
            'quantidade': p.quantidade,
            'valor_custo': str(p.valor_custo) if p.valor_custo is not None else '',
            'percentual_lucro': str(p.percentual_lucro) if p.percentual_lucro is not None else '30.00',
        }
        for p in catalogo_pecas
    ])
    
    context = {
        'form': form,
        'formset': formset,
        'terceiro_formset': terceiro_formset,
        'peca_formset': peca_formset,
        'orcamento': orcamento,
        'titulo': f'Editar {orcamento.numero}',
        'is_create': False,
        'etapas_json': json.dumps(etapas),
        'fornecedores_json': json.dumps(fornecedores),
        'catalogo_pecas': catalogo_pecas,
        'catalogo_pecas_json': catalogo_pecas_json,
    }
    return render(request, 'orcamentos/orcamento_form.html', context)


# ─────────────────────────── DETALHE ────────────────────────────

@login_required
def orcamento_detail(request, pk):
    """Visualiza o orçamento estilo invoice/proposta"""
    orcamento = get_object_or_404(
        Orcamento.objects.select_related(
            'cliente', 'veiculo__modelo_veiculo__fabricante',
            'veiculo__cor_veiculo', 'criado_por'
        ).prefetch_related('itens'),
        pk=pk
    )
    context = {'orcamento': orcamento}
    return render(request, 'orcamentos/orcamento_detail.html', context)


# ─────────────────────────── EXCLUSÃO ───────────────────────────

@login_required
def orcamento_delete(request, pk):
    """Exclui um orçamento (apenas rascunho)"""
    orcamento = get_object_or_404(Orcamento, pk=pk)

    if orcamento.status != 'rascunho':
        messages.error(request, 'Apenas orçamentos em "Aguardando Resposta" podem ser excluídos.')
        return redirect('orcamentos:detail', pk=pk)

    if request.method == 'POST':
        numero = orcamento.numero
        orcamento.delete()
        messages.success(request, f'Orçamento {numero} excluído.')
        return redirect('orcamentos:list')

    return render(request, 'orcamentos/orcamento_confirm_delete.html', {'orcamento': orcamento})


# ─────────────────────────── MUDAR STATUS ───────────────────────

@login_required
@require_http_methods(['POST'])
def orcamento_mudar_status(request, pk):
    """Altera o status do orçamento via POST"""
    orcamento = get_object_or_404(Orcamento, pk=pk)
    novo_status = request.POST.get('status', '')

    TRANSICOES_VALIDAS = {
        'rascunho': ['enviado', 'cancelado'],
        'enviado': ['aprovado', 'rejeitado', 'cancelado', 'rascunho'],
        'aprovado': ['retrabalho', 'entregue'],
        'entregue': [],
        'retrabalho': ['aprovado', 'cancelado'],
        'rejeitado': ['rascunho'],
        'cancelado': [],
    }

    permitidos = TRANSICOES_VALIDAS.get(orcamento.status, [])

    if novo_status not in permitidos:
        messages.error(request, f'Não é possível alterar de "{orcamento.get_status_display()}" para "{novo_status}".')
        return redirect('orcamentos:detail', pk=pk)

    STATUS_LABELS = {
        'rascunho': 'Aguardando Resposta',
        'enviado': 'Enviado',
        'aprovado': 'Aprovado',
        'entregue': 'Entregue',
        'retrabalho': 'Retrabalho',
        'rejeitado': 'Rejeitado',
        'cancelado': 'Cancelado',
    }

    orcamento.status = novo_status
    if novo_status in ['aprovado', 'retrabalho'] and not orcamento.perda_total:
        data_prevista_entrega = request.POST.get('data_prevista_entrega', '').strip()
        if data_prevista_entrega:
            orcamento.data_prevista_entrega = data_prevista_entrega
        if novo_status == 'aprovado' and not orcamento.data_prevista_entrega:
            messages.error(request, 'Informe a previsão de entrega para aprovar o orçamento.')
            return redirect('orcamentos:detail', pk=pk)
        orcamento.save(update_fields=['status', 'data_prevista_entrega'])
    else:
        orcamento.save(update_fields=['status'])

    if novo_status in ['aprovado', 'retrabalho']:
        tem_os = hasattr(orcamento, 'ordem_servico') and orcamento.ordem_servico is not None
        tem_itens = orcamento.itens.exists()
        if orcamento.perda_total:
            messages.success(request, '✅ Orçamento aprovado como Perda Total (não gera OS).')
        elif not tem_os and tem_itens:
            from apps.ordens.services import OrdemServicoService
            try:
                OrdemServicoService.criar_de_orcamento(orcamento.id, request.user)
                if novo_status == 'retrabalho':
                    messages.success(request, '✅ Retrabalho registrado e OS gerada automaticamente!')
                else:
                    messages.success(request, '✅ Orçamento aprovado e OS gerada automaticamente!')
            except Exception as e:
                messages.error(request, f'Orçamento aprovado, mas erro ao gerar OS: {str(e)}')
        elif not tem_itens:
            if novo_status == 'retrabalho':
                messages.warning(request, '⚠️ Retrabalho marcado, mas ainda sem etapas. Edite para adicionar etapas — a OS será gerada ao salvar.')
            else:
                messages.warning(request, '⚠️ Orçamento aprovado! Ele ainda não tem etapas de serviço. Edite-o para adicionar etapas — a OS será gerada ao salvar.')
        else:
            if novo_status == 'retrabalho':
                messages.success(request, '✅ Retrabalho registrado (OS já existente mantida).')
            else:
                messages.success(request, '✅ Orçamento aprovado (OS já existente mantida).')
    else:
        messages.success(request, f'Orçamento marcado como {STATUS_LABELS.get(novo_status, novo_status)}.')

    return redirect('orcamentos:detail', pk=pk)


# ─────────────────────────── GERAR OS ───────────────────────────

@login_required
@require_http_methods(['POST'])
def orcamento_gerar_os(request, pk):
    """Gera uma Ordem de Serviço a partir do orçamento aprovado"""
    orcamento = get_object_or_404(Orcamento, pk=pk)

    if orcamento.status not in ['aprovado', 'retrabalho']:
        messages.error(request, 'O orçamento precisa estar Aprovado ou em Retrabalho para gerar uma OS.')
        return redirect('orcamentos:detail', pk=pk)

    if orcamento.perda_total:
        messages.error(request, 'Orçamento marcado como Perda Total não gera Ordem de Serviço.')
        return redirect('orcamentos:detail', pk=pk)

    try:
        from apps.ordens.services import OrdemServicoService
        ordem = OrdemServicoService.criar_de_orcamento(
            orcamento_id=orcamento.id,
            criado_por=request.user
        )
        messages.success(request, f'Ordem de Serviço {ordem.numero} gerada com sucesso!')
        # Redirecionar para a OS criada (quando existir a view de detalhe da OS)
        return redirect('orcamentos:detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Erro ao gerar OS: {str(e)}')
        return redirect('orcamentos:detail', pk=pk)


# ─────────────────────── HTMX ─────────────

@login_required
def veiculos_por_cliente(request):
    """
    Endpoint HTMX: retorna <option>s de veículos filtrados pelo cliente selecionado.
    """
    cliente_id = request.GET.get('cliente', '')
    veiculos = []
    total_cliente = 0

    if cliente_id:
        base = Veiculo.objects.filter(cliente_id=cliente_id)
        total_cliente = base.count()
        veiculos = (
            base.exclude(ordens__status__in=['aberta', 'em_andamento', 'aguardando_peca', 'concluida'])
            .select_related('modelo_veiculo__fabricante', 'cor_veiculo')
            .distinct()
            .order_by('placa')
        )

    return render(request, 'orcamentos/_veiculos_options.html', {
        'veiculos': veiculos,
        'selected_id': request.GET.get('veiculo_atual', ''),
        'total_cliente': total_cliente,
    })


@login_required
def verificar_capacidade_data(request):
    """
    Endpoint HTMX: verifica a capacidade programada de mão de obra para a semana da data agendada.
    Retorna um aviso se a capacidade estiver alta.
    """
    from datetime import datetime, timedelta
    from decimal import Decimal
    from apps.ordens.models import OrdemEtapa
    from apps.funcionarios.models import Funcionario

    data_str = request.GET.get('data_agendada', '')
    if not data_str:
        return HttpResponse("")

    try:
        data_agendada = datetime.strptime(data_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return HttpResponse("")

    # Determinar a semana (Segunda a Domingo)
    inicio_semana = data_agendada - timedelta(days=data_agendada.weekday())
    fim_semana = inicio_semana + timedelta(days=6)

    # Buscar todas as horas programadas nesta semana
    etapas = OrdemEtapa.objects.filter(
        data_programada__gte=inicio_semana,
        data_programada__lte=fim_semana
    ).exclude(status='finalizada').values_list('horas_orcadas', flat=True)

    total_horas_programadas = sum((h or Decimal('0') for h in etapas), Decimal('0'))

    # Capacidade total (ex: 44h * qtd de operacionais ativos)
    qtd_operacionais = Funcionario.objects.filter(ativo=True).count()
    capacidade_total = Decimal('44') * Decimal(qtd_operacionais)

    if capacidade_total > 0:
        ocupacao = (total_horas_programadas / capacidade_total) * 100
        
        if ocupacao >= 90:
            html = f"""
            <div class="mt-2 text-xs font-semibold text-red-600 bg-red-50 p-2 rounded border border-red-200 flex items-start gap-2">
                <i class="fas fa-exclamation-triangle mt-0.5"></i>
                <div>
                    <strong>Risco de atraso:</strong> A oficina já está com {ocupacao:.0f}% da capacidade ocupada nesta semana ({inicio_semana.strftime('%d/%m')} a {fim_semana.strftime('%d/%m')}).
                </div>
            </div>
            """
            return HttpResponse(html)
        elif ocupacao >= 75:
            html = f"""
            <div class="mt-2 text-xs font-semibold text-yellow-700 bg-yellow-50 p-2 rounded border border-yellow-200 flex items-start gap-2">
                <i class="fas fa-info-circle mt-0.5"></i>
                <div>
                    <strong>Atenção:</strong> A ocupação da oficina está em {ocupacao:.0f}% nesta semana ({inicio_semana.strftime('%d/%m')} a {fim_semana.strftime('%d/%m')}).
                </div>
            </div>
            """
            return HttpResponse(html)

    return HttpResponse("")

"""
Views CRUD para Orçamentos (Django Templates)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.urls import reverse
import json
from uuid import uuid4

from apps.veiculos.models import Veiculo
from apps.clientes.models import Cliente
from apps.pecas.models import CatalogoPeca
from .models import Orcamento, OrcamentoItem, EtapaPadrao, OrcamentoAditivo, OrcamentoRevisao
from .forms import (
    OrcamentoForm,
    OrcamentoItemFormSet,
    OrcamentoTerceiroFormSet,
    OrcamentoPecaFormSet,
    OrcamentoAditivoForm,
    AditivoPecaFormSet,
)

def _snapshot_orcamento_para_revisao(orcamento):
    def _date(d):
        return d.isoformat() if d else None

    itens = [
        {
            'id': i.id,
            'descricao': i.descricao,
            'etapa': i.etapa.nome if i.etapa else None,
            'horas_previstas': str(i.horas_previstas) if i.horas_previstas is not None else None,
            'valor': str(i.valor) if i.valor is not None else None,
            'retrabalho': bool(getattr(i, 'retrabalho', False)),
            'ordem': i.ordem,
        }
        for i in orcamento.itens.all().select_related('etapa')
    ]

    terceiros = [
        {
            'id': t.id,
            'descricao': t.descricao,
            'fornecedor': t.fornecedor.nome if t.fornecedor else None,
            'valor': str(t.valor) if t.valor is not None else None,
        }
        for t in orcamento.servicos_terceiros.all().select_related('fornecedor')
    ]

    pecas = [
        {
            'id': p.id,
            'descricao': p.descricao,
            'fornecedor_tipo': p.fornecedor_tipo,
            'fornecedor_nome': p.fornecedor_nome,
            'quantidade': p.quantidade,
            'valor_custo': str(p.valor_custo) if p.valor_custo is not None else None,
            'percentual_lucro': str(p.percentual_lucro) if p.percentual_lucro is not None else None,
            'valor_venda': str(p.valor_venda) if p.valor_venda is not None else None,
            'prazo_chegada': _date(p.prazo_chegada),
            'status': p.status,
            'data_recebimento': p.data_recebimento.isoformat() if p.data_recebimento else None,
            'aditivo': p.aditivo.numero if getattr(p, 'aditivo', None) else None,
        }
        for p in orcamento.pecas.all().select_related('aditivo')
    ]

    os_data = None
    try:
        os_obj = orcamento.ordem_servico
        os_data = {
            'id': os_obj.id,
            'numero': os_obj.numero,
            'status': os_obj.status,
            'data_chegada_veiculo': _date(os_obj.data_chegada_veiculo),
            'data_previsao_entrega': _date(os_obj.data_previsao_entrega),
            'etapas': [
                {
                    'id': e.id,
                    'nome': e.nome,
                    'status': e.status,
                    'data_programada': _date(e.data_programada),
                    'funcionario': e.funcionario.nome_completo if e.funcionario else None,
                    'auxiliares': [a.nome_completo for a in e.auxiliares.all()],
                }
                for e in os_obj.etapas.all().select_related('funcionario').prefetch_related('auxiliares').order_by('sequencia', 'id')
            ],
        }
    except Exception:
        os_data = None

    return {
        'orcamento': {
            'id': orcamento.id,
            'numero': orcamento.numero,
            'status': orcamento.status,
            'validade': _date(orcamento.validade),
            'data_agendada': _date(orcamento.data_agendada),
            'data_prevista_entrega': _date(orcamento.data_prevista_entrega),
            'desconto': str(orcamento.desconto) if orcamento.desconto is not None else None,
            'observacoes': orcamento.observacoes or '',
        },
        'itens': itens,
        'terceiros': terceiros,
        'pecas': pecas,
        'os': os_data,
    }


# ─────────────────────────── LISTAGEM ───────────────────────────

@login_required
def orcamento_list(request):
    """Lista todos os orçamentos com filtros de status e busca"""
    try:
        from django.utils import timezone
        from django.db.utils import OperationalError, ProgrammingError
        try:
            hoje = timezone.now().date()
            Orcamento.objects.filter(status='entregue', inativo=False).update(inativo=True)
            Orcamento.objects.filter(status__in=['rejeitado', 'cancelado'], inativo=False).update(inativo=True)
            Orcamento.objects.filter(status__in=['rascunho', 'enviado'], inativo=False, validade__lt=hoje).update(inativo=True)
            Orcamento.objects.filter(status__in=['aprovado', 'retrabalho'], inativo=True).update(inativo=False)
        except (OperationalError, ProgrammingError):
            pass
    except Exception:
        pass

    qs = Orcamento.objects.select_related(
        'cliente', 'veiculo', 'criado_por'
    ).prefetch_related('itens').order_by('-criado_em')

    filtro = request.GET.get('filtro', '') or 'aprovados'

    # Filtro por status
    status_filtro = request.GET.get('status', '')
    if status_filtro:
        qs = qs.filter(status=status_filtro)
    else:
        if filtro == 'pendentes':
            qs = qs.filter(status__in=['rascunho', 'enviado']).order_by('criado_em')
        elif filtro == 'aprovados':
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
    revisao_id = (request.GET.get('revisao') or request.session.get('orcamento_revisao_id') or '').strip()
    revisao = None
    if revisao_id:
        try:
            revisao = OrcamentoRevisao.objects.filter(
                pk=int(revisao_id),
                orcamento=orcamento,
                confirmado_em__isnull=True,
            ).first()
        except Exception:
            revisao = None
    if revisao:
        request.session['orcamento_revisao_id'] = str(revisao.id)

    # Bloqueia edição somente se aprovado E já tem OS com etapas criadas
    tem_os = False
    os_vazia = False
    try:
        os_obj = orcamento.ordem_servico
        tem_os = True
        os_vazia = not os_obj.etapas.exists()
    except Exception:
        pass

    if not revisao and orcamento.status not in ('rascunho', 'enviado'):
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
    if revisao:
        messages.info(request, f'🔁 Modo Revisão: você está editando este orçamento para registrar alterações ({revisao.numero}).')

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

                if revisao:
                    try:
                        os_obj = orcamento_salvo.ordem_servico
                        update_fields = []
                        if orcamento_salvo.data_agendada and os_obj.data_chegada_veiculo != orcamento_salvo.data_agendada:
                            os_obj.data_chegada_veiculo = orcamento_salvo.data_agendada
                            update_fields.append('data_chegada_veiculo')
                        if (
                            orcamento_salvo.data_prevista_entrega
                            and (
                                not os_obj.data_previsao_entrega
                                or orcamento_salvo.data_prevista_entrega > os_obj.data_previsao_entrega
                            )
                        ):
                            os_obj.data_previsao_entrega = orcamento_salvo.data_prevista_entrega
                            update_fields.append('data_previsao_entrega')
                        if update_fields:
                            os_obj.save(update_fields=update_fields)

                        from apps.ordens.models import OrdemEtapa
                        from apps.ordens.services import OrdemEtapaService, OrdemServicoService

                        existentes_por_sequencia = {
                            e.sequencia: e
                            for e in os_obj.etapas.all()
                        }
                        sequencias_usadas = set(existentes_por_sequencia.keys())
                        max_sequencia = max(sequencias_usadas) if sequencias_usadas else 0

                        itens = list(orcamento_salvo.itens.all().select_related('etapa'))
                        for item in itens:
                            nome_etapa = item.etapa.nome if item.etapa else 'Serviço Adicional'
                            descricao = (item.descricao or '').strip()

                            sequencia_desejada = OrdemEtapaService.obter_sequencia_por_nome(nome_etapa)
                            if sequencia_desejada in sequencias_usadas:
                                etapa_existente = existentes_por_sequencia.get(sequencia_desejada)
                                if (
                                    etapa_existente
                                    and etapa_existente.status in ['aguardando', 'programado']
                                    and etapa_existente.nome == nome_etapa
                                ):
                                    update_fields_etapa = []
                                    if descricao and etapa_existente.descricao != descricao:
                                        etapa_existente.descricao = descricao
                                        update_fields_etapa.append('descricao')
                                    valor_servico = (item.valor or 0) if not getattr(item, 'retrabalho', False) else 0
                                    if etapa_existente.valor_servico != valor_servico:
                                        etapa_existente.valor_servico = valor_servico
                                        update_fields_etapa.append('valor_servico')
                                    if etapa_existente.horas_orcadas != item.horas_previstas:
                                        etapa_existente.horas_orcadas = item.horas_previstas
                                        update_fields_etapa.append('horas_orcadas')
                                    if update_fields_etapa:
                                        etapa_existente.save(update_fields=update_fields_etapa)
                                continue

                            if sequencia_desejada in sequencias_usadas:
                                max_sequencia += 1
                                sequencia_desejada = max_sequencia

                            etapa_nova = OrdemEtapa.objects.create(
                                ordem=os_obj,
                                nome=nome_etapa,
                                descricao=descricao,
                                sequencia=sequencia_desejada,
                                valor_servico=(item.valor or 0) if not getattr(item, 'retrabalho', False) else 0,
                                horas_orcadas=item.horas_previstas,
                                status='aguardando',
                            )
                            existentes_por_sequencia[etapa_nova.sequencia] = etapa_nova
                            sequencias_usadas.add(etapa_nova.sequencia)

                        OrdemServicoService.atualizar_status_ordem(os_obj)
                    except Exception:
                        pass

                if not revisao and orcamento_salvo.status in ['aprovado', 'retrabalho']:
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
            if revisao:
                return redirect('orcamentos:detail', pk=orcamento.pk)
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
    from django.db.models import Prefetch
    from apps.pecas.models import Peca

    orcamento = get_object_or_404(
        Orcamento.objects.select_related(
            'cliente', 'veiculo__modelo_veiculo__fabricante',
            'veiculo__cor_veiculo', 'criado_por'
        ).prefetch_related(
            'itens',
            'aditivos',
            'aditivos__pecas',
            Prefetch(
                'pecas',
                queryset=Peca.objects.select_related('aditivo', 'etapa_bloqueada').order_by('-criado_em', '-id'),
            ),
        ),
        pk=pk
    )
    revisao_aberta = OrcamentoRevisao.objects.filter(
        orcamento=orcamento,
        confirmado_em__isnull=True,
    ).order_by('-criado_em').first()
    context = {'orcamento': orcamento, 'revisao_aberta': revisao_aberta}
    return render(request, 'orcamentos/orcamento_detail.html', context)


@login_required
@require_http_methods(['POST'])
def orcamento_revisao_iniciar(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk)
    url_editar = reverse('orcamentos:update', kwargs={'pk': pk})

    revisao_aberta = OrcamentoRevisao.objects.filter(
        orcamento=orcamento,
        confirmado_em__isnull=True,
    ).order_by('-criado_em').first()
    if revisao_aberta:
        request.session['orcamento_revisao_id'] = str(revisao_aberta.id)
        return redirect(f"{url_editar}?revisao={revisao_aberta.id}")

    snapshot_antes = _snapshot_orcamento_para_revisao(orcamento)
    revisao = OrcamentoRevisao.objects.create(
        orcamento=orcamento,
        criado_por=request.user,
        motivo=(request.POST.get('motivo') or '').strip(),
        snapshot_antes=snapshot_antes,
    )
    request.session['orcamento_revisao_id'] = str(revisao.id)
    return redirect(f"{url_editar}?revisao={revisao.id}")


@login_required
@require_http_methods(['POST'])
def orcamento_revisao_confirmar(request, pk, revisao_id):
    orcamento = get_object_or_404(Orcamento, pk=pk)
    revisao = get_object_or_404(OrcamentoRevisao, pk=revisao_id, orcamento=orcamento)

    if revisao.confirmado_em:
        return redirect('orcamentos:revisao_imprimir', pk=pk, revisao_id=revisao.pk)

    revisao.snapshot_depois = _snapshot_orcamento_para_revisao(orcamento)
    revisao.confirmado_em = timezone.now()
    revisao.save(update_fields=['snapshot_depois', 'confirmado_em'])
    request.session.pop('orcamento_revisao_id', None)
    return redirect('orcamentos:revisao_imprimir', pk=pk, revisao_id=revisao.pk)


@login_required
def orcamento_revisao_imprimir(request, pk, revisao_id):
    orcamento = get_object_or_404(Orcamento.objects.select_related('cliente', 'veiculo'), pk=pk)
    revisao = get_object_or_404(OrcamentoRevisao, pk=revisao_id, orcamento=orcamento)

    depois = revisao.snapshot_depois or _snapshot_orcamento_para_revisao(orcamento)
    antes = revisao.snapshot_antes or {}
    return render(request, 'orcamentos/orcamento_revisao_print.html', {
        'orcamento': orcamento,
        'revisao': revisao,
        'antes': antes,
        'depois': depois,
    })


@login_required
def orcamento_aditivo_pecas_create(request, pk):
    orcamento = get_object_or_404(
        Orcamento.objects.select_related('cliente', 'veiculo', 'criado_por').prefetch_related('aditivos'),
        pk=pk
    )

    if orcamento.status not in ['aprovado', 'retrabalho']:
        messages.error(request, 'Aditivo só pode ser criado para orçamento aprovado/retrabalho.')
        return redirect('orcamentos:detail', pk=pk)

    if not hasattr(orcamento, 'ordem_servico') or not orcamento.ordem_servico:
        messages.error(request, 'Aditivo de peças exige uma OS gerada para vincular o controle de peças.')
        return redirect('orcamentos:detail', pk=pk)

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

    if request.method == 'POST':
        with transaction.atomic():
            aditivo = OrcamentoAditivo.objects.create(orcamento=orcamento, criado_por=request.user)
            form = OrcamentoAditivoForm(request.POST, instance=aditivo)
            formset = AditivoPecaFormSet(request.POST, instance=aditivo)

            if form.is_valid() and formset.is_valid():
                tem_peca = any(
                    f.cleaned_data
                    and not f.cleaned_data.get('DELETE', False)
                    and f.cleaned_data.get('catalogo')
                    for f in formset.forms
                )
                if not tem_peca:
                    aditivo.delete()
                    messages.error(request, 'Adicione ao menos 1 peça no aditivo.')
                    context = {
                        'orcamento': orcamento,
                        'form': form,
                        'formset': formset,
                        'catalogo_pecas': catalogo_pecas,
                        'catalogo_pecas_json': catalogo_pecas_json,
                    }
                    return render(request, 'orcamentos/orcamento_aditivo_pecas_form.html', context)

                aditivo = form.save()

                pecas = formset.save(commit=False)
                for peca in pecas:
                    peca.solicitado_por = request.user
                    peca.orcamento = orcamento
                    peca.veiculo = orcamento.veiculo
                    peca.ordem = orcamento.ordem_servico
                    peca.aditivo = aditivo
                    peca.save()
                for obj in formset.deleted_objects:
                    obj.delete()

                messages.success(request, f'Aditivo {aditivo.numero} criado.')
                return redirect('orcamentos:aditivo_imprimir', pk=orcamento.pk, aditivo_id=aditivo.pk)

            messages.error(request, 'Corrija os erros do formulário.')
            context = {
                'orcamento': orcamento,
                'form': form,
                'formset': formset,
                'catalogo_pecas': catalogo_pecas,
                'catalogo_pecas_json': catalogo_pecas_json,
            }
            return render(request, 'orcamentos/orcamento_aditivo_pecas_form.html', context)

    form = OrcamentoAditivoForm()
    formset = AditivoPecaFormSet()
    context = {
        'orcamento': orcamento,
        'form': form,
        'formset': formset,
        'catalogo_pecas': catalogo_pecas,
        'catalogo_pecas_json': catalogo_pecas_json,
    }
    return render(request, 'orcamentos/orcamento_aditivo_pecas_form.html', context)


@login_required
def orcamento_aditivo_imprimir(request, pk, aditivo_id):
    orcamento = get_object_or_404(Orcamento.objects.select_related('cliente', 'veiculo'), pk=pk)
    aditivo = get_object_or_404(OrcamentoAditivo.objects.select_related('orcamento', 'criado_por'), pk=aditivo_id, orcamento=orcamento)

    pecas = aditivo.pecas.all().order_by('-criado_em', '-id')
    total = sum((p.valor_venda or 0) * (p.quantidade or 1) for p in pecas)
    context = {
        'orcamento': orcamento,
        'aditivo': aditivo,
        'pecas': pecas,
        'total': total,
    }
    return render(request, 'orcamentos/orcamento_aditivo_print.html', context)


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
        veiculos_disponiveis = (
            base.exclude(ordens__status__in=['aberta', 'em_andamento', 'aguardando_peca'])
            .select_related('modelo_veiculo__fabricante', 'cor_veiculo')
            .distinct()
        )
        selected_id = request.GET.get('veiculo_atual', '')
        if selected_id:
            veiculos = (veiculos_disponiveis | base.filter(pk=selected_id)).distinct().order_by('placa')
        else:
            veiculos = veiculos_disponiveis.order_by('placa')

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


@login_required
def relatorio_orcamentos_entregas(request):
    from datetime import date, datetime
    import calendar
    from django.db.models import (
        Q,
        Sum,
        Count,
        F,
        Value,
        DecimalField,
        ExpressionWrapper,
    )
    from django.db.models.functions import Coalesce

    perfil = getattr(request.user, 'perfil', '')
    pode_ver = request.user.is_superuser or perfil in ['admin', 'gerente', 'supervisor', 'financeiro', 'orcamentista']
    if not pode_ver:
        messages.error(request, 'Você não tem permissão para acessar este relatório.')
        return redirect('dashboard:index')

    hoje = date.today()
    ini_padrao = hoje.replace(day=1)
    fim_padrao = date(hoje.year, hoje.month, calendar.monthrange(hoje.year, hoje.month)[1])

    data_inicio_str = request.GET.get('de') or ini_padrao.isoformat()
    data_fim_str = request.GET.get('ate') or fim_padrao.isoformat()
    status_filtro = request.GET.get('status') or 'aprovado'
    incluir_perda_total = (request.GET.get('perda_total') or '') == '1'
    incluir_retrabalho = (request.GET.get('retrabalho') or '') == '1'
    somente_risco = (request.GET.get('risco') or '') == '1'
    busca = (request.GET.get('q') or '').strip()

    try:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        data_inicio = ini_padrao
        data_fim = fim_padrao

    status_base = []
    if status_filtro == 'aprovado':
        status_base = ['aprovado']
    elif status_filtro == 'entregue':
        status_base = ['entregue']
    elif status_filtro == 'aprovado_entregue':
        status_base = ['aprovado', 'entregue']
    else:
        status_base = ['aprovado', 'entregue']

    if incluir_retrabalho and 'retrabalho' not in status_base:
        status_base.append('retrabalho')

    qs = (
        Orcamento.objects.select_related('cliente', 'veiculo', 'criado_por')
        .filter(
            data_prevista_entrega__isnull=False,
            data_prevista_entrega__gte=data_inicio,
            data_prevista_entrega__lte=data_fim,
            status__in=status_base,
        )
    )

    if not incluir_perda_total:
        qs = qs.filter(perda_total=False)

    if busca:
        qs = qs.filter(
            Q(numero__icontains=busca)
            | Q(cliente__nome__icontains=busca)
            | Q(veiculo__placa__icontains=busca)
        )

    if somente_risco:
        qs = qs.filter(pecas__status__in=['solicitada', 'falta_comprar', 'comprada', 'atrasada']).distinct()

    total_servicos_expr = Coalesce(Sum('itens__valor', filter=Q(itens__retrabalho=False)), Value(0), output_field=DecimalField())
    prejuizo_retrabalho_expr = Coalesce(Sum('itens__valor', filter=Q(itens__retrabalho=True)), Value(0), output_field=DecimalField())
    total_pecas_expr = Coalesce(Sum('pecas__valor_venda', filter=Q(pecas__fornecedor_tipo='escritorio')), Value(0), output_field=DecimalField())
    total_terceiros_expr = Coalesce(Sum('servicos_terceiros__valor'), Value(0), output_field=DecimalField())

    total_geral_expr = ExpressionWrapper(
        total_servicos_expr + total_pecas_expr + total_terceiros_expr,
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    total_com_desconto_expr = ExpressionWrapper(
        total_geral_expr - Coalesce(F('desconto'), Value(0), output_field=DecimalField()),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )

    qs = qs.annotate(
        total_servicos=total_servicos_expr,
        prejuizo_retrabalho=prejuizo_retrabalho_expr,
        total_pecas=total_pecas_expr,
        total_terceiros=total_terceiros_expr,
        total_geral=total_geral_expr,
        total_com_desconto=total_com_desconto_expr,
        pecas_pendentes=Count('pecas', filter=Q(pecas__status__in=['solicitada', 'falta_comprar', 'comprada', 'atrasada']), distinct=True),
        pecas_atrasadas=Count('pecas', filter=Q(pecas__status='atrasada'), distinct=True),
    ).order_by('data_prevista_entrega', 'criado_em')

    totais = qs.aggregate(
        qtd=Count('id', distinct=True),
        servicos=Coalesce(Sum('total_servicos'), Value(0), output_field=DecimalField()),
        pecas=Coalesce(Sum('total_pecas'), Value(0), output_field=DecimalField()),
        terceiros=Coalesce(Sum('total_terceiros'), Value(0), output_field=DecimalField()),
        total=Coalesce(Sum('total_com_desconto'), Value(0), output_field=DecimalField()),
        com_peca_pendente=Count('id', filter=Q(pecas_pendentes__gt=0), distinct=True),
        com_peca_atrasada=Count('id', filter=Q(pecas_atrasadas__gt=0), distinct=True),
    )

    top_maiores = qs.order_by('-total_com_desconto', '-criado_em')[:5]

    context = {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'data_inicio_str': data_inicio_str,
        'data_fim_str': data_fim_str,
        'status_filtro': status_filtro,
        'incluir_perda_total': incluir_perda_total,
        'incluir_retrabalho': incluir_retrabalho,
        'somente_risco': somente_risco,
        'busca': busca,
        'orcamentos': qs[:1000],
        'top_maiores': top_maiores,
        'totais': {
            'qtd': totais.get('qtd') or 0,
            'servicos': totais.get('servicos') or 0,
            'pecas': totais.get('pecas') or 0,
            'terceiros': totais.get('terceiros') or 0,
            'total': totais.get('total') or 0,
            'com_peca_pendente': totais.get('com_peca_pendente') or 0,
            'com_peca_atrasada': totais.get('com_peca_atrasada') or 0,
        },
    }
    return render(request, 'orcamentos/relatorio_orcamentos_entregas.html', context)

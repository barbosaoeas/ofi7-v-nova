from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from datetime import date

from .models import OrdemServico
from .forms import OrdemServicoForm, OrdemEtapaFormSet

@login_required
def ordem_list(request):
    """Lista as Ordens de Serviço (mesma interface do painel principal ou tabela simples)"""
    # Esta view serve apenas de base para voltar da edição
    # O ideal é redirecionar para o painel kanban se for a gestão principal
    filtro = request.GET.get('filtro', '') or 'nao_concluidas'

    base_qs = OrdemServico.objects.select_related('cliente', 'veiculo').order_by('-criado_em')
    qs = base_qs
    if filtro != 'todas':
        qs = qs.exclude(status__in=['concluida', 'entregue'])

    context = {
        'ordens': qs,
        'filtro': filtro,
        'hoje': date.today(),
        'contagens': {
            'todas': base_qs.count(),
            'nao_concluidas': base_qs.exclude(status__in=['concluida', 'entregue']).count(),
        }
    }
    return render(request, 'ordens/ordem_list.html', context)

@login_required
def ordem_update(request, pk):
    """Edita a Ordem de Serviço e programa suas etapas"""
    ordem = get_object_or_404(OrdemServico.objects.select_related('cliente', 'veiculo', 'orcamento'), pk=pk)
    hoje = date.today()
    chegada_futura = bool(ordem.data_chegada_veiculo and ordem.data_chegada_veiculo > hoje)

    try:
        tem_mecanica = ordem.orcamento.itens.filter(etapa__nome__icontains='mec').exists()
    except Exception:
        tem_mecanica = False

    if tem_mecanica:
        try:
            from apps.ordens.models import OrdemEtapa
            from apps.orcamentos.models import OrcamentoItem

            with transaction.atomic():
                etapas = list(OrdemEtapa.objects.select_for_update().filter(ordem=ordem).order_by('sequencia', 'id'))

                etapas_prep = [
                    e for e in etapas
                    if e.nome and 'prepara' in e.nome.lower() and 'entreg' in e.nome.lower()
                ]
                etapas_mec = [e for e in etapas if e.nome and 'mec' in e.nome.lower()]

                item_mec = (
                    OrcamentoItem.objects.filter(orcamento=ordem.orcamento, etapa__nome__icontains='mec')
                    .select_related('etapa')
                    .order_by('id')
                    .first()
                )
                item_prep = (
                    OrcamentoItem.objects.filter(orcamento=ordem.orcamento)
                    .filter(etapa__nome__icontains='prepara')
                    .filter(etapa__nome__icontains='entreg')
                    .select_related('etapa')
                    .order_by('id')
                    .first()
                )

                mec_stage = etapas_mec[0] if etapas_mec else (etapas_prep[0] if len(etapas_prep) >= 2 else None)
                if mec_stage and mec_stage in etapas_prep:
                    etapas_prep = [e for e in etapas_prep if e.id != mec_stage.id]

                prep_stage = etapas_prep[0] if etapas_prep else None

                if not mec_stage and item_mec:
                    mec_stage = OrdemEtapa(
                        ordem=ordem,
                        nome='Mecânica',
                        descricao=item_mec.descricao,
                        sequencia=8,
                        valor_servico=(item_mec.valor if not getattr(item_mec, 'retrabalho', False) else 0),
                        horas_orcadas=item_mec.horas_previstas,
                        status='aguardando',
                    )
                    if hasattr(mec_stage, 'execucao'):
                        mec_stage.execucao = getattr(item_mec, 'execucao', 'oficina') or 'oficina'
                    mec_stage.save()
                    etapas.append(mec_stage)

                if not prep_stage and item_prep:
                    prep_stage = OrdemEtapa(
                        ordem=ordem,
                        nome='Preparação Entrega',
                        descricao=item_prep.descricao,
                        sequencia=9,
                        valor_servico=(item_prep.valor if not getattr(item_prep, 'retrabalho', False) else 0),
                        horas_orcadas=item_prep.horas_previstas,
                        status='aguardando',
                    )
                    if hasattr(prep_stage, 'execucao'):
                        prep_stage.execucao = getattr(item_prep, 'execucao', 'oficina') or 'oficina'
                    prep_stage.save()
                    etapas.append(prep_stage)

                if mec_stage and prep_stage:
                    para_mover = [e for e in etapas if e.sequencia in [8, 9] and e.id not in [mec_stage.id, prep_stage.id]]
                    for idx, e in enumerate(para_mover, start=1):
                        e.sequencia = 90 + idx
                        e.save(update_fields=['sequencia'])

                    mec_stage.sequencia = 80
                    mec_stage.save(update_fields=['sequencia'])
                    prep_stage.sequencia = 81
                    prep_stage.save(update_fields=['sequencia'])

                    if mec_stage.nome != 'Mecânica':
                        mec_stage.nome = 'Mecânica'
                    if item_mec:
                        mec_stage.descricao = item_mec.descricao
                        mec_stage.valor_servico = (item_mec.valor if not getattr(item_mec, 'retrabalho', False) else 0)
                        mec_stage.horas_orcadas = item_mec.horas_previstas
                        if hasattr(mec_stage, 'execucao'):
                            mec_stage.execucao = getattr(item_mec, 'execucao', 'oficina') or 'oficina'
                    mec_stage.sequencia = 8
                    mec_stage.save()

                    if prep_stage.nome != 'Preparação Entrega':
                        prep_stage.nome = 'Preparação Entrega'
                    if item_prep:
                        prep_stage.descricao = item_prep.descricao
                        prep_stage.valor_servico = (item_prep.valor if not getattr(item_prep, 'retrabalho', False) else 0)
                        prep_stage.horas_orcadas = item_prep.horas_previstas
                        if hasattr(prep_stage, 'execucao'):
                            prep_stage.execucao = getattr(item_prep, 'execucao', 'oficina') or 'oficina'
                    prep_stage.sequencia = 9
                    prep_stage.save()

                etapas_prep_todas = list(
                    OrdemEtapa.objects.filter(ordem=ordem)
                    .filter(nome__icontains='prepara')
                    .filter(nome__icontains='entreg')
                    .order_by('sequencia', 'id')
                )
                if len(etapas_prep_todas) > 1:
                    for extra in etapas_prep_todas[1:]:
                        pode_apagar = (
                            extra.status in ['aguardando', 'programado']
                            and not getattr(extra, 'funcionario_id', None)
                            and not getattr(extra, 'data_programada', None)
                            and not getattr(extra, 'data_inicio', None)
                            and not getattr(extra, 'data_fim', None)
                            and getattr(extra, 'horas_gastas_real', None) in [None, 0, '0']
                            and not (getattr(extra, 'descricao', '') or '').strip()
                        )
                        if pode_apagar:
                            extra.delete()
        except Exception:
            pass

    if request.method == 'POST':
        form = OrdemServicoForm(request.POST, instance=ordem)
        formset = OrdemEtapaFormSet(request.POST, instance=ordem)

        if not form.is_valid():
            messages.error(request, 'Corrija os erros abaixo para salvar a OS.')
        else:
            if not formset.is_valid():
                with transaction.atomic():
                    ordem = form.save()
                chegada_futura = bool(ordem.data_chegada_veiculo and ordem.data_chegada_veiculo > hoje)
                messages.warning(request, 'Dados gerais da OS salvos. Corrija as etapas abaixo para salvar a programação.')
            else:
                data_chegada = form.cleaned_data.get('data_chegada_veiculo') or ordem.data_chegada_veiculo

                if data_chegada:
                    for f in formset.forms:
                        if not getattr(f, 'cleaned_data', None):
                            continue
                        if f.cleaned_data.get('DELETE'):
                            continue

                        data_programada = f.cleaned_data.get('data_programada')
                        status_etapa = f.cleaned_data.get('status')

                        if data_programada and data_programada < data_chegada:
                            f.add_error('data_programada', f'Data deve ser a partir de {data_chegada.strftime("%d/%m/%Y")} (chegada do veículo).')

                        if status_etapa == 'programado' and not data_programada:
                            f.add_error('data_programada', 'Informe uma data para programar.')

                        if status_etapa == 'programado' and data_programada and data_programada < data_chegada:
                            f.add_error('status', f'Não pode programar antes da chegada do veículo ({data_chegada.strftime("%d/%m/%Y")}).')

                        if status_etapa in ['em_andamento', 'finalizada'] and hoje < data_chegada:
                            f.add_error('status', f'Não pode iniciar/finalizar antes da chegada do veículo ({data_chegada.strftime("%d/%m/%Y")}).')

                if any(f.errors for f in formset.forms):
                    messages.error(request, 'Corrija os erros abaixo para salvar a programação.')
                else:
                    with transaction.atomic():
                        form.save()
                        formset.save()
                    messages.success(request, f'Programação da OS {ordem.numero} salva com sucesso!')
                    return redirect('orcamentos:detail', pk=ordem.orcamento.pk)
    else:
        form = OrdemServicoForm(instance=ordem)
        formset = OrdemEtapaFormSet(instance=ordem)

    context = {
        'form': form,
        'formset': formset,
        'ordem': ordem,
        'titulo': f'Programar {ordem.numero}',
        'chegada_futura': chegada_futura,
        'hoje': hoje,
    }
    return render(request, 'ordens/ordem_form.html', context)

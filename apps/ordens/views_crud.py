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

    if request.method == 'POST':
        form = OrdemServicoForm(request.POST, instance=ordem)
        formset = OrdemEtapaFormSet(request.POST, instance=ordem)

        if form.is_valid() and formset.is_valid():
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
                context = {
                    'form': form,
                    'formset': formset,
                    'ordem': ordem,
                    'titulo': f'Programar {ordem.numero}',
                    'chegada_futura': chegada_futura,
                    'hoje': hoje,
                }
                return render(request, 'ordens/ordem_form.html', context)

            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, f'Programação da OS {ordem.numero} salva com sucesso!')
            # Pode voltar para o detalhe do orçamento ou uma lista de OS
            return redirect('orcamentos:detail', pk=ordem.orcamento.pk)
        else:
            messages.error(request, 'Corrija os erros abaixo para salvar a programação.')
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

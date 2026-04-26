"""
Views do Dashboard
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import date, timedelta
import calendar

from apps.ordens.models import OrdemServico, OrdemEtapa
from apps.clientes.models import Cliente
from apps.veiculos.models import Veiculo
from apps.comissoes.models import Comissao
from apps.orcamentos.models import Orcamento, OrcamentoItem, OrcamentoServicoTerceiro
from apps.pecas.models import Peca
from .models import ConfiguracaoSistema


@login_required
def dashboard(request):
    """Dashboard principal com filtro de período"""
    if getattr(request.user, 'perfil', '') == 'visual':
        return redirect('kanban:producao')

    hoje = date.today()
    ano_atual = hoje.year
    mes_atual = hoje.month

    # ── Período selecionado ──────────────────────────────────────────
    periodo = request.GET.get('periodo', 'mes_atual')

    if periodo == 'mes_anterior':
        # Primeiro e último dia do mês anterior
        primeiro_dia_mes_anterior = (date(ano_atual, mes_atual, 1) - timedelta(days=1)).replace(day=1)
        ultimo_dia_mes_anterior = date(ano_atual, mes_atual, 1) - timedelta(days=1)
        data_inicio = primeiro_dia_mes_anterior
        data_fim = ultimo_dia_mes_anterior
        label_periodo = primeiro_dia_mes_anterior.strftime('%B/%Y').capitalize()

    elif periodo == 'anual':
        # De 1º de janeiro até hoje
        data_inicio = date(ano_atual, 1, 1)
        data_fim = hoje
        label_periodo = f'Jan a {hoje.strftime("%b/%Y").capitalize()}'

    else:  # mes_atual (padrão)
        data_inicio = date(ano_atual, mes_atual, 1)
        data_fim = hoje
        label_periodo = hoje.strftime('%B/%Y').capitalize()

    # ── Filtros de data ───────────────────────────────────────────────
    # Orçamento: usa data do orçamento (data_orcamento)
    filtro_orcamentos_periodo = Q(data_orcamento__gte=data_inicio, data_orcamento__lte=data_fim)

    # ── Estatísticas gerais (sem filtro de período) ──────────────────
    total_clientes = Cliente.objects.filter(ativo=True).count()
    total_veiculos = Veiculo.objects.count()

    # ── Orçamentos no período ────────────────────────────────────────
    orcamentos_periodo = Orcamento.objects.filter(filtro_orcamentos_periodo)
    total_orcamentos = orcamentos_periodo.count()
    orcamentos_aprovados = orcamentos_periodo.filter(status__in=['aprovado', 'entregue']).count()
    orcamentos_retrabalho = orcamentos_periodo.filter(status='retrabalho').count()

    # Valor total aprovado no período (inclui os já entregues; não conta retrabalho como receita)
    valor_aprovado = orcamentos_periodo.filter(
        status__in=['aprovado', 'entregue']
    ).aggregate(total=Sum('itens__valor', filter=Q(itens__retrabalho=False)))['total'] or 0

    # Perda por retrabalho no período:
    # - Itens marcados como retrabalho
    # - OU orçamentos com status retrabalho (todos os itens são prejuízo)
    perda_retrabalho = OrcamentoItem.objects.filter(
        orcamento__in=orcamentos_periodo
    ).filter(
        Q(retrabalho=True) | Q(orcamento__status='retrabalho')
    ).aggregate(total=Sum('valor'))['total'] or 0

    # ── Ordens de Serviço no período ─────────────────────────────────
    os_abertas = OrdemServico.objects.filter(status='aberta').count()
    os_em_andamento = OrdemServico.objects.filter(status='em_andamento').count()
    os_concluidas_periodo = OrdemServico.objects.filter(
        status='entregue',
        data_entrega__isnull=False,
        data_entrega__date__gte=data_inicio,
        data_entrega__date__lte=data_fim,
    ).count()

    ordens_entregues_periodo = OrdemServico.objects.filter(
        status='entregue',
        data_entrega__isnull=False,
        data_entrega__date__gte=data_inicio,
        data_entrega__date__lte=data_fim,
    )

    faturamento_entregue_servicos = OrdemEtapa.objects.filter(
        ordem__in=ordens_entregues_periodo,
        ordem__orcamento__status__in=['aprovado', 'entregue'],
    ).aggregate(total=Sum('valor_servico'))['total'] or 0

    faturamento_entregue_pecas = Peca.objects.filter(
        ordem__in=ordens_entregues_periodo,
        fornecedor_tipo='escritorio',
    ).aggregate(total=Sum('valor_venda'))['total'] or 0

    faturamento_entregue_terceiros = OrcamentoServicoTerceiro.objects.filter(
        orcamento__ordem_servico__in=ordens_entregues_periodo,
        orcamento__status__in=['aprovado', 'entregue'],
    ).aggregate(total=Sum('valor'))['total'] or 0

    faturamento_entregue_total = (
        faturamento_entregue_servicos
        + faturamento_entregue_pecas
        + faturamento_entregue_terceiros
    )

    # ── Etapas atuais (sem filtro de período — situação atual) ───────
    etapas_em_andamento = OrdemEtapa.objects.filter(status='em_andamento').count()
    etapas_aguardando_peca = OrdemEtapa.objects.filter(status='aguardando_peca').count()

    # Carros no pátio = OS abertas sem nenhuma etapa com funcionário atribuído
    # (inclui: OS sem etapas, OS com etapas todas não programadas)
    os_com_etapas_ids = list(OrdemEtapa.objects.values_list('ordem_id', flat=True).distinct())
    # OS sem nenhuma etapa
    os_sem_etapas = OrdemServico.objects.exclude(id__in=os_com_etapas_ids).count()
    # OS com etapas mas nenhum funcionário atribuído em nenhuma etapa
    ordens_com_func_ids = list(
        OrdemEtapa.objects.filter(funcionario__isnull=False)
        .values_list('ordem_id', flat=True).distinct()
    )
    os_com_etapas_sem_func = OrdemServico.objects.filter(
        id__in=os_com_etapas_ids
    ).exclude(id__in=ordens_com_func_ids).count()

    etapas_no_patio = os_sem_etapas + os_com_etapas_sem_func

    # ── Comissões geradas no período (por data de execução) ───────────
    comissoes_periodo = Comissao.objects.filter(
        Q(
            data_execucao__isnull=False,
            data_execucao__gte=data_inicio,
            data_execucao__lte=data_fim,
        )
        | Q(
            data_execucao__isnull=True,
            criado_em__date__gte=data_inicio,
            criado_em__date__lte=data_fim,
        )
    ).aggregate(total=Sum('valor'))['total'] or 0

    context = {
        # Período
        'periodo': periodo,
        'label_periodo': label_periodo,
        'data_inicio': data_inicio,
        'data_fim': data_fim,

        # Gerais
        'total_clientes': total_clientes,
        'total_veiculos': total_veiculos,

        # Orçamentos
        'total_orcamentos': total_orcamentos,
        'orcamentos_aprovados': orcamentos_aprovados,
        'orcamentos_retrabalho': orcamentos_retrabalho,
        'valor_aprovado': valor_aprovado,
        'perda_retrabalho': perda_retrabalho,

        # OS
        'os_abertas': os_abertas,
        'os_em_andamento': os_em_andamento,
        'os_concluidas_periodo': os_concluidas_periodo,
        'faturamento_entregue_total': faturamento_entregue_total,
        'faturamento_entregue_servicos': faturamento_entregue_servicos,
        'faturamento_entregue_pecas': faturamento_entregue_pecas,
        'faturamento_entregue_terceiros': faturamento_entregue_terceiros,

        # Etapas
        'etapas_em_andamento': etapas_em_andamento,
        'etapas_aguardando_peca': etapas_aguardando_peca,
        'etapas_no_patio': etapas_no_patio,

        # Comissões
        'comissoes_periodo': comissoes_periodo,
    }

    return render(request, 'dashboard/index.html', context)


@login_required
def configuracao_sistema(request):
    from django import forms
    from django.contrib import messages
    from django.shortcuts import redirect

    perfil = getattr(request.user, 'perfil', '')
    if not (request.user.is_superuser or perfil == 'admin'):
        messages.error(request, 'Acesso restrito ao administrador.')
        return redirect('dashboard:index')

    config, _ = ConfiguracaoSistema.objects.get_or_create(id=1)

    class ConfiguracaoSistemaForm(forms.ModelForm):
        class Meta:
            model = ConfiguracaoSistema
            fields = [
                'nome_empresa',
                'cnpj',
                'endereco',
                'telefone',
                'email',
                'site',
                'logo',
                'cor_primaria',
                'cor_rodape',
                'texto_rodape',
            ]
            widgets = {
                'nome_empresa': forms.TextInput(attrs={'class': 'form-input'}),
                'cnpj': forms.TextInput(attrs={'class': 'form-input'}),
                'endereco': forms.TextInput(attrs={'class': 'form-input'}),
                'telefone': forms.TextInput(attrs={'class': 'form-input'}),
                'email': forms.EmailInput(attrs={'class': 'form-input'}),
                'site': forms.TextInput(attrs={'class': 'form-input'}),
                'cor_primaria': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '#2563EB'}),
                'cor_rodape': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '#111827'}),
                'texto_rodape': forms.TextInput(attrs={'class': 'form-input'}),
            }

    if request.method == 'POST':
        form = ConfiguracaoSistemaForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações atualizadas.')
            return redirect('dashboard:configuracao_sistema')
        messages.error(request, 'Corrija os erros do formulário.')
    else:
        form = ConfiguracaoSistemaForm(instance=config)

    return render(request, 'dashboard/configuracao_sistema.html', {'form': form, 'config': config})

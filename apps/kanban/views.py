"""
Views do Kanban de Produção
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import models
from datetime import date, timedelta

from apps.ordens.models import OrdemEtapa, OrdemServico
from apps.producao.models import EtapaPadrao
from apps.funcionarios.models import Funcionario


@login_required
def kanban_producao(request):
    """Kanban principal de produção"""
    
    # Filtros
    data_filter = request.GET.get('data', '') or str(date.today())
    funcionario_filter = request.GET.get('funcionario', '')

    data_alvo = date.today()
    if data_filter:
        try:
            from datetime import datetime
            data_alvo = datetime.strptime(data_filter, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            data_alvo = date.today()
    
    # Buscar etapas padrão na ordem
    etapas_padrao = EtapaPadrao.objects.filter(ativa=True).order_by('sequencia')
    
    # Buscar todas as etapas ativas (excluindo finalizadas)
    etapas = OrdemEtapa.objects.select_related(
        'ordem', 'ordem__cliente', 'ordem__veiculo', 'ordem__orcamento', 'funcionario'
    ).exclude(status='finalizada').order_by('ordem__criado_em')
    
    # Aplicar filtros opcionais
    if funcionario_filter:
        etapas = etapas.filter(funcionario_id=funcionario_filter)

    etapas = list(etapas)
    try:
        from apps.ordens.models import SessaoTrabalho
        sessoes_ativas = SessaoTrabalho.objects.filter(
            etapa_id__in=[e.id for e in etapas if e.status == 'em_andamento'],
            fim__isnull=True,
        ).select_related('etapa')
        sessao_por_etapa = {s.etapa_id: s for s in sessoes_ativas}

        for e in etapas:
            if e.status == 'em_andamento':
                s = sessao_por_etapa.get(e.id)
                if s:
                    e.segundos_em_andamento = int(float(s.minutos_ate_agora()) * 60)
                else:
                    e.segundos_em_andamento = 0
            else:
                e.segundos_em_andamento = 0
    except Exception:
        for e in etapas:
            e.segundos_em_andamento = 0

    from collections import defaultdict
    etapas_por_os = defaultdict(list)
    for e in etapas:
        etapas_por_os[e.ordem_id].append(e)

    forcar_patio_ids = set()
    etapas_para_exibir = []
    for _, lista in etapas_por_os.items():
        lista_ordenada = sorted(lista, key=lambda x: (x.sequencia, x.id))

        ordem_ref = lista_ordenada[0].ordem if lista_ordenada else None
        data_entrada = None
        if ordem_ref:
            data_entrada = getattr(ordem_ref, 'data_chegada_veiculo', None)
            if not data_entrada and getattr(ordem_ref, 'orcamento_id', None):
                data_entrada = getattr(ordem_ref.orcamento, 'data_agendada', None)

        primeira_pendente_encontrada = False
        for e in lista_ordenada:
            if e.status != 'finalizada':
                pular_etapa = bool(getattr(e, 'pular_etapa', False))
                e.bloqueada_sequencia = (primeira_pendente_encontrada and not pular_etapa)
                if not pular_etapa:
                    primeira_pendente_encontrada = True
            else:
                e.bloqueada_sequencia = False

        tem_em_execucao = any(e.status == 'em_andamento' for e in lista_ordenada)
        tem_programada_no_dia = any(e.data_programada == data_alvo for e in lista_ordenada)
        aguardando_entrada = bool(data_entrada and data_alvo < data_entrada and not tem_em_execucao)

        if tem_em_execucao or tem_programada_no_dia:
            for e in lista_ordenada:
                if e.status == 'em_andamento' or e.data_programada == data_alvo:
                    e.data_entrada_veiculo = data_entrada
                    e.aguardando_entrada = aguardando_entrada
                    etapas_para_exibir.append(e)
        else:
            proxima = next((e for e in lista_ordenada if e.status in ['aguardando', 'programado', 'aguardando_peca']), None)
            if proxima:
                forcar_patio_ids.add(proxima.id)
                proxima.data_entrada_veiculo = data_entrada
                proxima.aguardando_entrada = aguardando_entrada
                proxima.sem_programacao = True
                etapas_para_exibir.append(proxima)
    
    # Montar estrutura de colunas
    colunas = {}
    for etapa_padrao in etapas_padrao:
        colunas[etapa_padrao.nome] = {
            'etapa_padrao': etapa_padrao,
            'etapas': []
        }

    seq_to_nome_coluna = {dados['etapa_padrao'].sequencia: nome for nome, dados in colunas.items()}
    nome_patio = seq_to_nome_coluna.get(1, 'Pátio')
    seq_finalizado = max(seq_to_nome_coluna.keys()) if seq_to_nome_coluna else 9
    nome_finalizado = seq_to_nome_coluna.get(seq_finalizado, 'Finalizado')
    seq_prepara_entrega = next(
        (e.sequencia for e in etapas_padrao if 'prepara' in e.nome.lower() and 'entreg' in e.nome.lower()),
        9,
    )
    seq_mecanica = next((e.sequencia for e in etapas_padrao if 'mec' in e.nome.lower()), 8)

    def inferir_sequencia_coluna(nome_etapa):
        if not nome_etapa:
            return None
        n = str(nome_etapa).lower()
        if 'desmont' in n:
            return 2
        if 'funilar' in n:
            return 3
        if 'mec' in n:
            return seq_mecanica
        if 'prepara' in n and 'entreg' in n:
            return seq_prepara_entrega
        if 'prepara' in n:
            return 4
        if 'pintur' in n:
            return 5
        if 'montag' in n:
            return 6
        if 'polim' in n:
            return 7
        if 'final' in n:
            return seq_finalizado
        return None
    
    # Distribuir etapas nas colunas:
    # - Sem funcionário atribuído → Pátio (aguardando programação)
    # - Com funcionário → coluna do serviço pelo nome da etapa
    for etapa in etapas_para_exibir:
        if etapa.id in forcar_patio_ids or not etapa.funcionario_id:
            # Sem responsável → vai para o Pátio
            if nome_patio in colunas:
                etapa.em_patio = True
                if getattr(etapa, 'aguardando_entrada', False) and getattr(etapa, 'data_entrada_veiculo', None):
                    etapa.patio_banner = f'Entrada prevista: {etapa.data_entrada_veiculo.strftime("%d/%m/%Y")}'
                elif not getattr(etapa, 'data_programada', None):
                    etapa.patio_banner = 'Sem programação — Programar'
                elif etapa.data_programada != data_alvo:
                    etapa.patio_banner = f'Programado para {etapa.data_programada.strftime("%d/%m/%Y")}'
                elif not etapa.funcionario_id:
                    etapa.patio_banner = 'Programar'
                colunas[nome_patio]['etapas'].append(etapa)
        else:
            seq = inferir_sequencia_coluna(etapa.nome)
            nome_etapa = seq_to_nome_coluna.get(seq) if seq else etapa.nome
            if nome_etapa in colunas:
                colunas[nome_etapa]['etapas'].append(etapa)
            elif nome_patio in colunas:
                # fallback: se o nome não bater com nenhuma coluna, vai pro Pátio também
                etapa.em_patio = True
                if not getattr(etapa, 'data_programada', None):
                    etapa.patio_banner = 'Sem programação — Programar'
                elif etapa.data_programada != data_alvo:
                    etapa.patio_banner = f'Programado para {etapa.data_programada.strftime("%d/%m/%Y")}'
                colunas[nome_patio]['etapas'].append(etapa)

    ordens_finalizadas = OrdemServico.objects.filter(status='concluida')

    etapas_finalizado = []
    ultimas_por_os = {}
    for e in OrdemEtapa.objects.filter(
        ordem__in=ordens_finalizadas
    ).select_related(
        'ordem', 'ordem__cliente', 'ordem__veiculo', 'funcionario'
    ).order_by('ordem_id', '-sequencia', '-id'):
        if e.ordem_id not in ultimas_por_os:
            ultimas_por_os[e.ordem_id] = e

    for e in ultimas_por_os.values():
        e.nome = 'Finalizado'
        e.bloqueada_sequencia = False
        e.modo_finalizado = True
        e.mostrar_entrega = (e.ordem.status == 'concluida')
        etapas_finalizado.append(e)

    if nome_finalizado in colunas and etapas_finalizado:
        colunas[nome_finalizado]['etapas'].extend(etapas_finalizado)

    if str(getattr(request.user, 'perfil', '') or '').lower() == 'visual':
        for nome, dados in colunas.items():
            limite = 1 if nome == nome_finalizado else 2
            dados['etapas'] = list(dados.get('etapas') or [])[:limite]
    
    # Funcionários para filtro
    funcionarios = Funcionario.objects.filter(ativo=True)
    
    context = {
        'colunas': colunas,
        'etapas_padrao': etapas_padrao,
        'funcionarios': funcionarios,
        'data_filter': data_filter,
        'funcionario_filter': funcionario_filter,
        'data_alvo': data_alvo,
    }
    
    return render(request, 'kanban/producao.html', context)


@login_required
@require_POST
def mover_etapa(request, etapa_id):
    """Move etapa para outra coluna (status)"""
    etapa = get_object_or_404(OrdemEtapa, id=etapa_id)
    nova_etapa_nome = request.POST.get('nova_etapa')
    etapa.nome = nova_etapa_nome
    etapa.save()
    return JsonResponse({'success': True, 'message': f'Etapa movida para {nova_etapa_nome}'})


@login_required
@require_POST
def atribuir_funcionario(request, etapa_id):
    """Atribui funcionário a uma etapa"""
    etapa = get_object_or_404(OrdemEtapa, id=etapa_id)
    funcionario_id = request.POST.get('funcionario_id')
    data_programada = request.POST.get('data_programada')
    
    data_programada_date = None
    if data_programada:
        try:
            from datetime import datetime
            data_programada_date = datetime.strptime(data_programada, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return JsonResponse({'ok': False, 'erro': 'Data programada inválida.'}, status=400)

    data_entrada = None
    try:
        data_entrada = getattr(etapa.ordem, 'data_chegada_veiculo', None)
        if not data_entrada and getattr(etapa.ordem, 'orcamento_id', None):
            data_entrada = getattr(etapa.ordem.orcamento, 'data_agendada', None)
    except Exception:
        data_entrada = None

    hoje = date.today()
    if data_entrada and data_entrada > hoje:
        if not data_programada_date or data_programada_date < data_entrada:
            return JsonResponse(
                {'ok': False, 'erro': f'Veículo com entrada prevista para {data_entrada.strftime("%d/%m/%Y")}. Programação deve ser a partir desta data.'},
                status=400
            )

    if funcionario_id:
        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        etapa.funcionario = funcionario
    
    if data_programada_date:
        etapa.data_programada = data_programada_date

    if etapa.funcionario_id and etapa.data_programada and etapa.status in ['aguardando', 'programado']:
        etapa.status = 'programado'
    
    etapa.save()
    data_alvo = date.today()
    data_alvo_str = data_programada or request.GET.get('data')
    if data_alvo_str:
        try:
            from datetime import datetime
            data_alvo = datetime.strptime(data_alvo_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            data_alvo = date.today()
    try:
        from django.utils import timezone
        if etapa.status == 'em_andamento' and etapa.data_inicio:
            etapa.segundos_em_andamento = int((timezone.now() - etapa.data_inicio).total_seconds())
        else:
            etapa.segundos_em_andamento = 0
    except Exception:
        etapa.segundos_em_andamento = 0
    return render(request, 'kanban/partials/etapa_card.html', {'etapa': etapa, 'data_alvo': data_alvo})


@login_required
@require_POST
def entregar_ordem(request, ordem_id):
    from django.utils import timezone

    ordem = get_object_or_404(OrdemServico, id=ordem_id)
    perfil = getattr(request.user, 'perfil', '')
    if not (request.user.is_superuser or perfil in ['admin', 'gerente', 'supervisor', 'financeiro', 'orcamentista']):
        return JsonResponse({'ok': False, 'erro': 'Acesso restrito.'}, status=403)

    if ordem.status != 'concluida':
        return JsonResponse({'ok': False, 'erro': 'Apenas OS concluída pode ser marcada como entregue.'}, status=400)

    ordem.status = 'entregue'
    ordem.data_entrega = timezone.now()
    ordem.save(update_fields=['status', 'data_entrega'])

    try:
        orcamento = ordem.orcamento
        if orcamento.status not in ['entregue', 'retrabalho']:
            orcamento.status = 'entregue'
            orcamento.save(update_fields=['status'])
    except Exception:
        pass

    return JsonResponse({'ok': True})


@login_required
def minhas_tarefas(request):
    """Kanban pessoal do colaborador — hoje + programadas futuras com sequência."""
    from apps.ordens.models import SessaoTrabalho
    from django.utils import timezone

    funcionario = request.user
    hoje = date.today()

    # Sessão ativa (se existir)
    sessao_ativa = SessaoTrabalho.objects.filter(
        funcionario=funcionario,
        fim__isnull=True
    ).select_related('etapa', 'etapa__ordem', 'etapa__ordem__orcamento', 'etapa__ordem__cliente', 'etapa__ordem__veiculo', 'etapa__ordem__veiculo__modelo_veiculo').first()

    if sessao_ativa and (
        sessao_ativa.etapa.status != 'em_andamento'
        or sessao_ativa.etapa.ordem.status in ['concluida', 'entregue', 'cancelada']
    ):
        sessao_ativa.fechar()
        sessao_ativa = None

    em_andamento = sessao_ativa.etapa if sessao_ativa else None

    segundos_trabalhando = 0
    if sessao_ativa:
        segundos_trabalhando = int(float(sessao_ativa.minutos_ate_agora()) * 60)

    tarefas_pendentes_status = ['aguardando', 'programado', 'aguardando_peca']

    tarefas_base = OrdemEtapa.objects.select_related(
        'ordem',
        'ordem__orcamento',
        'ordem__cliente',
        'ordem__veiculo',
        'ordem__veiculo__modelo_veiculo',
    ).filter(
        models.Q(funcionario=funcionario) | models.Q(auxiliares=funcionario)
    ).filter(
        status__in=tarefas_pendentes_status
    ).distinct()

    tarefas_hoje_qs = list(tarefas_base.filter(
        models.Q(data_programada__lte=hoje) | models.Q(data_programada__isnull=True)
    ).order_by('data_programada', 'sequencia', 'id'))

    tarefas_futuras_qs = list(tarefas_base.filter(
        data_programada__gt=hoje
    ).order_by('data_programada', 'sequencia', 'id'))

    # Próximas etapas da mesma OS (mesma exclusão de funcionário)
    if em_andamento:
        proximas_mesma_os = list(OrdemEtapa.objects.filter(
            ordem=em_andamento.ordem,
            status__in=tarefas_pendentes_status,
        ).filter(
            models.Q(funcionario=funcionario) | models.Q(funcionario__isnull=True) | models.Q(auxiliares=funcionario)
        ).filter(
            models.Q(data_programada__lte=hoje) | models.Q(data_programada__isnull=True)
        ).order_by('sequencia'))
        ids_hoje = {e.pk for e in tarefas_hoje_qs}
        for e in proximas_mesma_os:
            if e.pk not in ids_hoje:
                tarefas_hoje_qs.append(e)
                ids_hoje.add(e.pk)

    # Bloqueio de sequência: primeira tarefa do dia está livre para iniciar
    tarefas_hoje_com_status = []
    for idx, tarefa in enumerate(tarefas_hoje_qs):
        bloqueada = (idx > 0)  # 2ª em diante fica na fila
        atrasada = tarefa.data_programada is not None and tarefa.data_programada < hoje
        tarefas_hoje_com_status.append({
            'etapa': tarefa,
            'bloqueada': bloqueada,
            'atrasada': atrasada,
        })

    # Futuras agrupadas por data
    tarefas_futuras_agrupadas = {}
    for tarefa in tarefas_futuras_qs:
        key = tarefa.data_programada
        if key not in tarefas_futuras_agrupadas:
            tarefas_futuras_agrupadas[key] = []
        tarefas_futuras_agrupadas[key].append(tarefa)

    # Finalizadas hoje
    finalizadas_hoje = OrdemEtapa.objects.filter(
        status='finalizada',
        data_fim__date=hoje
    ).filter(
        models.Q(funcionario=funcionario) | models.Q(auxiliares=funcionario) | models.Q(sessoes__funcionario=funcionario)
    ).distinct().select_related('ordem', 'ordem__cliente', 'ordem__veiculo').order_by('-data_fim')

    context = {
        'em_andamento': em_andamento,
        'sessao_ativa': sessao_ativa,
        'segundos_trabalhando': segundos_trabalhando,
        'tarefas_hoje': tarefas_hoje_com_status,
        'tarefas_futuras_agrupadas': tarefas_futuras_agrupadas,
        'finalizadas_hoje': finalizadas_hoje,
        'hoje': hoje,
    }
    return render(request, 'kanban/minhas_tarefas.html', context)


@login_required
def agenda_producao(request):
    """Agenda de produção — visão de gestores com todas as etapas programadas por data."""
    from django.db.models import Count
    import json
    from django.urls import reverse
    from apps.orcamentos.models import Orcamento

    # Apenas admin, gerente, supervisor e superuser
    if not (request.user.is_superuser or getattr(request.user, 'perfil', '') in ['admin', 'gerente', 'supervisor']):
        from django.contrib import messages
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('kanban:producao')

    hoje = date.today()

    # Período: padrão 30 dias à frente; pode filtrar por data
    data_inicio_str = request.GET.get('de', str(hoje))
    data_fim_str = request.GET.get('ate', str(hoje + timedelta(days=30)))

    try:
        from datetime import datetime
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        data_inicio = hoje
        data_fim = hoje + timedelta(days=30)

    # Etapas com data programada no período
    etapas_programadas = OrdemEtapa.objects.filter(
        data_programada__gte=data_inicio,
        data_programada__lte=data_fim,
    ).select_related(
        'ordem', 'ordem__cliente', 'ordem__veiculo', 'ordem__orcamento',
        'funcionario'
    ).order_by('data_programada', 'funcionario__first_name', 'sequencia')

    # Etapas atrasadas (antes do período) — ainda não finalizadas
    etapas_atrasadas = OrdemEtapa.objects.filter(
        data_programada__lt=data_inicio,
    ).exclude(
        status='finalizada'
    ).select_related(
        'ordem', 'ordem__cliente', 'ordem__veiculo', 'ordem__orcamento',
        'funcionario'
    ).order_by('data_programada', 'funcionario__first_name', 'sequencia')

    # Etapas sem data (no pátio — sem programação)
    sem_data = OrdemEtapa.objects.filter(
        data_programada__isnull=True,
        funcionario__isnull=False,
        status__in=['aguardando', 'programado']
    ).select_related('ordem', 'ordem__cliente', 'ordem__veiculo', 'funcionario')

    # Agrupar por data
    agenda = {}
    for etapa in etapas_programadas:
        d = etapa.data_programada
        if d not in agenda:
            agenda[d] = []
        agenda[d].append(etapa)

    # Funcionários para filtro
    funcionarios = Funcionario.objects.filter(ativo=True).order_by('first_name')

    data_inicio_agenda = data_inicio if data_inicio > hoje else hoje
    orcamentos_agendados_qs = Orcamento.objects.filter(
        data_agendada__isnull=False,
        data_agendada__gte=data_inicio_agenda,
        data_agendada__lte=data_fim,
    ).select_related('cliente', 'veiculo').order_by('data_agendada', 'criado_em')

    agenda_entrada = {}
    for o in orcamentos_agendados_qs:
        d = o.data_agendada
        if d not in agenda_entrada:
            agenda_entrada[d] = []
        agenda_entrada[d].append(o)

    agenda_entrada_json = {
        str(d): [
            {
                'id': o.id,
                'numero': o.numero,
                'os_numero': (getattr(getattr(o, 'ordem_servico', None), 'numero', None) if hasattr(o, 'ordem_servico') else None),
                'cliente': o.cliente.nome,
                'placa': o.veiculo.placa,
                'marca': (o.veiculo.modelo_veiculo.fabricante.nome if getattr(o.veiculo, 'modelo_veiculo', None) and getattr(o.veiculo.modelo_veiculo, 'fabricante', None) else o.veiculo.marca),
                'modelo': (o.veiculo.modelo_veiculo.nome if getattr(o.veiculo, 'modelo_veiculo', None) else o.veiculo.modelo),
                'ano': (o.veiculo.ano_modelo or o.veiculo.ano_fabricacao),
                'cor': getattr(o.veiculo, 'cor_display', None),
                'km': getattr(o.veiculo, 'km_atual', None),
                'renavam': getattr(o.veiculo, 'renavam', None),
                'chassi': getattr(o.veiculo, 'chassi', None),
                'status': o.get_status_display(),
                'status_codigo': o.status,
                'perda_total': bool(o.perda_total),
                'detail_url': reverse('orcamentos:detail', args=[o.pk]),
            }
            for o in agenda_entrada[d]
        ]
        for d in agenda_entrada
    }

    context = {
        'agenda': agenda,  # dict: {date: [etapas]}
        'etapas_atrasadas': etapas_atrasadas,
        'agenda_entrada': agenda_entrada,
        'agenda_entrada_json': json.dumps(agenda_entrada_json, ensure_ascii=False),
        'sem_data': sem_data,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'hoje': hoje,
        'funcionarios': funcionarios,
    }
    return render(request, 'kanban/agenda.html', context)


@login_required
@require_POST
def reprogramar_etapa(request, etapa_id):
    from django.contrib import messages
    from django.urls import reverse

    perfil = getattr(request.user, 'perfil', '')
    if not (request.user.is_superuser or perfil in ['admin', 'gerente', 'supervisor']):
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('kanban:producao')

    etapa = get_object_or_404(OrdemEtapa, id=etapa_id)
    data_programada = request.POST.get('data_programada')

    if not data_programada:
        messages.error(request, 'Informe a data para reprogramar.')
        return redirect(request.POST.get('next') or reverse('kanban:agenda'))

    try:
        from datetime import datetime
        data_programada_date = datetime.strptime(data_programada, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        messages.error(request, 'Data programada inválida.')
        return redirect(request.POST.get('next') or reverse('kanban:agenda'))

    data_entrada = None
    try:
        data_entrada = getattr(etapa.ordem, 'data_chegada_veiculo', None)
        if not data_entrada and getattr(etapa.ordem, 'orcamento_id', None):
            data_entrada = getattr(etapa.ordem.orcamento, 'data_agendada', None)
    except Exception:
        data_entrada = None

    hoje = date.today()
    if data_entrada and data_entrada > hoje and data_programada_date < data_entrada:
        messages.error(
            request,
            f'Veículo com entrada prevista para {data_entrada.strftime("%d/%m/%Y")}. Programação deve ser a partir desta data.'
        )
        return redirect(request.POST.get('next') or reverse('kanban:agenda'))

    etapa.data_programada = data_programada_date
    if etapa.funcionario_id and etapa.status in ['aguardando', 'programado']:
        etapa.status = 'programado'
    etapa.save(update_fields=['data_programada', 'status', 'atualizado_em'])

    messages.success(request, f'Etapa reprogramada para {data_programada_date.strftime("%d/%m/%Y")}.')
    return redirect(request.POST.get('next') or reverse('kanban:agenda'))


@login_required
def agenda_mao_obra(request):
    from decimal import Decimal

    if not (request.user.is_superuser or getattr(request.user, 'perfil', '') in ['admin', 'gerente', 'supervisor']):
        from django.contrib import messages
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('kanban:producao')

    hoje = date.today()
    data_inicio_str = request.GET.get('de', str(hoje))
    data_fim_str = request.GET.get('ate', str(hoje + timedelta(days=30)))
    capacidade_str = request.GET.get('cap', '44')

    try:
        from datetime import datetime
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        data_inicio = hoje
        data_fim = hoje + timedelta(days=30)

    try:
        capacidade_semanal = Decimal(str(capacidade_str))
    except Exception:
        capacidade_semanal = Decimal('44')
    if capacidade_semanal < 0:
        capacidade_semanal = Decimal('44')

    funcionarios = list(Funcionario.objects.filter(ativo=True, perfil='operacional').order_by('first_name'))
    semanas = []
    inicio_semana = data_inicio - timedelta(days=data_inicio.weekday())
    fim_semana = data_fim - timedelta(days=data_fim.weekday())
    cursor = inicio_semana
    while cursor <= fim_semana:
        semana_inicio = cursor
        semana_fim = min(cursor + timedelta(days=6), data_fim)
        semanas.append((semana_inicio, semana_fim))
        cursor = cursor + timedelta(days=7)

    etapas = list(
        OrdemEtapa.objects.filter(
            data_programada__gte=data_inicio,
            data_programada__lte=data_fim,
        )
        .exclude(status='finalizada')
        .filter(models.Q(funcionario__perfil='operacional') | models.Q(funcionario__isnull=True))
        .values('data_programada', 'funcionario_id', 'horas_orcadas')
    )

    horas_por_semana_func = {str(ini): {} for ini, _ in semanas}
    for e in etapas:
        d = e.get('data_programada')
        semana_inicio = d - timedelta(days=d.weekday())
        key = str(semana_inicio)
        if key not in horas_por_semana_func:
            continue
        func_id = e.get('funcionario_id')
        horas = e.get('horas_orcadas') or Decimal('0')
        bucket = func_id if func_id is not None else 0
        horas_por_semana_func[key][bucket] = (horas_por_semana_func[key].get(bucket, Decimal('0')) + horas)

    resumo_semanal = []
    for ini, fim in semanas:
        key = str(ini)
        linhas = []
        total_atribuido = Decimal('0')
        for f in funcionarios:
            horas_f = horas_por_semana_func.get(key, {}).get(f.id, Decimal('0'))
            total_atribuido += horas_f
            saldo = capacidade_semanal - horas_f
            linhas.append({
                'id': f.id,
                'nome': f.get_full_name() or f.username,
                'horas': float(horas_f),
                'capacidade': float(capacidade_semanal),
                'saldo': float(saldo),
            })
        horas_sem_responsavel = horas_por_semana_func.get(key, {}).get(0, Decimal('0'))
        linhas.append({
            'id': 0,
            'nome': 'Sem responsável',
            'horas': float(horas_sem_responsavel),
            'capacidade': None,
            'saldo': None,
        })
        linhas.sort(key=lambda x: (-x['horas'], x['nome']))
        total_programado = (total_atribuido + horas_sem_responsavel)
        total_capacidade = capacidade_semanal * Decimal(len(funcionarios))
        resumo_semanal.append({
            'inicio': ini,
            'fim': fim,
            'funcionarios': linhas,
            'total_programado': float(total_programado),
            'total_atribuido': float(total_atribuido),
            'total_capacidade': float(total_capacidade),
            'saldo_total': float(total_capacidade - total_programado),
            'sem_responsavel': float(horas_sem_responsavel),
        })

    context = {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'capacidade_semanal': float(capacidade_semanal),
        'resumo_semanal': resumo_semanal,
    }
    return render(request, 'kanban/agenda_mao_obra.html', context)


@login_required
def debug_etapas(request):
    """DEBUG temporário — remover depois"""
    from django.http import JsonResponse
    from apps.ordens.models import SessaoTrabalho
    from django.utils import timezone

    funcionario = request.user
    hoje = date.today()

    sessao_ativa = SessaoTrabalho.objects.filter(
        funcionario=funcionario, fim__isnull=True
    ).select_related('etapa', 'etapa__ordem').first()
    em_andamento = sessao_ativa.etapa if sessao_ativa else None

    etapas_do_usuario = list(OrdemEtapa.objects.filter(
        funcionario=funcionario,
        status__in=['aguardando', 'programado']
    ).values('id', 'nome', 'funcionario_id', 'status', 'ordem_id', 'data_programada'))

    etapas_mesma_os = []
    if em_andamento:
        proximas = list(OrdemEtapa.objects.filter(
            ordem=em_andamento.ordem,
            status__in=['aguardando', 'programado'],
        ).filter(
            models.Q(funcionario=funcionario) | models.Q(funcionario__isnull=True)
        ).values('id', 'nome', 'funcionario_id', 'status', 'data_programada'))
        ids_usuario = {e['id'] for e in etapas_do_usuario}
        etapas_mesma_os = [e for e in proximas if e['id'] not in ids_usuario]

    todas = etapas_mesma_os + [e for e in etapas_do_usuario if e['id'] not in {x['id'] for x in etapas_mesma_os}]

    tarefas_hoje = [e for e in todas if e['data_programada'] is None or str(e['data_programada']) <= str(hoje)]
    tarefas_futuras = [e for e in todas if e['data_programada'] and str(e['data_programada']) > str(hoje)]

    return JsonResponse({
        'user_pk': funcionario.pk,
        'hoje': str(hoje),
        'em_andamento_id': em_andamento.pk if em_andamento else None,
        'etapas_do_usuario': etapas_do_usuario,
        'etapas_mesma_os': etapas_mesma_os,
        'todas_pendentes': todas,
        'tarefas_hoje': tarefas_hoje,
        'tarefas_futuras': tarefas_futuras,
    }, json_dumps_params={'indent': 2, 'default': str})


@login_required
@require_POST
def sessao_iniciar(request, etapa_id):
    """Inicia uma sessão de trabalho."""
    from apps.ordens.services import SessaoService
    etapa = get_object_or_404(OrdemEtapa, id=etapa_id)
    try:
        SessaoService.iniciar_sessao(etapa, request.user)
        return JsonResponse({'ok': True})
    except ValueError as e:
        return JsonResponse({'ok': False, 'erro': str(e)}, status=400)


@login_required
@require_POST
def sessao_pausar(request, etapa_id):
    """Pausa a sessão ativa, acumula horas."""
    from apps.ordens.services import SessaoService
    etapa = get_object_or_404(OrdemEtapa, id=etapa_id)
    try:
        SessaoService.pausar_sessao(etapa, request.user)
        return JsonResponse({'ok': True})
    except ValueError as e:
        return JsonResponse({'ok': False, 'erro': str(e)}, status=400)


@login_required
@require_POST
def sessao_finalizar(request, etapa_id):
    """Finaliza a etapa definitivamente."""
    from apps.ordens.services import SessaoService
    etapa = get_object_or_404(OrdemEtapa, id=etapa_id)
    try:
        SessaoService.finalizar_sessao(etapa, request.user)
        return JsonResponse({'ok': True})
    except ValueError as e:
        return JsonResponse({'ok': False, 'erro': str(e)}, status=400)


@login_required
@require_POST
def etapa_toggle_extra(request, etapa_id):
    etapa = get_object_or_404(OrdemEtapa, id=etapa_id)
    perfil = getattr(request.user, 'perfil', '')
    if not (request.user.is_superuser or perfil in ['admin', 'gerente', 'supervisor']):
        return JsonResponse({'ok': False, 'erro': 'Acesso restrito.'}, status=403)

    etapa.permitir_horas_extras = not bool(getattr(etapa, 'permitir_horas_extras', False))
    etapa.save(update_fields=['permitir_horas_extras'])
    return JsonResponse({'ok': True, 'permitir_horas_extras': etapa.permitir_horas_extras})


@login_required
@require_POST
def iniciar_tarefa(request, etapa_id):
    """[LEGADO] mantido por compatibilidade"""
    from apps.ordens.services import OrdemEtapaService
    etapa = get_object_or_404(OrdemEtapa, id=etapa_id)
    try:
        OrdemEtapaService.iniciar_etapa(etapa, request.user)
        try:
            from django.utils import timezone
            if etapa.status == 'em_andamento' and etapa.data_inicio:
                etapa.segundos_em_andamento = int((timezone.now() - etapa.data_inicio).total_seconds())
            else:
                etapa.segundos_em_andamento = 0
        except Exception:
            etapa.segundos_em_andamento = 0
        return render(request, 'kanban/partials/etapa_card.html', {'etapa': etapa})
    except ValueError as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_POST
def concluir_tarefa(request, etapa_id):
    """[LEGADO] mantido por compatibilidade"""
    from apps.ordens.services import OrdemEtapaService
    etapa = get_object_or_404(OrdemEtapa, id=etapa_id)
    tem_peca_pendente = request.POST.get('tem_peca_pendente') == 'true'
    try:
        resultado = OrdemEtapaService.concluir_etapa(etapa, tem_peca_pendente)
        comissoes = resultado.get('comissao') or []
        total_comissao = sum(c.valor for c in comissoes) if comissoes else 0
        return JsonResponse({
            'success': True,
            'comissao_gerada': str(total_comissao),
            'proxima_etapa': resultado.get('proxima_etapa').nome if resultado.get('proxima_etapa') else None
        })
    except ValueError as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

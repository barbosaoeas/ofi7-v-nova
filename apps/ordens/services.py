"""
Services para Ordens de Serviço
Centraliza TODAS as regras de negócio relacionadas a ordens
"""
from django.db import transaction
from django.utils import timezone
from apps.orcamentos.models import Orcamento
from apps.comissoes.services import ComissaoService
from .models import OrdemServico, OrdemEtapa, SessaoTrabalho


class OrdemServicoService:
    """
    Service para gerenciar Ordens de Serviço
    """
    
    @staticmethod
    @transaction.atomic
    def criar_de_orcamento(orcamento_id, criado_por):
        """
        Cria uma Ordem de Serviço a partir de um orçamento aprovado
        
        Args:
            orcamento_id: ID do orçamento
            criado_por: Funcionário que está criando a OS
            
        Returns:
            OrdemServico: Ordem criada com todas as etapas
        """
        # Busca orçamento
        orcamento = Orcamento.objects.get(id=orcamento_id)
        
        # Validações
        if orcamento.status not in ['aprovado', 'retrabalho']:
            raise ValueError("Orçamento precisa estar aprovado ou em retrabalho para gerar OS")
        
        # Verifica se já existe OS
        try:
            ordem = orcamento.ordem_servico
            # Se já existe OS mas sem etapas, recria as etapas
            if ordem.etapas.exists():
                raise ValueError("Já existe uma OS com etapas para este orçamento")
            # OS existe mas vazia — adiciona as etapas agora
        except OrdemServico.DoesNotExist:
            # Cria OS nova
            ordem = OrdemServico.objects.create(
                orcamento=orcamento,
                cliente=orcamento.cliente,
                veiculo=orcamento.veiculo,
                criado_por=criado_por,
                status='aberta',
                data_chegada_veiculo=orcamento.data_agendada,
                data_previsao_entrega=orcamento.data_prevista_entrega
            )
        except AttributeError:
            # Sem OS — cria nova
            ordem = OrdemServico.objects.create(
                orcamento=orcamento,
                cliente=orcamento.cliente,
                veiculo=orcamento.veiculo,
                criado_por=criado_por,
                status='aberta',
                data_chegada_veiculo=orcamento.data_agendada,
                data_previsao_entrega=orcamento.data_prevista_entrega
            )
        
        # Cria etapas a partir dos itens do orçamento
        for idx, item in enumerate(orcamento.itens.all(), start=1):
            nome_etapa = item.etapa.nome if item.etapa else "Serviço Adicional"
            
            # Determina sequência baseada no nome da etapa
            sequencia = OrdemEtapaService.obter_sequencia_por_nome(nome_etapa)
            
            OrdemEtapa.objects.create(
                ordem=ordem,
                nome=nome_etapa,
                descricao=item.descricao,
                sequencia=sequencia,
                valor_servico=(item.valor if not getattr(item, 'retrabalho', False) else 0),
                horas_orcadas=item.horas_previstas,
                execucao=getattr(item, 'execucao', 'oficina') or 'oficina',
                status='aguardando'
            )
        
        return ordem

    @staticmethod
    @transaction.atomic
    def liberar_veiculo_patio(ordem):
        """
        Libera veículo do pátio após orçamento aprovado
        - Marca etapa Pátio como concluída
        - Muda próximas etapas para 'aguardando_programacao'
        """
        # Busca etapa do pátio
        etapa_patio = ordem.etapas.filter(nome='Pátio').first()

        if etapa_patio and etapa_patio.status == 'patio':
            # Conclui pátio
            etapa_patio.status = 'liberado'
            etapa_patio.data_fim = timezone.now()
            etapa_patio.save()

            # Libera próximas etapas para programação
            ordem.etapas.filter(status='aguardando_liberacao').update(
                status='aguardando_programacao'
            )

            # Atualiza status da ordem
            ordem.status = 'aguardando_programacao'
            ordem.save()

        return ordem

    @staticmethod
    def atualizar_status_ordem(ordem):
        """
        Atualiza o status da ordem baseado nas etapas
        """
        etapas = ordem.etapas.all()
        
        if ordem.data_entrega:
            ordem.status = 'entregue'
        # Verifica se tem peça pendente
        elif etapas.filter(status='aguardando_peca').exists():
            ordem.status = 'aguardando_peca'
        # Verifica se todas estão concluídas
        elif etapas.filter(status='finalizada').count() == etapas.count():
            ordem.status = 'concluida'
            if not ordem.data_conclusao:
                ordem.data_conclusao = timezone.now()
        # Verifica se alguma está em andamento
        elif etapas.filter(status='em_andamento').exists():
            ordem.status = 'em_andamento'
        else:
            ordem.status = 'aberta'
        
        ordem.save()


class OrdemEtapaService:
    """
    Service para gerenciar Etapas das Ordens
    """
    
    # Mapeamento de nomes para sequências
    SEQUENCIAS = {
        'Pátio': 1,
        'Desmontagem': 2,
        'Funilaria': 3,
        'Preparação Pintura': 4,
        'Pintura': 5,
        'Montagem': 6,
        'Polimento': 7,
        'Mecânica': 8,
        'Mecanica': 8,
        'Preparação Entrega': 9,
        'Finalizado': 10,
    }
    
    @staticmethod
    def obter_sequencia_por_nome(nome):
        """Retorna a sequência padrão para um nome de etapa"""
        if not nome:
            return 99
        direto = OrdemEtapaService.SEQUENCIAS.get(nome)
        if direto is not None:
            return direto
        n = str(nome).strip().lower()
        if 'patio' in n or 'pátio' in n:
            return 1
        if 'desmont' in n:
            return 2
        if 'funilar' in n:
            return 3
        if 'prepara' in n and 'pint' in n:
            return 4
        if 'prepara' in n and 'entreg' not in n:
            return 4
        if 'pintur' in n:
            return 5
        if 'montag' in n:
            return 6
        if 'polim' in n:
            return 7
        if 'mec' in n:
            return 8
        if 'prepara' in n and 'entreg' in n:
            return 9
        if 'final' in n:
            return 10
        return 99
    
    @staticmethod
    @transaction.atomic
    def programar_etapa(etapa, funcionario, data_programada):
        """
        Programa uma etapa para um funcionário
        - Muda status de 'aguardando' para 'programado'
        """
        if etapa.status not in ['aguardando', 'programado']:
            raise ValueError(f"Etapa não está em estado inicial. Status atual: {etapa.get_status_display()}")

        data_entrada = None
        try:
            data_entrada = getattr(etapa.ordem, 'data_chegada_veiculo', None)
            if not data_entrada and getattr(etapa.ordem, 'orcamento_id', None):
                data_entrada = getattr(etapa.ordem.orcamento, 'data_agendada', None)
        except Exception:
            data_entrada = None

        if data_entrada:
            if data_programada is None:
                raise ValueError(f"Veículo com entrada prevista para {data_entrada.strftime('%d/%m/%Y')}. Informe uma data de programação.")
            if data_programada < data_entrada:
                raise ValueError(f"Veículo com entrada prevista para {data_entrada.strftime('%d/%m/%Y')}. Programação deve ser a partir desta data.")

        etapa.funcionario = funcionario
        etapa.data_programada = data_programada
        etapa.status = 'programado'
        etapa.save()

        return etapa

    @staticmethod
    def validar_pode_iniciar(etapa, funcionario):
        """
        Valida se um funcionário pode iniciar uma etapa

        Returns:
            tuple: (pode_iniciar: bool, mensagem_erro: str)
        """
        # Verifica se está programada
        if etapa.status != 'programado':
            return False, f"Etapa não está programada. Status: {etapa.get_status_display()}"

        # Verifica se é o funcionário programado
        if etapa.funcionario != funcionario:
            return False, "Etapa programada para outro funcionário"

        # Verifica se funcionário tem outra tarefa em andamento
        tarefas_em_andamento = OrdemEtapa.objects.filter(
            funcionario=funcionario,
            status='em_andamento'
        ).exclude(id=etapa.id)

        if tarefas_em_andamento.exists():
            tarefa = tarefas_em_andamento.first()
            return False, f"Você já tem tarefa em serviço: {tarefa.ordem.numero} - {tarefa.nome}"

        try:
            data_entrada = None
            data_entrada = getattr(etapa.ordem, 'data_chegada_veiculo', None)
            if not data_entrada and getattr(etapa.ordem, 'orcamento_id', None):
                data_entrada = getattr(etapa.ordem.orcamento, 'data_agendada', None)
            if data_entrada and timezone.localdate() < data_entrada:
                return False, f"Veículo ainda não deu entrada na oficina (previsto para {data_entrada.strftime('%d/%m/%Y')})."
        except Exception:
            pass

        pendente_anterior = OrdemEtapa.objects.filter(
            ordem=etapa.ordem,
            sequencia__lt=etapa.sequencia,
        ).exclude(
            status='finalizada'
        ).order_by('sequencia').first()

        if pendente_anterior:
            return False, f'Conclua primeiro a etapa anterior: "{pendente_anterior.nome}" (OS {etapa.ordem.numero}).'

        return True, ""
    
    @staticmethod
    @transaction.atomic
    def iniciar_etapa(etapa_id, funcionario):
        """
        Inicia uma etapa
        
        Args:
            etapa_id: ID da etapa
            funcionario: Funcionário que está iniciando
            
        Returns:
            OrdemEtapa: Etapa atualizada
        """
        etapa = OrdemEtapa.objects.select_for_update().get(id=etapa_id)
        
        # Valida
        pode, mensagem = OrdemEtapaService.validar_pode_iniciar(etapa, funcionario)
        if not pode:
            raise ValueError(mensagem)
        
        # Atribui funcionário se não tiver
        if not etapa.funcionario:
            etapa.funcionario = funcionario
        
        # Atualiza status para EM ANDAMENTO
        etapa.status = 'em_andamento'
        etapa.data_inicio = timezone.now()
        etapa.save()
        
        # Atualiza status da ordem
        OrdemServicoService.atualizar_status_ordem(etapa.ordem)

        return etapa

    @staticmethod
    @transaction.atomic
    def concluir_etapa(etapa_id, tem_peca_pendente=False, observacao_peca=''):
        """
        Conclui uma etapa

        Args:
            etapa_id: ID da etapa
            tem_peca_pendente: Se True, marca como aguardando peça
            observacao_peca: Observação sobre a peça (se aplicável)

        Returns:
            dict: {
                'etapa': OrdemEtapa,
                'comissao': Comissao (se gerada),
                'proxima_etapa': OrdemEtapa (se houver),
                'peca_criada': Peca (se criada)
            }
        """
        from apps.pecas.services import PecaService

        etapa = OrdemEtapa.objects.select_for_update().get(id=etapa_id)

        # Valida
        if etapa.status != 'em_andamento':
            raise ValueError("Apenas etapas em andamento podem ser concluídas")

        resultado = {
            'etapa': etapa,
            'comissao': None,
            'proxima_etapa': None,
            'peca_criada': None
        }

        # Se tem peça pendente
        if tem_peca_pendente:
            etapa.status = 'aguardando_peca'
            etapa.save()

            # Cria registro de peça
            peca = PecaService.criar_peca_bloqueante(
                etapa=etapa,
                observacao=observacao_peca,
                solicitado_por=etapa.funcionario or etapa.ordem.criado_por
            )
            resultado['peca_criada'] = peca

        else:
            # Conclui a etapa
            etapa.status = 'finalizada'
            etapa.data_fim = timezone.now()
            etapa.save()

            # Gera comissão
            comissoes = ComissaoService.gerar_comissao_etapa(etapa)
            resultado['comissao'] = comissoes

            # Anula lógica rígida de bloqueio para manter flexibilidade do novo painel
            # proxima = OrdemEtapaService.obter_proxima_etapa(etapa)
            # if proxima: pass

        # Atualiza status da ordem
        OrdemServicoService.atualizar_status_ordem(etapa.ordem)

        return resultado

    @staticmethod
    def obter_proxima_etapa(etapa):
        """
        Obtém a próxima etapa na sequência
        """
        return OrdemEtapa.objects.filter(
            ordem=etapa.ordem,
            sequencia__gt=etapa.sequencia
        ).order_by('sequencia').first()

    @staticmethod
    def obter_etapas_funcionario(funcionario, apenas_hoje=False):
        """
        Obtém as etapas de um funcionário

        Returns:
            dict: {
                'programadas_hoje': QuerySet,
                'em_andamento': OrdemEtapa ou None,
                'aguardando_peca': QuerySet
            }
        """
        from datetime import date

        etapas = OrdemEtapa.objects.filter(funcionario=funcionario)

        # Em andamento (só pode ter 1)
        em_andamento = etapas.filter(status='em_andamento').first()

        # Programadas
        programadas = etapas.filter(status='pendente')
        if apenas_hoje:
            programadas = programadas.filter(data_programada=date.today())

        # Aguardando peça
        aguardando_peca = etapas.filter(status='aguardando_peca')

        return {
            'programadas_hoje': programadas.order_by('data_programada'),
            'em_andamento': em_andamento,
            'aguardando_peca': aguardando_peca.order_by('-atualizado_em')
        }


class SessaoService:
    """
    Controla o apontamento de horas por sessão de trabalho.
    Regra: bloqueia apenas se há sessão ABERTA (fim=None).
    Pausado = sessão fechada = pode iniciar outra tarefa livremente.
    """

    @staticmethod
    def iniciar_sessao(etapa, funcionario):
        with transaction.atomic():
            etapa = OrdemEtapa.objects.select_for_update().select_related('ordem').get(pk=etapa.pk)

            sessao_ativa = SessaoTrabalho.objects.filter(
                funcionario=funcionario,
                fim__isnull=True
            ).select_related('etapa', 'etapa__ordem').first()

            if sessao_ativa:
                if (
                    sessao_ativa.etapa.status != 'em_andamento'
                    or sessao_ativa.etapa.ordem.status in ['concluida', 'entregue', 'cancelada']
                ):
                    sessao_ativa.fechar()
                else:
                    raise ValueError(
                        f'Você já está trabalhando em "{sessao_ativa.etapa.nome}" '
                        f'(OS {sessao_ativa.etapa.ordem.numero}). Pause antes de iniciar outra tarefa.'
                    )

            if etapa.status not in ['aguardando', 'programado']:
                raise ValueError(f'Esta etapa não pode ser iniciada. Status atual: {etapa.get_status_display()}')

            if etapa.funcionario_id and etapa.funcionario_id != funcionario.id:
                raise ValueError(
                    f'Etapa programada para "{etapa.funcionario.nome_completo}". '
                    f'Você está logado como "{funcionario.nome_completo}".'
                )

            try:
                data_entrada = None
                data_entrada = getattr(etapa.ordem, 'data_chegada_veiculo', None)
                if not data_entrada and getattr(etapa.ordem, 'orcamento_id', None):
                    data_entrada = getattr(etapa.ordem.orcamento, 'data_agendada', None)
                if data_entrada and timezone.localdate() < data_entrada:
                    raise ValueError(f'Veículo ainda não deu entrada na oficina (previsto para {data_entrada.strftime("%d/%m/%Y")}).')
            except ValueError:
                raise
            except Exception:
                pass

            pendente_anterior = OrdemEtapa.objects.filter(
                ordem=etapa.ordem,
                sequencia__lt=etapa.sequencia,
            ).exclude(
                status='finalizada'
            ).order_by('sequencia').first()

            if pendente_anterior:
                raise ValueError(f'Conclua primeiro a etapa anterior: "{pendente_anterior.nome}" (OS {etapa.ordem.numero}).')

            sessao = SessaoTrabalho.objects.create(etapa=etapa, funcionario=funcionario)

            update_fields = ['status', 'data_inicio']
            if not etapa.funcionario_id:
                etapa.funcionario = funcionario
                update_fields.insert(0, 'funcionario')
            etapa.status = 'em_andamento'
            etapa.data_inicio = timezone.now()
            etapa.save(update_fields=update_fields)

            return sessao

    @staticmethod
    def pausar_sessao(etapa, funcionario, close_at=None, reprogramar_para=None):
        from decimal import Decimal

        with transaction.atomic():
            sessao = SessaoTrabalho.objects.select_related('etapa', 'funcionario', 'etapa__ordem').filter(
                etapa=etapa,
                fim__isnull=True
            ).first()

            if not sessao:
                raise ValueError('Nenhuma sessão ativa encontrada para pausar.')

            perfil = getattr(funcionario, 'perfil', '')
            pode_intervir = funcionario.is_superuser or perfil in ['admin', 'gerente', 'supervisor']
            if sessao.funcionario_id != funcionario.id and not pode_intervir:
                raise ValueError('Sessão ativa pertence a outro colaborador.')

            duracao = sessao.fechar(close_at=close_at)
            horas_adicionadas = Decimal(str(round(float(duracao) / 60, 4)))
            etapa_db = OrdemEtapa.objects.select_for_update().get(pk=etapa.pk)
            etapa_db.horas_gastas_real = (etapa_db.horas_gastas_real or Decimal('0')) + horas_adicionadas
            etapa_db.status = 'programado'
            update_fields = ['horas_gastas_real', 'status']
            if reprogramar_para:
                etapa_db.data_programada = reprogramar_para
                update_fields.append('data_programada')
            etapa_db.save(update_fields=update_fields)
            try:
                OrdemServicoService.atualizar_status_ordem(etapa_db.ordem)
            except Exception:
                pass

            return sessao

    @staticmethod
    def finalizar_sessao(etapa, funcionario, close_at=None):
        from decimal import Decimal

        with transaction.atomic():
            sessao = SessaoTrabalho.objects.select_related('etapa', 'funcionario', 'etapa__ordem').filter(
                etapa=etapa,
                fim__isnull=True
            ).first()

            perfil = getattr(funcionario, 'perfil', '')
            pode_intervir = funcionario.is_superuser or perfil in ['admin', 'gerente', 'supervisor']
            if sessao and sessao.funcionario_id != funcionario.id and not pode_intervir:
                raise ValueError('Sessão ativa pertence a outro colaborador.')

            etapa_db = OrdemEtapa.objects.select_for_update().select_related('ordem').get(pk=etapa.pk)

            if sessao:
                duracao = sessao.fechar(close_at=close_at)
                horas_adicionadas = Decimal(str(round(float(duracao) / 60, 4)))
                etapa_db.horas_gastas_real = (etapa_db.horas_gastas_real or Decimal('0')) + horas_adicionadas

            etapa_db.status = 'finalizada'
            etapa_db.data_fim = timezone.now()
            etapa_db.save(update_fields=['horas_gastas_real', 'status', 'data_fim'])

            ComissaoService.gerar_comissao_etapa(etapa_db)
            OrdemServicoService.atualizar_status_ordem(etapa_db.ordem)

            return etapa_db

    @staticmethod
    def _proximo_dia_util(d):
        from datetime import timedelta
        dia = d + timedelta(days=1)
        while dia.weekday() >= 5:
            dia = dia + timedelta(days=1)
        return dia

    @staticmethod
    def _fim_expediente_aware(d):
        from datetime import datetime, time
        from django.utils import timezone
        tz = timezone.get_current_timezone()
        return timezone.make_aware(datetime.combine(d, time(17, 48)), tz)

    @staticmethod
    def auto_pausar_sessoes_sem_extra():
        from django.utils import timezone

        agora = timezone.now()
        sessoes = SessaoTrabalho.objects.select_related('etapa', 'etapa__ordem', 'funcionario').filter(
            fim__isnull=True,
            etapa__permitir_horas_extras=False,
        )

        total = 0
        for s in sessoes:
            try:
                inicio_local = timezone.localtime(s.inicio).date()
                fim_expediente = SessaoService._fim_expediente_aware(inicio_local)
                if agora < fim_expediente:
                    continue
                prox = SessaoService._proximo_dia_util(inicio_local)
                SessaoService.pausar_sessao(s.etapa, s.funcionario, close_at=fim_expediente, reprogramar_para=prox)
                total += 1
            except Exception:
                continue

        return total

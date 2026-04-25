"""
Services para Comissões
Centraliza regras de negócio de comissões
"""
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone
from .models import Comissao
from apps.ordens.models import SessaoTrabalho


class ComissaoService:
    """
    Service para gerenciar Comissões
    """
    
    @staticmethod
    @transaction.atomic
    def gerar_comissao_etapa(etapa):
        """
        Gera comissão automaticamente ao concluir uma etapa
        
        Args:
            etapa: OrdemEtapa que foi concluída
            
        Returns:
            list[Comissao]: Comissões criadas/atualizadas
        """
        if getattr(etapa, 'execucao', 'oficina') != 'oficina':
            return []

        # Validações
        if etapa.status != 'finalizada':
            raise ValueError("Apenas etapas finalizadas geram comissão")
        
        participantes_ids = set(
            SessaoTrabalho.objects.filter(etapa=etapa).values_list('funcionario_id', flat=True).distinct()
        )
        if etapa.funcionario_id:
            participantes_ids.add(etapa.funcionario_id)

        participantes_ids.update(etapa.auxiliares.values_list('id', flat=True))

        participantes_ids.discard(None)
        if not participantes_ids:
            raise ValueError("Etapa precisa ter ao menos um colaborador para gerar comissão")
        
        # Calcula tempo de execução
        tempo_execucao = etapa.horas_gastas_real
        if tempo_execucao is None and etapa.data_inicio and etapa.data_fim:
            delta = etapa.data_fim - etapa.data_inicio
            tempo_execucao = Decimal(str(round(delta.total_seconds() / 3600, 4)))
        
        # Obtém percentual a ser usado (hierarquia)
        percentual = etapa.percentual_comissao_efetivo
        
        # Calcula valor
        valor_total = Comissao.calcular_valor(etapa.valor_servico, percentual)

        participantes_ids_ordenados = sorted(participantes_ids)
        n = len(participantes_ids_ordenados)
        if n <= 0:
            raise ValueError("Nenhum participante válido para gerar comissão")

        valor_total_q = (Decimal(valor_total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        valor_base = (valor_total_q / Decimal(n)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        valores = [valor_base for _ in range(n)]
        soma = sum(valores)
        diferenca = (valor_total_q - soma).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if diferenca != Decimal('0.00'):
            passo = Decimal('0.01') if diferenca > 0 else Decimal('-0.01')
            for i in range(int((abs(diferenca) / Decimal('0.01')).to_integral_value())):
                valores[i % n] = (valores[i % n] + passo).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        data_execucao = (etapa.data_fim.date() if etapa.data_fim else timezone.localdate())

        comissoes = []
        for idx, funcionario_id in enumerate(participantes_ids_ordenados):
            comissao, created = Comissao.objects.get_or_create(
                etapa=etapa,
                funcionario_id=funcionario_id,
                defaults={
                    'ordem': etapa.ordem,
                    'valor_servico': etapa.valor_servico,
                    'percentual': percentual,
                    'valor': valores[idx],
                    'tempo_execucao_horas': tempo_execucao,
                    'status_pagamento': 'pendente',
                    'data_execucao': data_execucao,
                }
            )
            if not created:
                campos = {
                    'ordem': etapa.ordem,
                    'valor_servico': etapa.valor_servico,
                    'percentual': percentual,
                    'valor': valores[idx],
                    'tempo_execucao_horas': tempo_execucao,
                    'data_execucao': data_execucao,
                }
                for k, v in campos.items():
                    setattr(comissao, k, v)
                comissao.save(update_fields=list(campos.keys()) + ['atualizado_em'])
            comissoes.append(comissao)

        return comissoes
    
    @staticmethod
    @transaction.atomic
    def aprovar_comissao(comissao_id, aprovado_por):
        """
        Aprova uma comissão
        
        Args:
            comissao_id: ID da comissão
            aprovado_por: Funcionário que está aprovando (precisa ter permissão)
            
        Returns:
            Comissao: Comissão aprovada
        """
        comissao = Comissao.objects.get(id=comissao_id)
        
        # Validações
        if comissao.status_pagamento != 'pendente':
            raise ValueError("Apenas comissões pendentes podem ser aprovadas")
        
        if not aprovado_por.pode_aprovar_comissoes:
            raise ValueError("Usuário não tem permissão para aprovar comissões")
        
        # Aprova
        comissao.status_pagamento = 'aprovada'
        comissao.aprovado_por = aprovado_por
        comissao.data_aprovacao = timezone.now()
        comissao.save()
        
        return comissao
    
    @staticmethod
    @transaction.atomic
    def marcar_como_paga(comissao_id):
        """
        Marca uma comissão como paga
        
        Args:
            comissao_id: ID da comissão
            
        Returns:
            Comissao: Comissão atualizada
        """
        comissao = Comissao.objects.get(id=comissao_id)
        
        # Validação
        if comissao.status_pagamento != 'aprovada':
            raise ValueError("Apenas comissões aprovadas podem ser pagas")
        
        # Marca como paga
        comissao.status_pagamento = 'paga'
        comissao.data_pagamento = timezone.now()
        comissao.save()
        
        return comissao
    
    @staticmethod
    def obter_comissoes_funcionario(funcionario, status=None):
        """
        Obtém comissões de um funcionário
        
        Args:
            funcionario: Funcionário
            status: Filtrar por status (opcional)
            
        Returns:
            QuerySet de Comissao
        """
        comissoes = Comissao.objects.filter(funcionario=funcionario)
        
        if status:
            comissoes = comissoes.filter(status_pagamento=status)
        
        return comissoes.order_by('-criado_em')
    
    @staticmethod
    def calcular_total_periodo(funcionario, data_inicio, data_fim):
        """
        Calcula total de comissões de um funcionário em um período
        
        Returns:
            dict com totais por status
        """
        from django.db.models import Sum, Q
        
        comissoes = Comissao.objects.filter(
            funcionario=funcionario,
            criado_em__date__gte=data_inicio,
            criado_em__date__lte=data_fim
        )
        
        resultado = {
            'pendente': comissoes.filter(status_pagamento='pendente').aggregate(total=Sum('valor'))['total'] or 0,
            'aprovada': comissoes.filter(status_pagamento='aprovada').aggregate(total=Sum('valor'))['total'] or 0,
            'paga': comissoes.filter(status_pagamento='paga').aggregate(total=Sum('valor'))['total'] or 0,
            'total_geral': comissoes.aggregate(total=Sum('valor'))['total'] or 0,
        }
        
        return resultado

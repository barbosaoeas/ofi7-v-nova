"""
Services para Peças
Centraliza regras de negócio de peças
"""
from django.db import transaction
from django.utils import timezone
from .models import Peca


class PecaService:
    """
    Service para gerenciar Peças
    """
    
    @staticmethod
    @transaction.atomic
    def criar_peca_bloqueante(etapa, observacao, solicitado_por):
        """
        Cria uma peça que está bloqueando uma etapa
        
        Args:
            etapa: OrdemEtapa que está bloqueada
            observacao: Descrição da peça necessária
            solicitado_por: Funcionário que solicitou
            
        Returns:
            Peca: Peça criada
        """
        peca = Peca.objects.create(
            veiculo=etapa.ordem.veiculo,
            orcamento=getattr(etapa.ordem, 'orcamento', None),
            ordem=etapa.ordem,
            etapa_bloqueada=etapa,
            descricao=observacao or f"Peça necessária para {etapa.nome}",
            fornecedor_tipo='escritorio',  # padrão
            solicitado_por=solicitado_por,
            status='falta_comprar',
            observacao=observacao
        )
        
        return peca
    
    @staticmethod
    @transaction.atomic
    def marcar_como_recebida(peca_id):
        """
        Marca uma peça como recebida e libera a etapa bloqueada
        
        Args:
            peca_id: ID da peça
            
        Returns:
            dict: {'peca': Peca, 'etapa_liberada': OrdemEtapa}
        """
        peca = Peca.objects.get(id=peca_id)
        
        # Validação
        if peca.status == 'recebida':
            raise ValueError("Peça já foi marcada como recebida")
        
        # Atualiza peça
        peca.status = 'recebida'
        peca.data_recebimento = timezone.now()
        peca.save()
        
        # Libera etapa bloqueada (volta para pendente)
        etapa_liberada = None
        if peca.etapa_bloqueada:
            etapa = peca.etapa_bloqueada
            if etapa.status == 'aguardando_peca':
                etapa.status = 'programado' if etapa.funcionario_id else 'aguardando'
                etapa.save()
                etapa_liberada = etapa
                
                # Atualiza status da ordem
                from apps.ordens.services import OrdemServicoService
                OrdemServicoService.atualizar_status_ordem(etapa.ordem)
        
        return {
            'peca': peca,
            'etapa_liberada': etapa_liberada
        }
    
    @staticmethod
    def obter_pecas_atrasadas():
        """
        Retorna todas as peças atrasadas
        
        Returns:
            QuerySet de Peca
        """
        from django.utils import timezone
        hoje = timezone.now().date()
        
        return Peca.objects.filter(
            prazo_chegada__isnull=False,
            prazo_chegada__lt=hoje,
        ).exclude(status__in=['recebida', 'cancelada']).order_by('prazo_chegada')
    
    @staticmethod
    def obter_alertas_pecas():
        """
        Retorna alertas sobre peças
        
        Returns:
            dict com contadores
        """
        from django.utils import timezone
        hoje = timezone.now().date()
        
        return {
            'atrasadas': Peca.objects.filter(
                prazo_chegada__isnull=False,
                prazo_chegada__lt=hoje,
            ).exclude(status__in=['recebida', 'cancelada']).count(),
            'chegam_hoje': Peca.objects.filter(
                prazo_chegada=hoje,
            ).exclude(status__in=['recebida', 'cancelada']).count(),
            'falta_comprar': Peca.objects.filter(
                status='falta_comprar'
            ).count(),
        }

"""
Views/API para Orçamentos
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Orcamento
from .serializers import (
    OrcamentoSerializer,
    OrcamentoListSerializer,
    OrcamentoCreateSerializer
)
from apps.ordens.services import OrdemServicoService


class OrcamentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Orçamentos
    
    list: Listar todos os orçamentos
    create: Criar novo orçamento
    retrieve: Detalhar um orçamento
    update: Atualizar orçamento completo
    partial_update: Atualizar orçamento parcialmente
    destroy: Deletar orçamento
    gerar_os: Gerar Ordem de Serviço a partir do orçamento aprovado
    """
    
    queryset = Orcamento.objects.select_related(
        'cliente', 'veiculo', 'criado_por'
    ).prefetch_related('itens').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero', 'cliente__nome', 'veiculo__placa']
    ordering_fields = ['data_orcamento', 'criado_em']
    ordering = ['-criado_em']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrcamentoCreateSerializer
        elif self.action == 'list':
            return OrcamentoListSerializer
        return OrcamentoSerializer
    
    def perform_create(self, serializer):
        """Define o criado_por automaticamente"""
        serializer.save(criado_por=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='gerar-os')
    def gerar_os(self, request, pk=None):
        """
        POST /api/orcamentos/orcamentos/{id}/gerar-os/
        
        Gera uma Ordem de Serviço a partir do orçamento aprovado.
        O orçamento precisa estar com status 'aprovado'.
        """
        orcamento = self.get_object()
        
        try:
            ordem = OrdemServicoService.criar_de_orcamento(
                orcamento_id=orcamento.id,
                criado_por=request.user
            )
            
            from apps.ordens.serializers import OrdemServicoDetailSerializer
            return Response(
                OrdemServicoDetailSerializer(ordem).data,
                status=status.HTTP_201_CREATED
            )
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

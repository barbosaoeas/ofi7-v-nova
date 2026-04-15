"""
Views/API para Peças
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .models import Peca
from .serializers import PecaSerializer, MarcarPecaRecebidaSerializer
from .services import PecaService


class PecaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Peças
    
    list: Listar todas as peças
    create: Criar uma nova peça
    retrieve: Detalhar uma peça
    update: Atualizar uma peça
    partial_update: Atualizar parcialmente uma peça
    destroy: Deletar uma peça
    atrasadas: Listar peças atrasadas
    alertas: Obter alertas de peças
    marcar_recebida: Marcar peça como recebida
    """
    
    queryset = Peca.objects.all()
    serializer_class = PecaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros opcionais
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        ordem_id = self.request.query_params.get('ordem')
        if ordem_id:
            queryset = queryset.filter(ordem_id=ordem_id)
        
        return queryset.select_related(
            'ordem',
            'ordem__cliente',
            'ordem__veiculo',
            'etapa_bloqueada',
            'solicitado_por'
        )
    
    @extend_schema(
        summary="Peças Atrasadas",
        description="Lista todas as peças atrasadas",
        responses={200: PecaSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def atrasadas(self, request):
        """
        GET /api/pecas/pecas/atrasadas/
        
        Retorna todas as peças atrasadas
        """
        pecas = PecaService.obter_pecas_atrasadas()
        serializer = PecaSerializer(pecas, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Alertas de Peças",
        description="Retorna contadores de alertas sobre peças",
        responses={200: {
            "type": "object",
            "properties": {
                "atrasadas": {"type": "integer"},
                "chegam_hoje": {"type": "integer"},
                "aguardando_aprovacao": {"type": "integer"}
            }
        }}
    )
    @action(detail=False, methods=['get'])
    def alertas(self, request):
        """
        GET /api/pecas/pecas/alertas/
        
        Retorna alertas sobre peças
        """
        alertas = PecaService.obter_alertas_pecas()
        return Response(alertas)
    
    @extend_schema(
        summary="Marcar Peça como Recebida",
        description="Marca uma peça como recebida e libera a etapa bloqueada",
        request=MarcarPecaRecebidaSerializer,
        responses={
            200: {"description": "Peça marcada como recebida"},
            400: {"description": "Erro de validação"}
        }
    )
    @action(detail=True, methods=['post'], url_path='marcar-recebida')
    def marcar_recebida(self, request, pk=None):
        """
        POST /api/pecas/pecas/{id}/marcar-recebida/
        
        Marca uma peça como recebida.
        Se a peça estava bloqueando uma etapa, libera a etapa.
        """
        peca = self.get_object()
        
        try:
            resultado = PecaService.marcar_como_recebida(peca.id)
            
            response_data = {
                'peca': PecaSerializer(resultado['peca']).data,
                'etapa_liberada': None
            }
            
            if resultado['etapa_liberada']:
                from apps.ordens.serializers import OrdemEtapaListSerializer
                response_data['etapa_liberada'] = OrdemEtapaListSerializer(
                    resultado['etapa_liberada']
                ).data
            
            return Response(response_data)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


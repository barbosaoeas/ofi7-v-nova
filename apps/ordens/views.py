"""
Views/API para Ordens de Serviço
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q

from .models import OrdemServico, OrdemEtapa
from .serializers import (
    OrdemServicoListSerializer,
    OrdemServicoDetailSerializer,
    OrdemEtapaListSerializer,
    OrdemEtapaDetailSerializer,
    IniciarEtapaSerializer,
    ConcluirEtapaSerializer,
    MinhasEtapasResponseSerializer,
)
from .services import OrdemServicoService, OrdemEtapaService


class OrdemServicoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Ordens de Serviço
    
    list: Listar todas as ordens
    retrieve: Detalhar uma ordem específica
    """
    
    queryset = OrdemServico.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrdemServicoDetailSerializer
        return OrdemServicoListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros opcionais
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        return queryset.select_related('cliente', 'veiculo', 'criado_por')


class OrdemEtapaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Etapas das Ordens
    
    list: Listar todas as etapas
    retrieve: Detalhar uma etapa específica
    minhas_etapas: Minhas tarefas (funcionário logado)
    iniciar: Iniciar uma etapa
    concluir: Concluir uma etapa
    """
    
    queryset = OrdemEtapa.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrdemEtapaDetailSerializer
        elif self.action == 'iniciar':
            return IniciarEtapaSerializer
        elif self.action == 'concluir':
            return ConcluirEtapaSerializer
        elif self.action == 'minhas_etapas':
            return MinhasEtapasResponseSerializer
        return OrdemEtapaListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros opcionais
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        funcionario_id = self.request.query_params.get('funcionario')
        if funcionario_id:
            queryset = queryset.filter(funcionario_id=funcionario_id)
        
        return queryset.select_related(
            'ordem',
            'ordem__cliente',
            'ordem__veiculo',
            'funcionario'
        )
    
    @extend_schema(
        summary="Minhas Etapas",
        description="Retorna as etapas do funcionário logado organizadas por status",
        responses={200: MinhasEtapasResponseSerializer}
    )
    @action(detail=False, methods=['get'], url_path='minhas-etapas')
    def minhas_etapas(self, request):
        """
        GET /api/ordens/etapas/minhas-etapas/
        
        Retorna as etapas do funcionário logado:
        - programadas_hoje: Etapas programadas para hoje
        - em_andamento: Etapa que está executando (máximo 1)
        - aguardando_peca: Etapas aguardando peça
        """
        funcionario = request.user
        
        etapas = OrdemEtapaService.obter_etapas_funcionario(
            funcionario=funcionario,
            apenas_hoje=True
        )
        
        serializer = MinhasEtapasResponseSerializer(etapas)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Iniciar Etapa",
        description="Inicia uma etapa. Funcionário não pode ter outra etapa em andamento.",
        request=IniciarEtapaSerializer,
        responses={
            200: OrdemEtapaDetailSerializer,
            400: {"description": "Erro de validação"}
        }
    )
    @action(detail=True, methods=['post'], url_path='iniciar')
    def iniciar(self, request, pk=None):
        """
        POST /api/ordens/etapas/{id}/iniciar/
        
        Inicia uma etapa.
        
        Validações:
        - Etapa deve estar com status 'pendente'
        - Funcionário não pode ter outra tarefa em andamento
        """
        etapa = self.get_object()
        funcionario = request.user
        
        try:
            etapa_atualizada = OrdemEtapaService.iniciar_etapa(
                etapa_id=etapa.id,
                funcionario=funcionario
            )
            
            serializer = OrdemEtapaDetailSerializer(etapa_atualizada)
            return Response(serializer.data)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Concluir Etapa",
        description="Conclui uma etapa. Pode marcar como aguardando peça ou concluir definitivamente.",
        request=ConcluirEtapaSerializer,
        responses={
            200: {"description": "Etapa concluída com sucesso"},
            400: {"description": "Erro de validação"}
        }
    )
    @action(detail=True, methods=['post'], url_path='concluir')
    def concluir(self, request, pk=None):
        """
        POST /api/ordens/etapas/{id}/concluir/

        Conclui uma etapa.

        Payload (opcional):
        {
            "tem_peca_pendente": false,
            "observacao_peca": "Descrição da peça (se tem_peca_pendente=true)"
        }

        Processo:
        - Se tem_peca_pendente=true:
          → Marca etapa como 'aguardando_peca'
          → Cria registro de Peça
        - Se tem_peca_pendente=false:
          → Marca etapa como 'concluido'
          → Gera comissão automaticamente
          → Libera próxima etapa
        """
        etapa = self.get_object()

        serializer = ConcluirEtapaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            resultado = OrdemEtapaService.concluir_etapa(
                etapa_id=etapa.id,
                tem_peca_pendente=serializer.validated_data.get('tem_peca_pendente', False),
                observacao_peca=serializer.validated_data.get('observacao_peca', '')
            )

            # Monta response
            response_data = {
                'etapa': OrdemEtapaDetailSerializer(resultado['etapa']).data,
                'comissao': [],
                'proxima_etapa': None,
                'peca_criada': None,
            }

            if resultado['comissao']:
                from apps.comissoes.serializers import ComissaoSerializer
                response_data['comissao'] = ComissaoSerializer(resultado['comissao'], many=True).data

            if resultado['proxima_etapa']:
                response_data['proxima_etapa'] = OrdemEtapaListSerializer(resultado['proxima_etapa']).data

            if resultado['peca_criada']:
                from apps.pecas.serializers import PecaSerializer
                response_data['peca_criada'] = PecaSerializer(resultado['peca_criada']).data

            return Response(response_data)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

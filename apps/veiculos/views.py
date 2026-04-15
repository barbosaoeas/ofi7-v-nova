"""
Views/API para Veículos
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated

from .models import Veiculo
from .serializers import VeiculoSerializer, VeiculoListSerializer


class VeiculoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Veículos
    
    list: Listar todos os veículos
    create: Criar novo veículo
    retrieve: Detalhar um veículo
    update: Atualizar veículo completo
    partial_update: Atualizar veículo parcialmente
    destroy: Deletar veículo
    """
    
    queryset = Veiculo.objects.select_related('cliente').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['placa', 'marca', 'modelo', 'chassi', 'cliente__nome']
    ordering_fields = ['placa', 'marca', 'modelo', 'criado_em']
    ordering = ['placa']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return VeiculoListSerializer
        return VeiculoSerializer

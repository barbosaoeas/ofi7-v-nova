"""
Views/API para Produção
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated

from .models import EtapaPadrao
from .serializers import EtapaPadraoSerializer


class EtapaPadraoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Etapas Padrão
    
    list: Listar todas as etapas padrão
    create: Criar nova etapa padrão
    retrieve: Detalhar uma etapa
    update: Atualizar etapa completa
    partial_update: Atualizar etapa parcialmente
    destroy: Deletar etapa
    """
    
    queryset = EtapaPadrao.objects.all()
    serializer_class = EtapaPadraoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['sequencia', 'nome']
    ordering = ['sequencia']

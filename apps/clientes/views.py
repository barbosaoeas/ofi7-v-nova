"""
Views/API para Clientes
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated

from .models import Cliente
from .serializers import ClienteSerializer, ClienteListSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Clientes

    list: Listar todos os clientes
    create: Criar novo cliente
    retrieve: Detalhar um cliente
    update: Atualizar cliente completo
    partial_update: Atualizar cliente parcialmente
    destroy: Deletar cliente
    """

    queryset = Cliente.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'cpf_cnpj', 'telefone', 'email']
    ordering_fields = ['nome', 'criado_em']
    ordering = ['nome']

    def get_serializer_class(self):
        if self.action == 'list':
            return ClienteListSerializer
        return ClienteSerializer

    def get_queryset(self):
        """Adiciona filtros manuais"""
        queryset = super().get_queryset()

        # Filtros query params
        tipo = self.request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        ativo = self.request.query_params.get('ativo')
        if ativo is not None:
            queryset = queryset.filter(ativo=ativo.lower() == 'true')

        cidade = self.request.query_params.get('cidade')
        if cidade:
            queryset = queryset.filter(cidade__icontains=cidade)

        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset

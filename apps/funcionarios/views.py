"""
Views/API para Funcionários
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated

from .models import Funcionario
from .serializers import (
    FuncionarioSerializer,
    FuncionarioListSerializer,
    FuncionarioCreateSerializer
)


class FuncionarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Funcionários
    
    list: Listar todos os funcionários
    create: Criar novo funcionário
    retrieve: Detalhar um funcionário
    update: Atualizar funcionário completo
    partial_update: Atualizar funcionário parcialmente
    destroy: Deletar funcionário
    """
    
    queryset = Funcionario.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'cpf', 'email']
    ordering_fields = ['username', 'first_name', 'criado_em']
    ordering = ['first_name', 'last_name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FuncionarioCreateSerializer
        elif self.action == 'list':
            return FuncionarioListSerializer
        return FuncionarioSerializer

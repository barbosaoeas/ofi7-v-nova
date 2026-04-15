"""
Views/API para Comissões
"""
from datetime import date, datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .models import Comissao
from apps.funcionarios.models import Funcionario
from .serializers import (
    ComissaoSerializer,
    AprovarComissaoSerializer,
    MarcarComoPagaSerializer
)
from .services import ComissaoService


class ComissaoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Comissões
    
    list: Listar todas as comissões
    retrieve: Detalhar uma comissão
    minhas: Minhas comissões (funcionário logado)
    aprovar: Aprovar uma comissão (requer permissão)
    marcar_paga: Marcar como paga (requer permissão)
    """
    
    queryset = Comissao.objects.all()
    serializer_class = ComissaoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros opcionais
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status_pagamento=status_param)
        
        funcionario_id = self.request.query_params.get('funcionario')
        if funcionario_id:
            queryset = queryset.filter(funcionario_id=funcionario_id)
        
        return queryset.select_related(
            'funcionario',
            'ordem',
            'etapa',
            'aprovado_por'
        )
    
    @extend_schema(
        summary="Minhas Comissões",
        description="Retorna as comissões do funcionário logado",
        responses={200: ComissaoSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def minhas(self, request):
        """
        GET /api/comissoes/comissoes/minhas/
        
        Retorna as comissões do funcionário logado
        """
        funcionario = request.user
        comissoes = ComissaoService.obter_comissoes_funcionario(funcionario)
        serializer = ComissaoSerializer(comissoes, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Aprovar Comissão",
        description="Aprova uma comissão (requer permissão de supervisor ou superior)",
        request=AprovarComissaoSerializer,
        responses={
            200: ComissaoSerializer,
            400: {"description": "Erro de validação"},
            403: {"description": "Sem permissão"}
        }
    )
    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        """
        POST /api/comissoes/comissoes/{id}/aprovar/
        
        Aprova uma comissão.
        Requer perfil de supervisor, gerente ou admin.
        """
        comissao = self.get_object()
        aprovado_por = request.user
        
        try:
            comissao_aprovada = ComissaoService.aprovar_comissao(
                comissao_id=comissao.id,
                aprovado_por=aprovado_por
            )
            
            serializer = ComissaoSerializer(comissao_aprovada)
            return Response(serializer.data)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Marcar como Paga",
        description="Marca uma comissão como paga",
        request=MarcarComoPagaSerializer,
        responses={
            200: ComissaoSerializer,
            400: {"description": "Erro de validação"}
        }
    )
    @action(detail=True, methods=['post'], url_path='marcar-paga')
    def marcar_paga(self, request, pk=None):
        """
        POST /api/comissoes/comissoes/{id}/marcar-paga/
        
        Marca uma comissão como paga.
        """
        comissao = self.get_object()
        
        try:
            comissao_paga = ComissaoService.marcar_como_paga(comissao.id)
            
            serializer = ComissaoSerializer(comissao_paga)
            return Response(serializer.data)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@login_required
def relatorio_comissoes(request):
    hoje = date.today()
    data_inicio_str = request.GET.get('de') or str(hoje.replace(day=1))
    data_fim_str = request.GET.get('ate') or str(hoje)
    status_pagamento = request.GET.get('status') or ''
    funcionario_id = request.GET.get('funcionario') or ''

    try:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        data_inicio = hoje.replace(day=1)
        data_fim = hoje

    qs = Comissao.objects.select_related('funcionario', 'ordem', 'etapa').all()

    pode_ver_todos = request.user.is_superuser or getattr(request.user, 'perfil', '') != 'operacional'
    if not pode_ver_todos:
        qs = qs.filter(funcionario=request.user)

    qs = qs.filter(
        models.Q(
            data_execucao__isnull=False,
            data_execucao__gte=data_inicio,
            data_execucao__lte=data_fim,
        )
        | models.Q(
            data_execucao__isnull=True,
            criado_em__date__gte=data_inicio,
            criado_em__date__lte=data_fim,
        )
    )

    if status_pagamento:
        qs = qs.filter(status_pagamento=status_pagamento)

    if funcionario_id and pode_ver_todos:
        qs = qs.filter(funcionario_id=funcionario_id)

    funcionario_nome = 'Todos'
    if pode_ver_todos:
        if funcionario_id:
            f = Funcionario.objects.filter(id=funcionario_id).first()
            if f:
                funcionario_nome = f.get_full_name() or f.username
    else:
        funcionario_nome = request.user.get_full_name() or request.user.username

    totais = qs.aggregate(
        total=Sum('valor'),
        em_aberto=Sum('valor', filter=models.Q(status_pagamento='pendente')),
        pago=Sum('valor', filter=models.Q(status_pagamento='paga')),
    )

    context = {
        'comissoes': qs.order_by('-data_execucao', '-criado_em')[:500],
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'data_inicio_str': data_inicio_str,
        'data_fim_str': data_fim_str,
        'funcionario_nome': funcionario_nome,
        'status_filtro': status_pagamento,
        'funcionario_filtro': funcionario_id,
        'pode_ver_todos': pode_ver_todos,
        'funcionarios': Funcionario.objects.filter(ativo=True).order_by('first_name', 'last_name') if pode_ver_todos else Funcionario.objects.none(),
        'totais': {
            'total': totais.get('total') or 0,
            'em_aberto': totais.get('em_aberto') or 0,
            'pago': totais.get('pago') or 0,
        }
    }
    return render(request, 'comissoes/relatorio_comissoes.html', context)

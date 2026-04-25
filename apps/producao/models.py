"""
Models para Produção (Kanban)
"""
from django.db import models


class EtapaPadrao(models.Model):
    """
    Model de Etapas Padrões do processo
    Define as etapas fixas do Kanban
    """
    
    # Etapas fixas do sistema
    nome = models.CharField('Nome', max_length=50, unique=True)
    sequencia = models.IntegerField('Sequência', unique=True)
    cor = models.CharField('Cor (hex)', max_length=7, default='#3B82F6')
    ativa = models.BooleanField('Ativa', default=True)
    
    # Configurações
    gera_comissao = models.BooleanField(
        'Gera Comissão',
        default=True,
        help_text='Define se etapas deste tipo geram comissão ao serem concluídas'
    )
    percentual_comissao_padrao = models.DecimalField(
        'Percentual de Comissão Padrão (%)',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Percentual padrão para esta etapa'
    )
    
    # Timestamps
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Etapa Padrão'
        verbose_name_plural = 'Etapas Padrão'
        ordering = ['sequencia']
    
    def __str__(self):
        return f"{self.sequencia}. {self.nome}"


# Dados iniciais das etapas fixas
ETAPAS_PADRAO = [
    {'nome': 'Pátio', 'sequencia': 1, 'cor': '#6B7280'},
    {'nome': 'Desmontagem', 'sequencia': 2, 'cor': '#EF4444'},
    {'nome': 'Funilaria', 'sequencia': 3, 'cor': '#F59E0B'},
    {'nome': 'Preparação Pintura', 'sequencia': 4, 'cor': '#10B981'},
    {'nome': 'Pintura', 'sequencia': 5, 'cor': '#3B82F6'},
    {'nome': 'Montagem', 'sequencia': 6, 'cor': '#8B5CF6'},
    {'nome': 'Polimento', 'sequencia': 7, 'cor': '#EC4899'},
    {'nome': 'Mecânica', 'sequencia': 8, 'cor': '#0EA5E9'},
    {'nome': 'Preparação Entrega', 'sequencia': 9, 'cor': '#14B8A6'},
    {'nome': 'Finalizado', 'sequencia': 10, 'cor': '#22C55E'},
]

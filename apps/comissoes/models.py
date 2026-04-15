"""
Models para Comissões
"""
from django.db import models
from decimal import Decimal


class Comissao(models.Model):
    """
    Model de Comissão
    Gerada automaticamente ao concluir uma etapa
    """
    
    STATUS_PAGAMENTO_CHOICES = [
        ('pendente', 'Em aberto'),
        ('aprovada', 'Aprovada'),
        ('paga', 'Pago'),
        ('cancelada', 'Cancelada'),
    ]
    
    # Relacionamentos
    funcionario = models.ForeignKey(
        'funcionarios.Funcionario',
        on_delete=models.PROTECT,
        related_name='comissoes',
        verbose_name='Funcionário'
    )
    ordem = models.ForeignKey(
        'ordens.OrdemServico',
        on_delete=models.PROTECT,
        related_name='comissoes',
        verbose_name='Ordem de Serviço'
    )
    etapa = models.ForeignKey(
        'ordens.OrdemEtapa',
        on_delete=models.PROTECT,
        related_name='comissoes',
        verbose_name='Etapa'
    )
    aprovado_por = models.ForeignKey(
        'funcionarios.Funcionario',
        on_delete=models.PROTECT,
        related_name='comissoes_aprovadas',
        verbose_name='Aprovado por',
        null=True,
        blank=True
    )
    
    # Valores
    valor_servico = models.DecimalField(
        'Valor do Serviço',
        max_digits=10,
        decimal_places=2,
        help_text='Valor da etapa no momento da geração'
    )
    percentual = models.DecimalField(
        'Percentual (%)',
        max_digits=5,
        decimal_places=2,
        help_text='Percentual usado no cálculo'
    )
    valor = models.DecimalField(
        'Valor da Comissão',
        max_digits=10,
        decimal_places=2,
        help_text='Calculado: valor_servico * percentual / 100'
    )
    
    # Tempo
    tempo_execucao_horas = models.DecimalField(
        'Tempo de Execução (horas)',
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Status
    status_pagamento = models.CharField(
        'Status do Pagamento',
        max_length=15,
        choices=STATUS_PAGAMENTO_CHOICES,
        default='pendente'
    )
    
    # Datas
    data_execucao = models.DateField('Data de Execução', null=True, blank=True)
    data_aprovacao = models.DateTimeField('Data de Aprovação', null=True, blank=True)
    data_pagamento = models.DateTimeField('Data de Pagamento', null=True, blank=True)
    
    # Observações
    observacao = models.TextField('Observação', blank=True)
    
    # Timestamps
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Comissão'
        verbose_name_plural = 'Comissões'
        ordering = ['-criado_em']
        constraints = [
            models.UniqueConstraint(fields=['etapa', 'funcionario'], name='uniq_comissao_etapa_funcionario'),
        ]
    
    def __str__(self):
        return f"Comissão {self.funcionario.nome_completo} - {self.ordem.numero} - R$ {self.valor}"
    
    @staticmethod
    def calcular_valor(valor_servico, percentual):
        """Calcula o valor da comissão"""
        return (valor_servico * percentual) / 100
    
    def save(self, *args, **kwargs):
        # Calcula o valor automaticamente
        if not self.valor or self.valor == Decimal('0.00'):
            self.valor = self.calcular_valor(self.valor_servico, self.percentual)
        super().save(*args, **kwargs)

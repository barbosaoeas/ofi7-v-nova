"""
Models para Orçamentos
"""
from django.db import models
from decimal import Decimal


class EtapaPadrao(models.Model):
    """
    Model de Etapas Padrão do Orçamento.
    Ex: Desmontagem, Funilaria, Pintura, etc.
    """
    nome = models.CharField('Nome da Etapa', max_length=50, unique=True)
    descricao = models.TextField('Descrição Padrão', blank=True)
    ordem_default = models.IntegerField('Ordem de Exibição', default=0, help_text='Ex: 10, 20, 30 (impacta na ordenação)')
    ativo = models.BooleanField('Ativo', default=True)

    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Etapa Padrão'
        verbose_name_plural = 'Etapas Padrões'
        ordering = ['ordem_default', 'nome']

    def __str__(self):
        return self.nome


class Orcamento(models.Model):
    """
    Model de Orçamento
    """
    
    STATUS_CHOICES = [
        ('rascunho', 'Aguardando Resposta'),
        ('enviado', 'Enviado'),
        ('aprovado', 'Aprovado'),
        ('entregue', 'Entregue'),
        ('retrabalho', 'Retrabalho'),
        ('rejeitado', 'Rejeitado'),
        ('cancelado', 'Cancelado'),
    ]
    
    # Relacionamentos
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='orcamentos',
        verbose_name='Cliente'
    )
    veiculo = models.ForeignKey(
        'veiculos.Veiculo',
        on_delete=models.PROTECT,
        related_name='orcamentos',
        verbose_name='Veículo'
    )
    criado_por = models.ForeignKey(
        'funcionarios.Funcionario',
        on_delete=models.PROTECT,
        related_name='orcamentos_criados',
        verbose_name='Criado por'
    )
    
    # Dados do orçamento
    numero = models.CharField('Número', max_length=20, unique=True, editable=False)
    data_orcamento = models.DateField('Data do Orçamento', auto_now_add=True)
    validade = models.DateField('Validade', null=True, blank=True)
    data_agendada = models.DateField('Agenda (Entrada na Oficina)', null=True, blank=True)
    data_prevista_entrega = models.DateField('Previsão de Entrega', null=True, blank=True)
    
    # Status
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='rascunho'
    )

    perda_total = models.BooleanField('Perda Total', default=False)
    
    # Valores
    desconto = models.DecimalField(
        'Desconto',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    observacoes = models.TextField('Observações', blank=True)
    
    # Timestamps
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"Orçamento {self.numero} - {self.cliente.nome}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Gera número automático
            ultimo = Orcamento.objects.order_by('-id').first()
            proximo_numero = 1 if not ultimo else ultimo.id + 1
            self.numero = f"ORC-{proximo_numero:06d}"
        super().save(*args, **kwargs)
    
    @property
    def valor_total_servicos(self):
        """Calcula o valor total dos itens do orçamento"""
        return sum(item.valor for item in self.itens.filter(retrabalho=False))

    @property
    def valor_prejuizo_retrabalho(self):
        return sum(item.valor for item in self.itens.filter(retrabalho=True))

    @property
    def valor_total_pecas(self):
        """Calcula o valor total das peças fornecidas pelo escritório"""
        return sum(peca.valor_venda for peca in self.pecas.filter(fornecedor_tipo='escritorio'))

    @property
    def valor_total_terceiros(self):
        """Calcula o valor de serviços efetuados por terceiros no orçamento"""
        return sum(servico.valor for servico in self.servicos_terceiros.all())

    @property
    def valor_total_geral(self):
        """Calcula o valor total (Serviços + Peças Oficina + Terceiros)"""
        return self.valor_total_servicos + self.valor_total_pecas + self.valor_total_terceiros

    @property
    def valor_total_com_desconto(self):
        """Aplica o desconto sobre o valor total geral"""
        total = self.valor_total_geral
        if self.desconto > 0:
            total -= self.desconto
        return total


class OrcamentoAditivo(models.Model):
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('enviado', 'Enviado ao Cliente'),
        ('ciente', 'Ciente (Aprovado pelo Cliente)'),
    ]

    orcamento = models.ForeignKey(
        Orcamento,
        on_delete=models.CASCADE,
        related_name='aditivos',
        verbose_name='Orçamento',
    )
    criado_por = models.ForeignKey(
        'funcionarios.Funcionario',
        on_delete=models.PROTECT,
        related_name='aditivos_orcamento_criados',
        verbose_name='Criado por',
    )
    numero = models.CharField('Número', max_length=20, unique=True, editable=False)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='rascunho')
    observacoes = models.TextField('Observações', blank=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Aditivo de Orçamento'
        verbose_name_plural = 'Aditivos de Orçamento'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.numero} ({self.orcamento.numero})"

    def save(self, *args, **kwargs):
        if not self.numero:
            ultimo = OrcamentoAditivo.objects.order_by('-id').first()
            proximo_numero = 1 if not ultimo else ultimo.id + 1
            self.numero = f"ADT-{proximo_numero:06d}"
        super().save(*args, **kwargs)


class OrcamentoRevisao(models.Model):
    orcamento = models.ForeignKey(
        Orcamento,
        on_delete=models.CASCADE,
        related_name='revisoes',
        verbose_name='Orçamento',
    )
    criado_por = models.ForeignKey(
        'funcionarios.Funcionario',
        on_delete=models.PROTECT,
        related_name='revisoes_orcamento_criadas',
        verbose_name='Criado por',
    )
    numero = models.CharField('Número', max_length=20, unique=True, editable=False)
    motivo = models.TextField('Motivo da Revisão', blank=True)
    snapshot_antes = models.JSONField('Snapshot Antes')
    snapshot_depois = models.JSONField('Snapshot Depois', null=True, blank=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    confirmado_em = models.DateTimeField('Confirmado em', null=True, blank=True)

    class Meta:
        verbose_name = 'Revisão de Orçamento'
        verbose_name_plural = 'Revisões de Orçamento'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.numero} ({self.orcamento.numero})"

    def save(self, *args, **kwargs):
        if not self.numero:
            ultimo = OrcamentoRevisao.objects.order_by('-id').first()
            proximo_numero = 1 if not ultimo else ultimo.id + 1
            self.numero = f"REV-{proximo_numero:06d}"
        super().save(*args, **kwargs)


class OrcamentoItem(models.Model):
    """
    Model de Item de Orçamento
    Cada item representa um serviço e vira uma OrdemEtapa quando aprovado
    """
    
    # Relacionamento
    orcamento = models.ForeignKey(
        Orcamento,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Orçamento'
    )
    
    # Dados do serviço
    descricao = models.CharField('Descrição', max_length=200)
    
    etapa = models.ForeignKey(
        'EtapaPadrao',
        on_delete=models.PROTECT,
        verbose_name='Etapa',
        null=True,
        help_text='Etapa padronizada (ex: Funilaria, Pintura)'
    )
    horas_previstas = models.DecimalField(
        'Horas Previstas',
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Tempo estimado da atividade em horas'
    )
    valor = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    retrabalho = models.BooleanField(
        'Retrabalho',
        default=False,
        help_text='Marque se for uma etapa de retrabalho (perda/prejuízo sem receita)'
    )
    
    # Ordem de exibição
    ordem = models.IntegerField('Ordem', default=0)
    
    # Timestamps
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Item de Orçamento'
        verbose_name_plural = 'Itens de Orçamento'
        ordering = ['ordem', 'id']
    
    def __str__(self):
        return f"{self.descricao} - {self.valor}"


class OrcamentoServicoTerceiro(models.Model):
    """
    Model de Serviço/Produto Terceirizado em um orçamento.
    Utilizado para Retíficas, Especialistas externos, Fornecedores diversos.
    """
    
    orcamento = models.ForeignKey(
        Orcamento,
        on_delete=models.CASCADE,
        related_name='servicos_terceiros',
        verbose_name='Orçamento'
    )
    
    descricao = models.CharField('Descrição do Serviço/Peça', max_length=200, blank=True)
    
    fornecedor = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        verbose_name='Fornecedor / Especialista',
        limit_choices_to={'categoria__in': ['fornecedor', 'ambos']}
    )
    
    valor = models.DecimalField('Valor (R$)', max_digits=10, decimal_places=2)
    ordem = models.IntegerField('Ordem', default=0)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Serviço Terceirizado de Orçamento'
        verbose_name_plural = 'Serviços Terceirizados de Orçamentos'
        ordering = ['ordem', 'criado_em']

    def __str__(self):
        return f"{self.fornecedor.nome} - {self.valor}"

"""
Models para Peças
"""
from django.db import models
from django.utils import timezone
from decimal import Decimal


class Peca(models.Model):
    """
    Model de Peça
    Controla peças necessárias para a execução das ordens de serviço
    """
    
    FORNECEDOR_TIPO_CHOICES = [
        ('cliente', 'Cliente'),
        ('seguradora', 'Seguradora'),
        ('escritorio', 'Escritório'),
    ]
    
    STATUS_CHOICES = [
        ('solicitada', 'Solicitada'),
        ('falta_comprar', 'Falta Comprar'),
        ('comprada', 'Peça Comprada'),
        ('atrasada', 'Peça Atrasada'),
        ('recebida', 'Recebida'),
        ('cancelada', 'Cancelada'),
    ]
    
    # Relacionamentos
    veiculo = models.ForeignKey(
        'veiculos.Veiculo',
        on_delete=models.SET_NULL,
        related_name='pecas',
        verbose_name='Veículo',
        null=True,
        blank=True,
        help_text='Vincule esta peça a um veículo específico'
    )
    fornecedor = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.SET_NULL,
        related_name='pecas_fornecidas',
        verbose_name='Fornecedor (Cliente)',
        null=True,
        blank=True,
        help_text='Selecione o fornecedor cadastrado no sistema'
    )
    orcamento = models.ForeignKey(
        'orcamentos.Orcamento',
        on_delete=models.SET_NULL,
        related_name='pecas',
        verbose_name='Orçamento',
        null=True,
        blank=True
    )
    aditivo = models.ForeignKey(
        'orcamentos.OrcamentoAditivo',
        on_delete=models.SET_NULL,
        related_name='pecas',
        verbose_name='Aditivo',
        null=True,
        blank=True
    )
    ordem = models.ForeignKey(
        'ordens.OrdemServico',
        on_delete=models.CASCADE,
        related_name='pecas',
        verbose_name='Ordem de Serviço',
        null=True,
        blank=True
    )
    etapa_bloqueada = models.ForeignKey(
        'ordens.OrdemEtapa',
        on_delete=models.SET_NULL,
        related_name='pecas_bloqueantes',
        verbose_name='Etapa Bloqueada',
        null=True,
        blank=True,
        help_text='Etapa que está aguardando esta peça'
    )
    solicitado_por = models.ForeignKey(
        'funcionarios.Funcionario',
        on_delete=models.PROTECT,
        related_name='pecas_solicitadas',
        verbose_name='Solicitado por'
    )
    
    # Dados da peça
    descricao = models.CharField('Descrição', max_length=200)
    quantidade = models.IntegerField('Quantidade', default=1)
    
    # Fornecedor
    fornecedor_tipo = models.CharField(
        'Tipo de Fornecedor',
        max_length=15,
        choices=FORNECEDOR_TIPO_CHOICES
    )
    fornecedor_nome = models.CharField('Nome do Fornecedor', max_length=200, blank=True)
    
    # Valores (quando fornecedor = oficina)
    valor_custo = models.DecimalField(
        'Valor de Custo',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    percentual_lucro = models.DecimalField(
        'Percentual de Lucro (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('30.00'),
        help_text='Usado quando fornecedor = oficina'
    )
    valor_venda = models.DecimalField(
        'Valor de Venda',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Calculado automaticamente quando fornecedor = oficina'
    )
    
    # Status e datas
    status = models.CharField(
        'Status',
        max_length=15,
        choices=STATUS_CHOICES,
        default='falta_comprar'
    )
    data_solicitacao = models.DateTimeField('Data da Solicitação', auto_now_add=True)
    data_aprovacao = models.DateTimeField('Data da Aprovação', null=True, blank=True)
    data_pedido = models.DateTimeField('Data do Pedido', null=True, blank=True)
    
    # Prazos
    prazo_compra = models.DateField('Prazo para Compra', null=True, blank=True)
    data_compra = models.DateField('Data Efetiva da Compra', null=True, blank=True)
    prazo_chegada = models.DateField('Prazo para Chegada', null=True, blank=True)
    
    data_recebimento = models.DateTimeField('Data de Recebimento', null=True, blank=True)
    
    # Observações
    observacao = models.TextField('Observação', blank=True)
    
    # Timestamps
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Peça'
        verbose_name_plural = 'Peças'
        ordering = ['-criado_em']
    
    def __str__(self):
        veiculo_str = f" - {self.veiculo.placa}" if self.veiculo else ""
        return f"{self.descricao}{veiculo_str} ({self.get_status_display()})"
    
    @property
    def esta_atrasada(self):
        """Verifica se a peça está com entrega atrasada"""
        if self.data_recebimento or self.status == 'cancelada':
            return False
        if self.prazo_chegada and self.prazo_chegada < timezone.now().date():
            return True
        return False

    @property
    def dias_atraso(self):
        """Calcula quantos dias está atrasada"""
        if self.esta_atrasada:
            delta = timezone.now().date() - self.prazo_chegada
            return delta.days
        return 0
    
    def save(self, *args, **kwargs):
        # Automação de Status
        if self.status != 'cancelada':
            if self.data_recebimento:
                self.status = 'recebida'
            elif self.prazo_chegada and self.prazo_chegada < timezone.now().date():
                self.status = 'atrasada'
            elif self.data_compra:
                self.status = 'comprada'
            else:
                self.status = 'falta_comprar'
        
        # Calcula valor_venda automaticamente se fornecedor = escritorio
        if self.fornecedor_tipo == 'escritorio' and self.valor_custo:
            lucro = self.valor_custo * (self.percentual_lucro / Decimal('100.00'))
            self.valor_venda = self.valor_custo + lucro
        else:
            # Se não for escritorio, zera valores de venda para o financeiro
            self.valor_venda = Decimal('0.00')

        super().save(*args, **kwargs)

        try:
            descricao = (self.descricao or '').strip()
            if descricao:
                CatalogoPeca.objects.get_or_create(
                    descricao=descricao,
                    defaults={
                        'ativo': True,
                        'fornecedor_tipo': self.fornecedor_tipo or 'escritorio',
                        'quantidade': self.quantidade or 1,
                        'valor_custo': self.valor_custo,
                        'percentual_lucro': self.percentual_lucro or Decimal('30.00'),
                    },
                )
        except Exception:
            pass

        # Reflete o atraso da peça no prazo de entrega da Ordem de Serviço
        if self.ordem and self.prazo_chegada:
            if not self.ordem.data_previsao_entrega or self.prazo_chegada > self.ordem.data_previsao_entrega:
                self.ordem.data_previsao_entrega = self.prazo_chegada
                # Adiciona uma observação automática
                obs = f"\n[Sistema] Previsão de entrega estendida para {self.prazo_chegada.strftime('%d/%m/%Y')} devido à peça: {self.descricao}."
                if obs not in self.ordem.observacoes:
                    self.ordem.observacoes += obs
                self.ordem.save()


class CatalogoPeca(models.Model):
    descricao = models.CharField('Descrição', max_length=200, unique=True)
    fornecedor_tipo = models.CharField('Fornecedor padrão', max_length=15, choices=Peca.FORNECEDOR_TIPO_CHOICES, default='escritorio')
    quantidade = models.IntegerField('Quantidade padrão', default=1)
    valor_custo = models.DecimalField('Custo padrão', max_digits=10, decimal_places=2, null=True, blank=True)
    percentual_lucro = models.DecimalField('Lucro padrão (%)', max_digits=5, decimal_places=2, default=Decimal('30.00'))
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Catálogo de Peça'
        verbose_name_plural = 'Catálogo de Peças'
        ordering = ['descricao']

    def __str__(self):
        return self.descricao

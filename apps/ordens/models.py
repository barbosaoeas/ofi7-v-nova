"""
Models para Ordens de Serviço
"""
from django.db import models
from decimal import Decimal


class OrdemServico(models.Model):
    """
    Model de Ordem de Serviço
    Gerada a partir de um orçamento aprovado
    """
    
    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('em_andamento', 'Em Andamento'),
        ('aguardando_peca', 'Aguardando Peça'),
        ('concluida', 'Concluída'),
        ('entregue', 'Entregue'),
        ('cancelada', 'Cancelada'),
    ]
    
    # Relacionamentos
    orcamento = models.OneToOneField(
        'orcamentos.Orcamento',
        on_delete=models.PROTECT,
        related_name='ordem_servico',
        verbose_name='Orçamento'
    )
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='ordens',
        verbose_name='Cliente'
    )
    veiculo = models.ForeignKey(
        'veiculos.Veiculo',
        on_delete=models.PROTECT,
        related_name='ordens',
        verbose_name='Veículo'
    )
    criado_por = models.ForeignKey(
        'funcionarios.Funcionario',
        on_delete=models.PROTECT,
        related_name='ordens_criadas',
        verbose_name='Criado por'
    )
    
    # Dados da OS
    numero = models.CharField('Número', max_length=20, unique=True, editable=False)
    data_abertura = models.DateField('Data de Abertura', auto_now_add=True)
    data_chegada_veiculo = models.DateField('Data de Chegada do Veículo', null=True, blank=True)
    data_previsao_entrega = models.DateField('Previsão de Entrega', null=True, blank=True)
    data_conclusao = models.DateTimeField('Data de Conclusão', null=True, blank=True)
    data_entrega = models.DateTimeField('Data de Entrega', null=True, blank=True)
    
    # Status
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='aberta'
    )
    
    # Observações
    observacoes = models.TextField('Observações', blank=True)
    
    # Timestamps
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Ordem de Serviço'
        verbose_name_plural = 'Ordens de Serviço'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"OS {self.numero} - {self.cliente.nome}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Gera número automático
            ultimo = OrdemServico.objects.order_by('-id').first()
            proximo_numero = 1 if not ultimo else ultimo.id + 1
            self.numero = f"OS-{proximo_numero:06d}"
        super().save(*args, **kwargs)
    
    @property
    def valor_servicos(self):
        """Calcula o valor total apenas dos serviços"""
        return sum(etapa.valor_servico for etapa in self.etapas.all())

    @property
    def valor_pecas(self):
        """Calcula o valor total das peças fornecidas pela oficina"""
        return sum(peca.valor_venda for peca in self.pecas.filter(fornecedor_tipo='escritorio'))

    @property
    def valor_total(self):
        """Calcula o valor total (Serviços + Peças Oficina)"""
        return self.valor_servicos + self.valor_pecas
    
    @property
    def percentual_conclusao(self):
        """Calcula percentual de conclusão baseado nas etapas"""
        total_etapas = self.etapas.count()
        if total_etapas == 0:
            return 0
        concluidas = self.etapas.filter(status='concluido').count()
        return int((concluidas / total_etapas) * 100)


class OrdemEtapa(models.Model):
    """
    Model de Etapa da Ordem de Serviço
    Representa cada etapa do processo de produção
    """
    
    STATUS_CHOICES = [
        ('aguardando', 'Aguardando'),
        ('programado', 'Programado'),
        ('em_andamento', 'Em Andamento'),
        ('finalizada', 'Finalizada'),
        ('aguardando_peca', 'Aguardando Peça'),
    ]
    
    # Relacionamento
    ordem = models.ForeignKey(
        OrdemServico,
        on_delete=models.CASCADE,
        related_name='etapas',
        verbose_name='Ordem de Serviço'
    )
    funcionario = models.ForeignKey(
        'funcionarios.Funcionario',
        on_delete=models.PROTECT,
        related_name='etapas_atribuidas',
        verbose_name='Responsável',
        null=True,
        blank=True
    )
    auxiliares = models.ManyToManyField(
        'funcionarios.Funcionario',
        related_name='etapas_como_auxiliar',
        blank=True,
        verbose_name='Auxiliares'
    )
    
    # Dados da etapa
    nome = models.CharField('Nome da Etapa', max_length=50)
    descricao = models.TextField('Descrição', blank=True)
    sequencia = models.IntegerField(
        'Sequência',
        help_text='Ordem de execução da etapa no processo'
    )
    valor_servico = models.DecimalField('Valor do Serviço', max_digits=10, decimal_places=2)

    EXECUCAO_CHOICES = [
        ('oficina', 'Oficina'),
        ('terceiro', 'Terceiro'),
    ]
    execucao = models.CharField(
        'Execução',
        max_length=10,
        choices=EXECUCAO_CHOICES,
        default='oficina',
    )
    horas_orcadas = models.DecimalField('Horas Orçadas', max_digits=6, decimal_places=2, null=True, blank=True)
    horas_gastas_real = models.DecimalField('Horas Realizadas', max_digits=6, decimal_places=2, null=True, blank=True)

    # Programação
    data_programada = models.DateField('Data Programada', null=True, blank=True)

    # Status e datas
    status = models.CharField(
        'Status',
        max_length=30,
        choices=STATUS_CHOICES,
        default='aguardando'
    )
    data_inicio = models.DateTimeField('Data de Início', null=True, blank=True)
    data_fim = models.DateTimeField('Data de Conclusão', null=True, blank=True)
    permitir_horas_extras = models.BooleanField('Permitir Horas Extras', default=False)

    # Comissão
    percentual_comissao = models.DecimalField(
        'Percentual de Comissão (%)',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Se não definido, usa o percentual padrão do funcionário'
    )

    # Observações
    observacao = models.TextField('Observação', blank=True)

    # Timestamps
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Etapa da Ordem'
        verbose_name_plural = 'Etapas das Ordens'
        ordering = ['ordem', 'sequencia']
        unique_together = [['ordem', 'sequencia']]

    def __str__(self):
        return f"{self.ordem.numero} - {self.nome} ({self.get_status_display()})"

    @property
    def tempo_execucao(self):
        """Calcula tempo de execução em horas"""
        if self.data_inicio and self.data_fim:
            delta = self.data_fim - self.data_inicio
            return delta.total_seconds() / 3600  # retorna em horas
        return None

    @property
    def percentual_comissao_efetivo(self):
        """Retorna o percentual de comissão a ser usado"""
        if self.percentual_comissao:
            return self.percentual_comissao
        if self.funcionario:
            return self.funcionario.percentual_comissao_padrao
        return Decimal('10.00')  # percentual padrão do sistema

    @property
    def valor_comissao_estimado(self):
        """Calcula o valor estimado da comissão"""
        return (self.valor_servico * self.percentual_comissao_efetivo) / 100

    @property
    def pode_iniciar(self):
        """Verifica se a etapa pode ser iniciada"""
        return self.status in ['aguardando', 'programado'] and self.funcionario is not None

    @property
    def pode_concluir(self):
        """Verifica se a etapa pode ser concluída"""
        return self.status == 'em_andamento'


class SessaoTrabalho(models.Model):
    """
    Registra cada bloco de trabalho de um funcionário em uma etapa.
    Uma etapa pode ter múltiplas sessões (pausou no fim do dia e retomou no dia seguinte).
    """
    etapa = models.ForeignKey(
        OrdemEtapa,
        on_delete=models.CASCADE,
        related_name='sessoes',
        verbose_name='Etapa'
    )
    funcionario = models.ForeignKey(
        'funcionarios.Funcionario',
        on_delete=models.PROTECT,
        related_name='sessoes_trabalho',
        verbose_name='Funcionário'
    )
    inicio = models.DateTimeField('Início', auto_now_add=True)
    fim = models.DateTimeField('Fim', null=True, blank=True)
    duracao_minutos = models.DecimalField(
        'Duração (minutos)',
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Sessão de Trabalho'
        verbose_name_plural = 'Sessões de Trabalho'
        ordering = ['-inicio']

    def __str__(self):
        status = 'em aberto' if self.fim is None else f'{self.duracao_minutos:.0f} min'
        return f"{self.funcionario.nome_completo} | {self.etapa.nome} | {status}"

    @property
    def em_aberto(self):
        return self.fim is None

    @staticmethod
    def calcular_minutos_expediente(inicio, fim):
        from datetime import datetime, time, timedelta
        from django.utils import timezone
        from decimal import Decimal

        if not inicio or not fim or fim <= inicio:
            return Decimal('0')

        tz = timezone.get_current_timezone()
        inicio_local = timezone.localtime(inicio, tz)
        fim_local = timezone.localtime(fim, tz)

        inicio_expediente = time(8, 0)
        fim_expediente = time(17, 48)

        total_minutos = 0.0
        dia = inicio_local.date()
        ultimo_dia = fim_local.date()
        while dia <= ultimo_dia:
            janela_inicio = timezone.make_aware(datetime.combine(dia, inicio_expediente), tz)
            janela_fim = timezone.make_aware(datetime.combine(dia, fim_expediente), tz)

            intervalo_inicio = max(inicio_local, janela_inicio)
            intervalo_fim = min(fim_local, janela_fim)
            if intervalo_fim > intervalo_inicio:
                total_minutos += (intervalo_fim - intervalo_inicio).total_seconds() / 60.0

            dia = dia + timedelta(days=1)

        return Decimal(str(round(total_minutos, 2)))

    def minutos_ate_agora(self):
        from django.utils import timezone
        from decimal import Decimal
        if self.fim:
            fim = self.fim
        else:
            fim = timezone.now()
        if getattr(self.etapa, 'permitir_horas_extras', False):
            delta = fim - self.inicio
            return Decimal(str(round(delta.total_seconds() / 60, 2)))
        return self.calcular_minutos_expediente(self.inicio, fim)

    def fechar(self, close_at=None):
        """Fecha a sessão e calcula duração em minutos."""
        from django.utils import timezone
        from decimal import Decimal
        fim = close_at or timezone.now()
        try:
            if timezone.is_naive(fim):
                fim = timezone.make_aware(fim, timezone.get_current_timezone())
        except Exception:
            pass
        if fim < self.inicio:
            fim = self.inicio
        self.fim = fim
        if getattr(self.etapa, 'permitir_horas_extras', False):
            delta = self.fim - self.inicio
            self.duracao_minutos = Decimal(str(round(delta.total_seconds() / 60, 2)))
        else:
            self.duracao_minutos = self.calcular_minutos_expediente(self.inicio, self.fim)
        self.save()
        return self.duracao_minutos

"""
Formulários para Orçamentos
"""
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError

from .models import Orcamento, OrcamentoItem, OrcamentoServicoTerceiro
from apps.clientes.models import Cliente
from apps.veiculos.models import Veiculo


class OrcamentoForm(forms.ModelForm):
    """Formulário principal do Orçamento"""

    DARK_SELECT = (
        'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
        'text-gray-200 text-sm focus:outline-none focus:border-yellow-400/60 '
        'focus:ring-1 focus:ring-yellow-400/20 transition'
    )
    DARK_INPUT = DARK_SELECT
    DARK_TEXTAREA = (
        'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
        'text-gray-200 text-sm placeholder-gray-600 focus:outline-none '
        'focus:border-yellow-400/60 focus:ring-1 focus:ring-yellow-400/20 transition resize-none'
    )

    class Meta:
        model = Orcamento
        fields = ['cliente', 'veiculo', 'status', 'perda_total', 'data_agendada', 'data_prevista_entrega', 'validade', 'desconto', 'observacoes']
        widgets = {
            'cliente': forms.Select(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm focus:outline-none focus:border-yellow-400/60 transition'
                ),
                'id': 'id_cliente',
            }),
            'veiculo': forms.Select(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm focus:outline-none focus:border-yellow-400/60 transition'
                ),
                'id': 'id_veiculo',
            }),
            'status': forms.Select(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm focus:outline-none focus:border-yellow-400/60 transition'
                ),
            }),
            'perda_total': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-yellow-400 bg-white/5 border-white/30 rounded focus:ring-yellow-400/30',
            }),
            'data_agendada': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm focus:outline-none focus:border-yellow-400/60 transition'
                ),
                'type': 'date',
                'hx-get': '/orcamentos/verificar-capacidade-data/',
                'hx-trigger': 'change',
                'hx-target': '#alerta-capacidade',
            }),
            'data_prevista_entrega': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm focus:outline-none focus:border-yellow-400/60 transition'
                ),
                'type': 'date',
            }),
            'validade': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm focus:outline-none focus:border-yellow-400/60 transition'
                ),
                'type': 'date',
            }),
            'desconto': forms.NumberInput(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm focus:outline-none focus:border-yellow-400/60 transition'
                ),
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'observacoes': forms.Textarea(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm placeholder-gray-600 focus:outline-none '
                    'focus:border-yellow-400/60 transition resize-none'
                ),
                'rows': 4,
                'placeholder': 'Condições de pagamento, prazo de execução, garantia...',
            }),
        }


    def __init__(self, *args, **kwargs):
        cliente_id = kwargs.pop('cliente_id', None)
        super().__init__(*args, **kwargs)

        # Labels em português
        self.fields['cliente'].label = 'Cliente'
        self.fields['veiculo'].label = 'Veículo'
        self.fields['status'].label = 'Status do Orçamento'
        self.fields['perda_total'].label = 'Perda total'
        self.fields['data_agendada'].label = 'Agendar entrada'
        self.fields['data_prevista_entrega'].label = 'Previsão de entrega'
        self.fields['validade'].label = 'Válido até'
        self.fields['desconto'].label = 'Desconto (R$)'
        self.fields['observacoes'].label = 'Observações'

        # Filtrar veículos por cliente, se selecionado
        if self.is_bound and self.data.get('cliente'):
            try:
                cid = int(self.data.get('cliente'))
                self.fields['veiculo'].queryset = (
                    Veiculo.objects.filter(cliente_id=cid)
                    .exclude(ordens__status__in=['aberta', 'em_andamento', 'aguardando_peca', 'concluida'])
                    .select_related('modelo_veiculo__fabricante')
                    .distinct()
                )
            except (ValueError, TypeError):
                self.fields['veiculo'].queryset = Veiculo.objects.none()
        elif self.instance.pk and self.instance.cliente_id:
            self.fields['veiculo'].queryset = (
                Veiculo.objects.filter(cliente=self.instance.cliente)
                .exclude(ordens__status__in=['aberta', 'em_andamento', 'aguardando_peca', 'concluida'])
                .select_related('modelo_veiculo__fabricante')
                .distinct()
            )
        elif cliente_id:
            self.fields['veiculo'].queryset = (
                Veiculo.objects.filter(cliente_id=cliente_id)
                .exclude(ordens__status__in=['aberta', 'em_andamento', 'aguardando_peca', 'concluida'])
                .select_related('modelo_veiculo__fabricante')
                .distinct()
            )
        else:
            self.fields['veiculo'].queryset = Veiculo.objects.none()

        # Label customizada para veículo
        self.fields['veiculo'].empty_label = '-- Selecione um veículo --'
        self.fields['cliente'].empty_label = '-- Selecione um cliente --'

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        perda_total = cleaned_data.get('perda_total')
        data_prevista_entrega = cleaned_data.get('data_prevista_entrega')
        if status == 'aprovado' and not perda_total and not data_prevista_entrega:
            raise ValidationError({'data_prevista_entrega': 'Informe a previsão de entrega para aprovar o orçamento.'})
        return cleaned_data


class OrcamentoItemForm(forms.ModelForm):
    """Formulário para um Item do Orçamento"""

    _CLS = (
        'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
        'text-gray-200 text-sm placeholder-gray-600 focus:outline-none '
        'focus:border-yellow-400/60 transition item-valor-input'
    )

    class Meta:
        model = OrcamentoItem
        fields = ['descricao', 'etapa', 'horas_previstas', 'valor', 'retrabalho']
        widgets = {
            'descricao': forms.TextInput(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm placeholder-gray-600 focus:outline-none '
                    'focus:border-yellow-400/60 transition'
                ),
                'placeholder': 'Descrição do serviço...',
            }),
            'etapa': forms.Select(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm focus:outline-none '
                    'focus:border-yellow-400/60 transition etapa-select'
                ),
            }),
            'horas_previstas': forms.NumberInput(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm focus:outline-none '
                    'focus:border-yellow-400/60 transition'
                ),
                'placeholder': 'Horas (Ex: 1.5)',
                'step': '0.1',
                'min': '0',
            }),
            'valor': forms.NumberInput(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm text-right focus:outline-none '
                    'focus:border-yellow-400/60 transition item-valor-input'
                ),
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'retrabalho': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-red-400 bg-white/5 border-white/30 rounded focus:ring-red-400/30 item-retrabalho',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descricao'].label = 'Descrição do Serviço'
        self.fields['etapa'].label = 'Etapa'
        self.fields['valor'].label = 'Valor (R$)'
        self.fields['retrabalho'].label = 'Retrabalho'
        self.fields['etapa'].empty_label = 'Selecione a Etapa'


# FormSet de itens — permite criar/editar múltiplos itens na mesma tela
OrcamentoItemFormSet = inlineformset_factory(
    Orcamento,
    OrcamentoItem,
    form=OrcamentoItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class OrcamentoServicoTerceiroForm(forms.ModelForm):
    """Formulário para itens de serviços terceirizados"""

    class Meta:
        model = OrcamentoServicoTerceiro
        fields = ['descricao', 'fornecedor', 'valor']
        widgets = {
            'descricao': forms.TextInput(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm placeholder-gray-600 focus:outline-none '
                    'focus:border-yellow-400/60 transition'
                ),
                'placeholder': 'Descrição (Opcional)',
            }),
            'fornecedor': forms.Select(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm focus:outline-none '
                    'focus:border-yellow-400/60 transition fornecedor-select'
                ),
            }),
            'valor': forms.NumberInput(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm text-right focus:outline-none '
                    'focus:border-yellow-400/60 transition item-terceiro-valor'
                ),
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fornecedor'].empty_label = 'Selecione o Fornecedor'


OrcamentoTerceiroFormSet = inlineformset_factory(
    Orcamento,
    OrcamentoServicoTerceiro,
    form=OrcamentoServicoTerceiroForm,
    extra=0,
    can_delete=True
)

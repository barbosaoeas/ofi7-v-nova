"""
Formulários para Orçamentos
"""
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError

from .models import Orcamento, OrcamentoItem, OrcamentoServicoTerceiro, OrcamentoAditivo
from apps.clientes.models import Cliente
from apps.veiculos.models import Veiculo
from apps.pecas.models import Peca
from apps.pecas.models import CatalogoPeca


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
        fields = ['cliente', 'veiculo', 'status', 'perda_total', 'data_agendada', 'data_prevista_entrega', 'validade', 'inativo', 'desconto', 'observacoes']
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
            'inativo': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-yellow-400 bg-white/5 border-white/30 rounded focus:ring-yellow-400/30',
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
        self.fields['inativo'].label = 'Inativo'
        self.fields['desconto'].label = 'Desconto (R$)'
        self.fields['observacoes'].label = 'Observações'

        if self.instance and getattr(self.instance, 'status', None) == 'entregue':
            self.fields['inativo'].disabled = True

        veiculo_atual_id = None
        if self.instance.pk and self.instance.veiculo_id:
            veiculo_atual_id = self.instance.veiculo_id
        elif self.is_bound and self.data.get('veiculo'):
            try:
                veiculo_atual_id = int(self.data.get('veiculo'))
            except (TypeError, ValueError):
                veiculo_atual_id = None

        def _queryset_veiculos_cliente(cid):
            base = Veiculo.objects.filter(cliente_id=cid).select_related('modelo_veiculo__fabricante').distinct()
            disponiveis = base.exclude(ordens__status__in=['aberta', 'em_andamento', 'aguardando_peca'])
            if veiculo_atual_id:
                return (disponiveis | base.filter(pk=veiculo_atual_id)).distinct()
            return disponiveis

        # Filtrar veículos por cliente, se selecionado
        if self.is_bound and self.data.get('cliente'):
            try:
                cid = int(self.data.get('cliente'))
                self.fields['veiculo'].queryset = _queryset_veiculos_cliente(cid)
            except (ValueError, TypeError):
                self.fields['veiculo'].queryset = Veiculo.objects.none()
        elif self.instance.pk and self.instance.cliente_id:
            self.fields['veiculo'].queryset = _queryset_veiculos_cliente(self.instance.cliente_id)
        elif cliente_id:
            self.fields['veiculo'].queryset = _queryset_veiculos_cliente(cliente_id)
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
    extra=0,
    can_delete=True,
    min_num=0,
    validate_min=False,
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


class OrcamentoPecaForm(forms.ModelForm):
    catalogo = forms.ModelChoiceField(
        queryset=CatalogoPeca.objects.filter(ativo=True).order_by('descricao'),
        required=False,
        empty_label='Selecione a peça...',
        widget=forms.Select(attrs={
            'class': (
                'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                'text-gray-200 text-sm focus:outline-none '
                'focus:border-yellow-400/60 transition item-peca-catalogo'
            ),
        }),
    )

    class Meta:
        model = Peca
        fields = [
            'descricao',
            'fornecedor_tipo',
            'quantidade',
            'valor_custo',
            'percentual_lucro',
            'valor_venda',
        ]
        widgets = {
            'descricao': forms.HiddenInput(attrs={
                'class': 'item-peca-descricao'
            }),
            'fornecedor_tipo': forms.Select(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm focus:outline-none '
                    'focus:border-yellow-400/60 transition item-peca-tipo'
                ),
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm text-center focus:outline-none '
                    'focus:border-yellow-400/60 transition item-peca-qtd'
                ),
                'min': '1',
                'step': '1',
            }),
            'valor_custo': forms.NumberInput(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm text-right focus:outline-none '
                    'focus:border-yellow-400/60 transition item-peca-custo'
                ),
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'percentual_lucro': forms.HiddenInput(attrs={
                'class': 'item-peca-lucro',
            }),
            'valor_venda': forms.NumberInput(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm text-right focus:outline-none '
                    'focus:border-yellow-400/60 transition item-peca-venda'
                ),
                'placeholder': '0.00',
                'step': '0.01',
                'readonly': 'readonly',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descricao'].required = False
        self.fields['fornecedor_tipo'].required = False
        self.fields['quantidade'].required = False
        self.fields['valor_custo'].required = False
        self.fields['percentual_lucro'].required = False
        try:
            if self.instance and getattr(self.instance, 'descricao', None):
                descricao = (self.instance.descricao or '').strip()
                item = (
                    CatalogoPeca.objects.filter(descricao=descricao).first()
                    or CatalogoPeca.objects.filter(descricao__iexact=descricao).first()
                )
                if item:
                    self.fields['catalogo'].initial = item
                    if not getattr(self.instance, 'fornecedor_tipo', None):
                        self.fields['fornecedor_tipo'].initial = item.fornecedor_tipo
                    if not getattr(self.instance, 'quantidade', None):
                        self.fields['quantidade'].initial = item.quantidade
                    if getattr(self.instance, 'valor_custo', None) in [None, '']:
                        self.fields['valor_custo'].initial = item.valor_custo
                    if getattr(self.instance, 'percentual_lucro', None) in [None, '']:
                        self.fields['percentual_lucro'].initial = item.percentual_lucro
        except Exception:
            pass
        self.fields['descricao'].label = 'Peça'
        self.fields['fornecedor_tipo'].label = 'Fornecedor'
        self.fields['quantidade'].label = 'Qtd'
        self.fields['valor_custo'].label = 'Custo'
        self.fields['percentual_lucro'].label = 'Lucro (%)'
        self.fields['valor_venda'].label = 'Venda'
        self.fields['catalogo'].label = 'Peça'

    def clean(self):
        cleaned = super().clean()
        if not self.has_changed() and not (self.instance and self.instance.pk):
            return cleaned

        catalogo = cleaned.get('catalogo')
        if catalogo:
            cleaned['descricao'] = catalogo.descricao
            if not cleaned.get('fornecedor_tipo'):
                cleaned['fornecedor_tipo'] = catalogo.fornecedor_tipo
            if not cleaned.get('quantidade'):
                cleaned['quantidade'] = catalogo.quantidade
            if cleaned.get('valor_custo') in [None, '']:
                cleaned['valor_custo'] = catalogo.valor_custo
            if cleaned.get('percentual_lucro') in [None, '']:
                cleaned['percentual_lucro'] = catalogo.percentual_lucro
            return cleaned
        if self.instance and self.instance.pk and getattr(self.instance, 'descricao', None):
            cleaned['descricao'] = self.instance.descricao
            return cleaned
        raise ValidationError({'catalogo': 'Selecione a peça.'})


OrcamentoPecaFormSet = inlineformset_factory(
    Orcamento,
    Peca,
    form=OrcamentoPecaForm,
    fk_name='orcamento',
    extra=0,
    can_delete=True,
)


OrcamentoTerceiroFormSet = inlineformset_factory(
    Orcamento,
    OrcamentoServicoTerceiro,
    form=OrcamentoServicoTerceiroForm,
    extra=0,
    can_delete=True
)


class OrcamentoAditivoForm(forms.ModelForm):
    class Meta:
        model = OrcamentoAditivo
        fields = ['status', 'observacoes']
        widgets = {
            'status': forms.Select(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm focus:outline-none focus:border-yellow-400/60 transition'
                ),
            }),
            'observacoes': forms.Textarea(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm placeholder-gray-600 focus:outline-none '
                    'focus:border-yellow-400/60 transition resize-none'
                ),
                'rows': 3,
                'placeholder': 'Motivo do acréscimo / observações para o cliente...',
            }),
        }


class AditivoPecaForm(forms.ModelForm):
    catalogo = forms.ModelChoiceField(
        queryset=CatalogoPeca.objects.filter(ativo=True).order_by('descricao'),
        required=False,
        empty_label='Selecione a peça...',
        widget=forms.Select(attrs={
            'class': (
                'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                'text-gray-200 text-sm focus:outline-none '
                'focus:border-yellow-400/60 transition item-peca-catalogo'
            ),
        }),
    )

    class Meta:
        model = Peca
        fields = [
            'descricao',
            'fornecedor_tipo',
            'quantidade',
            'valor_custo',
            'percentual_lucro',
            'valor_venda',
            'prazo_chegada',
        ]
        widgets = {
            'descricao': forms.HiddenInput(attrs={'class': 'item-peca-descricao'}),
            'fornecedor_tipo': forms.Select(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm focus:outline-none '
                    'focus:border-yellow-400/60 transition item-peca-tipo'
                ),
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm text-center focus:outline-none '
                    'focus:border-yellow-400/60 transition item-peca-qtd'
                ),
                'min': '1',
                'step': '1',
            }),
            'valor_custo': forms.NumberInput(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm text-right focus:outline-none '
                    'focus:border-yellow-400/60 transition item-peca-custo'
                ),
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'percentual_lucro': forms.HiddenInput(attrs={'class': 'item-peca-lucro'}),
            'valor_venda': forms.NumberInput(attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm text-right focus:outline-none '
                    'focus:border-yellow-400/60 transition item-peca-venda'
                ),
                'placeholder': '0.00',
                'step': '0.01',
                'readonly': 'readonly',
            }),
            'prazo_chegada': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': (
                    'w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 '
                    'text-gray-200 text-sm focus:outline-none focus:border-yellow-400/60 transition'
                ),
                'type': 'date',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descricao'].required = False
        self.fields['fornecedor_tipo'].required = False
        self.fields['quantidade'].required = False
        self.fields['valor_custo'].required = False
        self.fields['percentual_lucro'].required = False
        try:
            if self.instance and getattr(self.instance, 'descricao', None):
                item = CatalogoPeca.objects.filter(descricao=self.instance.descricao).first()
                if item:
                    self.fields['catalogo'].initial = item
        except Exception:
            pass

    def clean(self):
        cleaned = super().clean()
        if not self.has_changed() and not (self.instance and self.instance.pk):
            return cleaned

        catalogo = cleaned.get('catalogo')
        if catalogo:
            cleaned['descricao'] = catalogo.descricao
            if not cleaned.get('fornecedor_tipo'):
                cleaned['fornecedor_tipo'] = catalogo.fornecedor_tipo
            if not cleaned.get('quantidade'):
                cleaned['quantidade'] = catalogo.quantidade
            if cleaned.get('valor_custo') in [None, '']:
                cleaned['valor_custo'] = catalogo.valor_custo
            if cleaned.get('percentual_lucro') in [None, '']:
                cleaned['percentual_lucro'] = catalogo.percentual_lucro
            return cleaned

        if self.instance and self.instance.pk and getattr(self.instance, 'descricao', None):
            cleaned['descricao'] = self.instance.descricao
            return cleaned

        raise ValidationError({'catalogo': 'Selecione a peça.'})


AditivoPecaFormSet = inlineformset_factory(
    OrcamentoAditivo,
    Peca,
    form=AditivoPecaForm,
    fk_name='aditivo',
    extra=0,
    can_delete=True,
)

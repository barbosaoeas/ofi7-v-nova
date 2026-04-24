"""
Formulários para Peças
"""
from django import forms
from .models import Peca
from apps.clientes.models import Cliente
from apps.orcamentos.models import Orcamento
from apps.ordens.models import OrdemServico
from apps.veiculos.models import Veiculo


class PecaForm(forms.ModelForm):
    """Formulário para Cadastro de Peça"""

    def __init__(self, *args, **kwargs):
        cliente_id = kwargs.pop('cliente_id', None)
        super().__init__(*args, **kwargs)
        veiculos = Veiculo.objects.all()

        orcamento_id = None
        ordem_id = None
        try:
            orcamento_id = self.initial.get('orcamento') or getattr(self.instance, 'orcamento_id', None)
        except Exception:
            orcamento_id = getattr(self.instance, 'orcamento_id', None)
        try:
            ordem_id = self.initial.get('ordem') or getattr(self.instance, 'ordem_id', None)
        except Exception:
            ordem_id = getattr(self.instance, 'ordem_id', None)

        if not cliente_id and orcamento_id:
            try:
                cliente_id = Orcamento.objects.filter(id=orcamento_id).values_list('cliente_id', flat=True).first()
            except Exception:
                cliente_id = None
        if not cliente_id and ordem_id:
            try:
                cliente_id = (
                    OrdemServico.objects.filter(id=ordem_id)
                    .values_list('veiculo__cliente_id', flat=True)
                    .first()
                )
            except Exception:
                cliente_id = None
        if not cliente_id and getattr(self.instance, 'veiculo_id', None):
            try:
                cliente_id = Veiculo.objects.filter(id=self.instance.veiculo_id).values_list('cliente_id', flat=True).first()
            except Exception:
                cliente_id = None

        if cliente_id:
            veiculos = veiculos.filter(cliente_id=cliente_id)
        if self.instance and getattr(self.instance, 'veiculo_id', None):
            veiculos = veiculos | Veiculo.objects.filter(id=self.instance.veiculo_id)
        self.fields['veiculo'].queryset = veiculos.distinct().order_by('placa')

        fornecedores = Cliente.objects.filter(ativo=True)
        if self.instance and getattr(self.instance, 'fornecedor_id', None):
            fornecedores = fornecedores | Cliente.objects.filter(id=self.instance.fornecedor_id)
        self.fields['fornecedor'].queryset = fornecedores.distinct().order_by('nome')
        orcamentos_ativos = Orcamento.objects.exclude(status__in=['entregue', 'rejeitado', 'cancelado'])
        ordens_ativas = OrdemServico.objects.exclude(status__in=['concluida', 'entregue', 'cancelada'])

        if self.instance and getattr(self.instance, 'orcamento_id', None):
            orcamentos_ativos = orcamentos_ativos | Orcamento.objects.filter(id=self.instance.orcamento_id)
        if self.instance and getattr(self.instance, 'ordem_id', None):
            ordens_ativas = ordens_ativas | OrdemServico.objects.filter(id=self.instance.ordem_id)

        self.fields['orcamento'].queryset = orcamentos_ativos.distinct().order_by('-id')
        self.fields['ordem'].queryset = ordens_ativas.distinct().order_by('-id')

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not getattr(instance, 'veiculo_id', None):
            ordem = getattr(instance, 'ordem', None)
            if ordem and getattr(ordem, 'veiculo_id', None):
                instance.veiculo_id = ordem.veiculo_id
            else:
                orcamento = getattr(instance, 'orcamento', None)
                if orcamento and getattr(orcamento, 'veiculo_id', None):
                    instance.veiculo_id = orcamento.veiculo_id
        if commit:
            instance.save()
            self.save_m2m()
        return instance

    def clean_orcamento(self):
        orcamento = self.cleaned_data.get('orcamento')
        if not orcamento:
            return orcamento
        if orcamento.status in ['entregue', 'rejeitado', 'cancelado']:
            raise forms.ValidationError('Orçamento encerrado. Selecione um orçamento ativo.')
        return orcamento

    def clean_ordem(self):
        ordem = self.cleaned_data.get('ordem')
        if not ordem:
            return ordem
        if ordem.status in ['concluida', 'entregue', 'cancelada']:
            raise forms.ValidationError('OS encerrada. Selecione uma OS ativa.')
        return ordem

    class Meta:
        model = Peca
        fields = [
            'veiculo', 'orcamento', 'ordem', 'descricao', 'quantidade', 'fornecedor_tipo', 
            'fornecedor', 'fornecedor_nome', 'valor_custo', 'percentual_lucro', 'valor_venda',
            'prazo_compra', 'data_compra', 'prazo_chegada', 'observacao'
        ]
        widgets = {
            'veiculo': forms.Select(attrs={'class': 'form-select'}),
            'orcamento': forms.Select(attrs={'class': 'form-select'}),
            'ordem': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Parachoque Dianteiro'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-input', 'min': '1'}),
            'fornecedor_tipo': forms.Select(attrs={
                'class': 'form-select',
                'x-model': 'fornecedor_tipo'
            }),
            'fornecedor': forms.Select(attrs={
                'class': 'form-select',
                'x-model': 'fornecedor_id',
                '@change': 'atualizarNomeFornecedor($event)'
            }),
            'fornecedor_nome': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'Nome do fornecedor manual',
                'x-model': 'fornecedor_nome'
            }),
            'valor_custo': forms.NumberInput(attrs={
                'class': 'form-input', 
                'step': '0.01', 
                'x-model.number': 'valor_custo'
            }),
            'percentual_lucro': forms.NumberInput(attrs={
                'class': 'form-input', 
                'step': '0.01', 
                'x-model.number': 'percentual_lucro'
            }),
            'valor_venda': forms.NumberInput(attrs={
                'class': 'form-input bg-gray-100 font-bold', 
                'step': '0.01', 
                'readonly': 'readonly', 
                'x-model': 'valor_venda'
            }),
            'prazo_compra': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-input', 'type': 'date'}),
            'data_compra': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-input', 'type': 'date'}),
            'prazo_chegada': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-input', 'type': 'date'}),
            'observacao': forms.Textarea(attrs={'class': 'form-input', 'rows': '3'}),
        }

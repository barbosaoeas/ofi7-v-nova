"""
Formulários para Peças
"""
from django import forms
from .models import Peca
from apps.clientes.models import Cliente
from apps.orcamentos.models import Orcamento
from apps.ordens.models import OrdemServico


class PecaForm(forms.ModelForm):
    """Formulário para Cadastro de Peça"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

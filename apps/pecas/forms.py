"""
Formulários para Peças
"""
from django import forms
from .models import Peca
from apps.clientes.models import Cliente


class PecaForm(forms.ModelForm):
    """Formulário para Cadastro de Peça"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra fornecedores para mostrar apenas quem tem categoria Fornecedor ou Ambos
        self.fields['fornecedor'].queryset = Cliente.objects.filter(
            categoria__in=['fornecedor', 'ambos'],
            ativo=True
        )

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
            'prazo_compra': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'data_compra': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'prazo_chegada': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'observacao': forms.Textarea(attrs={'class': 'form-input', 'rows': '3'}),
        }

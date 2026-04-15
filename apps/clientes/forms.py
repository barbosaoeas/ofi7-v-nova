"""
Formulários para Clientes
"""
from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    """Formulário para cadastro/edição de Cliente"""
    
    class Meta:
        model = Cliente
        fields = [
            'tipo', 'categoria', 'nome', 'cpf_cnpj', 'rg_ie',
            'telefone', 'email',
            'cep', 'endereco', 'numero', 'complemento',
            'estado', 'observacoes', 'ativo', 'atividade_fornecedor'
        ]
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select', 'x-model': 'categoria'}),
            'nome': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nome completo'}),
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'CPF ou CNPJ'}),
            'rg_ie': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'RG ou IE'}),
            'telefone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '(11) 1234-5678'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'email@exemplo.com'}),
            'cep': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '00000-000'}),
            'endereco': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Rua, Avenida...'}),
            'numero': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '123'}),
            'complemento': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Apto, Bloco...'}),
            'bairro': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Bairro'}),
            'cidade': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Cidade'}),
            'estado': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'SP', 'maxlength': '2'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Observações...'}),
            'atividade_fornecedor': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Material de Pintura, Mecânica, etc.', 'autocomplete': 'off'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

"""
Formulários para Veículos
"""
import re
from django import forms
from .models import Veiculo
from .models_fabricantes import Fabricante, ModeloVeiculo, CorVeiculo


class CorVeiculoForm(forms.ModelForm):
    """Formulário para Cor de Veículo"""

    class Meta:
        model = CorVeiculo
        fields = ['nome', 'codigo_hex', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Branco'}),
            'codigo_hex': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '#FFFFFF'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean_nome(self):
        """Capitaliza o nome da cor"""
        nome = self.cleaned_data.get('nome')
        return nome.title() if nome else nome


class FabricanteForm(forms.ModelForm):
    """Formulário para Fabricante"""
    
    class Meta:
        model = Fabricante
        fields = ['nome', 'pais_origem', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Toyota'}),
            'pais_origem': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Japão'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class ModeloVeiculoForm(forms.ModelForm):
    """Formulário para Modelo de Veículo"""
    
    class Meta:
        model = ModeloVeiculo
        fields = ['fabricante', 'nome', 'categoria', 'ativo']
        widgets = {
            'fabricante': forms.Select(attrs={'class': 'form-select'}),
            'nome': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Corolla'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class VeiculoForm(forms.ModelForm):
    """Formulário para Veículo"""

    class Meta:
        model = Veiculo
        fields = [
            'cliente', 'modelo_veiculo', 'cor_veiculo', 'placa',
            'ano_fabricacao', 'ano_modelo',
            'chassi', 'renavam', 'km_atual',
            'foto_principal', 'foto_2', 'foto_3', 'foto_4',
            'observacoes'
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'modelo_veiculo': forms.Select(attrs={'class': 'form-select'}),
            'cor_veiculo': forms.Select(attrs={'class': 'form-select'}),
            'placa': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'ABC1234', 
                'style': 'text-transform: uppercase;',
                'maxlength': '7',
                'minlength': '7'
            }),
            'ano_fabricacao': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '2020'}),
            'ano_modelo': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '2021'}),
            'chassi': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '9BWZZZ377VT004251', 'style': 'text-transform: uppercase;'}),
            'renavam': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '00123456789'}),
            'km_atual': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '15000'}),
            'foto_principal': forms.ClearableFileInput(attrs={'class': 'form-file', 'accept': 'image/*', 'capture': 'environment'}),
            'foto_2': forms.ClearableFileInput(attrs={'class': 'form-file', 'accept': 'image/*', 'capture': 'environment'}),
            'foto_3': forms.ClearableFileInput(attrs={'class': 'form-file', 'accept': 'image/*', 'capture': 'environment'}),
            'foto_4': forms.ClearableFileInput(attrs={'class': 'form-file', 'accept': 'image/*', 'capture': 'environment'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Observações...'}),
        }

    def clean_placa(self):
        """Valida e formata a placa no padrão brasileiro (7 caracteres)"""
        placa = self.cleaned_data.get('placa', '')
        
        # Remove hífens e espaços
        placa = re.sub(r'[^A-Za-z0-9]', '', placa).upper()
        
        # Verifica se tem exatamente 7 caracteres
        if len(placa) != 7:
            raise forms.ValidationError("A placa deve ter exatamente 7 caracteres (Ex: ABC1234 ou ABC1D23).")
        
        # Regex flexível para 7 caracteres alfanuméricos
        padrao_placa = re.compile(r'^[A-Z0-9]{7}$')
        if not padrao_placa.match(placa):
            raise forms.ValidationError("A placa deve conter apenas letras e números (7 caracteres).")
            
        return placa

    def clean_chassi(self):
        """Converte chassi para MAIÚSCULA"""
        chassi = self.cleaned_data.get('chassi')
        return chassi.upper() if chassi else chassi

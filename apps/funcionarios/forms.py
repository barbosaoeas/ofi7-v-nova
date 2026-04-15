"""
Formulários para Funcionários
"""
from django import forms
from .models import Funcionario


class FuncionarioForm(forms.ModelForm):
    """Formulário para Cadastro de Funcionário"""
    
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Senha para acesso'}),
        required=False,
        help_text='Deixe em branco para manter a senha atual em caso de edição.'
    )

    class Meta:
        model = Funcionario
        fields = [
            'username', 'first_name', 'last_name', 'email', 
            'telefone', 'cpf', 'perfil', 'percentual_comissao_padrao', 
            'data_admissao', 'ativo', 'foto'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nome de usuário'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Sobrenome'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'email@exemplo.com'}),
            'telefone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '(00) 00000-0000'}),
            'cpf': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '000.000.000-00'}),
            'perfil': forms.Select(attrs={'class': 'form-select'}),
            'percentual_comissao_padrao': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'data_admissao': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        return username.capitalize() if username else username

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        return first_name.capitalize() if first_name else first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        return last_name.capitalize() if last_name else last_name

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

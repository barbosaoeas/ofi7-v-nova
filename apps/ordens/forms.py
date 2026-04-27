from django import forms
from django.forms import inlineformset_factory
from .models import OrdemServico, OrdemEtapa

class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ['status', 'data_chegada_veiculo', 'data_previsao_entrega', 'observacoes']
        widgets = {
            'status': forms.Select(attrs={'class': 'w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900 font-medium'}),
            'data_chegada_veiculo': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900 font-medium'}),
            'data_previsao_entrega': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900 font-medium'}),
            'observacoes': forms.Textarea(attrs={'class': 'w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900', 'rows': 2}),
        }

class OrdemEtapaForm(forms.ModelForm):
    class Meta:
        model = OrdemEtapa
        fields = ['funcionario', 'auxiliares', 'data_programada', 'pular_etapa', 'horas_gastas_real', 'status']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'w-full bg-white border border-gray-300 rounded-lg px-2 py-1.5 text-sm text-gray-900'}),
            'auxiliares': forms.SelectMultiple(attrs={'class': 'tom-select-multiple w-full text-sm', 'data-placeholder': 'Selecione...'}),
            'data_programada': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full bg-white border border-gray-300 rounded-lg px-2 py-1.5 text-sm text-gray-900'}),
            'pular_etapa': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded'}),
            'horas_gastas_real': forms.NumberInput(attrs={'class': 'w-full bg-white border border-gray-300 rounded-lg px-2 py-1.5 text-sm text-gray-900 font-mono', 'step': '0.1'}),
            'status': forms.Select(attrs={'class': 'w-full bg-white border border-gray-300 rounded-lg px-2 py-1.5 text-sm text-gray-900 font-medium'}),
        }

OrdemEtapaFormSet = inlineformset_factory(
    OrdemServico,
    OrdemEtapa,
    form=OrdemEtapaForm,
    extra=0,
    can_delete=False
)

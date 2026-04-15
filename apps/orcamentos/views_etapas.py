"""
Views CRUD para Etapas Padrão
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms

from .models import EtapaPadrao


class EtapaPadraoForm(forms.ModelForm):
    class Meta:
        model = EtapaPadrao
        fields = ['nome', 'descricao', 'ordem_default', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Pintura'}),
            'descricao': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Descrição...'}),
            'ordem_default': forms.NumberInput(attrs={'class': 'form-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


@login_required
def etapa_list(request):
    etapas = EtapaPadrao.objects.all().order_by('ordem_default', 'nome')
    return render(request, 'orcamentos/etapas_list.html', {'etapas': etapas})


@login_required
def etapa_create(request):
    if request.method == 'POST':
        form = EtapaPadraoForm(request.POST)
        if form.is_valid():
            etapa = form.save()
            messages.success(request, f'Etapa {etapa.nome} criada com sucesso!')
            return redirect('orcamentos:etapa_list')
    else:
        # Pre-selecionar próxima ordem
        ultima = EtapaPadrao.objects.order_by('-ordem_default').first()
        ordem = (ultima.ordem_default + 10) if ultima else 10
        form = EtapaPadraoForm(initial={'ordem_default': ordem})
        
    return render(request, 'orcamentos/etapas_form.html', {'form': form, 'titulo': 'Nova Etapa Padrão'})


@login_required
def etapa_update(request, pk):
    etapa = get_object_or_404(EtapaPadrao, pk=pk)
    if request.method == 'POST':
        form = EtapaPadraoForm(request.POST, instance=etapa)
        if form.is_valid():
            form.save()
            messages.success(request, f'Etapa {etapa.nome} atualizada com sucesso!')
            return redirect('orcamentos:etapa_list')
    else:
        form = EtapaPadraoForm(instance=etapa)
        
    return render(request, 'orcamentos/etapas_form.html', {'form': form, 'titulo': f'Editar Etapa {etapa.nome}'})


@login_required
def etapa_delete(request, pk):
    etapa = get_object_or_404(EtapaPadrao, pk=pk)
    if request.method == 'POST':
        try:
            nome = etapa.nome
            etapa.delete()
            messages.success(request, f'Etapa {nome} excluída com sucesso!')
        except Exception as e:
            messages.error(request, 'Não é possível excluir esta etapa pois ela já foi utilizada em orçamentos.')
        return redirect('orcamentos:etapa_list')
    return render(request, 'orcamentos/etapas_confirm_delete.html', {'etapa': etapa})

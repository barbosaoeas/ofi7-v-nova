"""
Views CRUD para Funcionários (Frontend Web)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Funcionario
from .forms import FuncionarioForm


@login_required
def funcionario_list(request):
    """Lista de funcionários com busca e filtros"""
    
    # Busca
    query = request.GET.get('q', '')
    perfil_filter = request.GET.get('perfil', '')
    ativo_filter = request.GET.get('ativo', '')
    
    # QuerySet base
    funcionarios = Funcionario.objects.all().order_by('first_name', 'last_name')
    
    # Aplicar busca
    if query:
        funcionarios = funcionarios.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(cpf__icontains=query) |
            Q(email__icontains=query)
        )
    
    # Aplicar filtros
    if perfil_filter:
        funcionarios = funcionarios.filter(perfil=perfil_filter)
    
    if ativo_filter:
        funcionarios = funcionarios.filter(ativo=ativo_filter == 'true')
    
    # Paginação
    paginator = Paginator(funcionarios, 20)
    page = request.GET.get('page', 1)
    funcionarios_page = paginator.get_page(page)
    
    context = {
        'funcionarios': funcionarios_page,
        'query': query,
        'perfil_filter': perfil_filter,
        'ativo_filter': ativo_filter,
        'perfil_choices': Funcionario.PERFIL_CHOICES
    }
    
    return render(request, 'funcionarios/funcionario_list.html', context)


@login_required
def funcionario_create(request):
    """Criar novo funcionário"""
    
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, request.FILES)
        if form.is_valid():
            funcionario = form.save()
            messages.success(request, f'Funcionário "{funcionario.nome_completo}" cadastrado com sucesso!')
            return redirect('funcionarios:list')
    else:
        form = FuncionarioForm()
    
    context = {'form': form, 'title': 'Novo Funcionário'}
    return render(request, 'funcionarios/funcionario_form.html', context)


@login_required
def funcionario_update(request, pk):
    """Editar funcionário"""
    
    funcionario = get_object_or_404(Funcionario, pk=pk)
    
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, request.FILES, instance=funcionario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Funcionário "{funcionario.nome_completo}" atualizado com sucesso!')
            return redirect('funcionarios:list')
    else:
        form = FuncionarioForm(instance=funcionario)
    
    context = {'form': form, 'title': f'Editar Funcionário: {funcionario.nome_completo}', 'funcionario': funcionario}
    return render(request, 'funcionarios/funcionario_form.html', context)


@login_required
def funcionario_delete(request, pk):
    """Deletar funcionário"""
    
    funcionario = get_object_or_404(Funcionario, pk=pk)
    
    if request.method == 'POST':
        nome = funcionario.nome_completo
        funcionario.delete()
        messages.success(request, f'Funcionário "{nome}" removido com sucesso!')
        return redirect('funcionarios:list')
    
    context = {'funcionario': funcionario}
    return render(request, 'funcionarios/funcionario_confirm_delete.html', context)


@login_required
def funcionario_reset_password(request, pk):
    """Reseta a senha do funcionário para o padrão 123456"""
    
    # Apenas admin e gerente podem resetar senhas
    if request.user.perfil not in ['admin', 'gerente']:
        messages.error(request, 'Você não tem permissão para realizar esta ação.')
        return redirect('funcionarios:list')
        
    funcionario = get_object_or_404(Funcionario, pk=pk)
    
    if request.method == 'POST':
        funcionario.set_password('123456')
        funcionario.save()
        messages.success(request, f'Senha do funcionário "{funcionario.nome_completo}" resetada para "123456" com sucesso!')
        return redirect('funcionarios:list')
    
    context = {'funcionario': funcionario}
    return render(request, 'funcionarios/funcionario_confirm_reset_password.html', context)

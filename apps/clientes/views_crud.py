"""
Views CRUD para Clientes (Frontend Web)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Cliente
from .forms import ClienteForm


@login_required
def cliente_list(request):
    """Lista de clientes com busca e filtros"""
    
    # Busca
    query = request.GET.get('q', '')
    tipo_filter = request.GET.get('tipo', '')
    categoria_filter = request.GET.get('categoria', '')
    ativo_filter = request.GET.get('ativo', '')
    
    # QuerySet base
    clientes = Cliente.objects.all().order_by('-criado_em')
    
    # Aplicar busca
    if query:
        clientes = clientes.filter(
            Q(nome__icontains=query) |
            Q(cpf_cnpj__icontains=query) |
            Q(telefone__icontains=query) |
            Q(email__icontains=query)
        )
    
    # Aplicar filtros
    if tipo_filter:
        clientes = clientes.filter(tipo=tipo_filter)
    
    if categoria_filter:
        clientes = clientes.filter(categoria=categoria_filter)
    
    if ativo_filter:
        clientes = clientes.filter(ativo=ativo_filter == 'true')
    
    # Paginação
    paginator = Paginator(clientes, 20)
    page = request.GET.get('page', 1)
    clientes_page = paginator.get_page(page)
    
    context = {
        'clientes': clientes_page,
        'query': query,
        'tipo_filter': tipo_filter,
        'categoria_filter': categoria_filter,
        'ativo_filter': ativo_filter,
    }
    
    return render(request, 'clientes/cliente_list.html', context)


@login_required
def cliente_create(request):
    """Criar novo cliente"""
    
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nome}" cadastrado com sucesso!')
            return redirect('clientes:list')
    else:
        form = ClienteForm()
    
    context = {'form': form, 'title': 'Novo Cliente'}
    return render(request, 'clientes/cliente_form.html', context)


@login_required
def cliente_update(request, pk):
    """Editar cliente"""
    
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cliente "{cliente.nome}" atualizado com sucesso!')
            return redirect('clientes:list')
    else:
        form = ClienteForm(instance=cliente)
    
    context = {'form': form, 'title': f'Editar Cliente: {cliente.nome}', 'cliente': cliente}
    return render(request, 'clientes/cliente_form.html', context)


@login_required
def cliente_delete(request, pk):
    """Deletar cliente"""
    
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        nome = cliente.nome
        cliente.delete()
        messages.success(request, f'Cliente "{nome}" removido com sucesso!')
        return redirect('clientes:list')
    
    context = {'cliente': cliente}
    return render(request, 'clientes/cliente_confirm_delete.html', context)


@login_required
def cliente_detail(request, pk):
    """Detalhes do cliente"""
    
    cliente = get_object_or_404(Cliente, pk=pk)
    veiculos = cliente.veiculos.all()
    
    context = {
        'cliente': cliente,
        'veiculos': veiculos,
    }
    
    return render(request, 'clientes/cliente_detail.html', context)

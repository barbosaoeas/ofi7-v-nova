"""
Views de autenticação customizadas
Login estilo: selecionar usuário → digitar apenas a senha
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import json

from .models import Funcionario


def login_view(request):
    """
    Tela de login customizada.
    Mostra todos os usuários ativos para seleção.
    Após selecionar, usuário digita apenas a senha.
    """
    # Se já está logado, redireciona
    if request.user.is_authenticated:
        if getattr(request.user, 'perfil', '') == 'visual':
            return redirect('kanban:producao')
        return redirect('dashboard:index')

    # Busca todos os funcionários ativos para exibir na tela
    # Inclui superusers (admin) mesmo sem campo 'ativo'
    funcionarios = Funcionario.objects.filter(
        is_active=True
    ).order_by('first_name', 'last_name').values(
        'id', 'username', 'first_name', 'last_name', 'perfil'
    )

    PERFIL_LABELS = {
        'operacional': 'Operacional',
        'visual': 'Visual',
        'supervisor': 'Supervisor',
        'gerente': 'Gerente',
        'admin': 'Administrador',
        'orcamentista': 'Orçamentista',
        'financeiro': 'Financeiro',
        'funcionario': 'Funcionário',  # legado
    }

    # Prepara a lista enriquecida
    usuarios = []
    for f in funcionarios:
        nome = f'{f["first_name"]} {f["last_name"]}'.strip() or f['username']
        # Iniciais para o avatar
        partes = nome.split()
        iniciais = ''.join(p[0].upper() for p in partes[:2])
        usuarios.append({
            'id': f['id'],
            'username': f['username'],
            'nome': nome,
            'iniciais': iniciais,
            'perfil': f['perfil'],
            'perfil_display': PERFIL_LABELS.get(f['perfil'], f['perfil'].capitalize()),
        })

    context = {
        'usuarios': usuarios,
        'usuarios_json': json.dumps(usuarios),
    }
    return render(request, 'funcionarios/login.html', context)


@require_http_methods(["POST"])
def autenticar_view(request):
    """
    Autentica o usuário com username + senha.
    Retorna JSON (para requisições HTMX/fetch) ou redireciona.
    """
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()

    if not username or not password:
        messages.error(request, 'Preencha usuário e senha.')
        return redirect('funcionarios:login')

    user = authenticate(request, username=username, password=password)

    if user is not None:
        if user.is_active and hasattr(user, 'ativo') and user.ativo:
            login(request, user)
            
            if hasattr(user, 'deve_mudar_senha') and user.deve_mudar_senha:
                return redirect('funcionarios:mudar_senha')

            next_url = request.POST.get('next') or request.GET.get('next')
            if not next_url and getattr(user, 'perfil', '') == 'visual':
                next_url = 'kanban:producao'
            if not next_url:
                next_url = 'dashboard:index'
            # Se next_url for uma URL relativa, redireciona direto
            if next_url.startswith('/'):
                return redirect(next_url)
            return redirect(next_url)
        else:
            messages.error(request, 'Sua conta está inativa. Fale com o administrador.')
    else:
        messages.error(request, 'Senha incorreta. Tente novamente.')

    return redirect('funcionarios:login')


from django.contrib.auth.decorators import login_required

@login_required
def mudar_senha_view(request):
    """
    Tela para mudança de senha no primeiro acesso (ou quando sugerido/obrigado).
    """
    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha', '').strip()
        confirmar_senha = request.POST.get('confirmar_senha', '').strip()
        
        if not nova_senha or not confirmar_senha:
            messages.error(request, 'Preencha as duas senhas.')
        elif nova_senha != confirmar_senha:
            messages.error(request, 'As senhas não coincidem.')
        else:
            user = request.user
            try:
                validate_password(nova_senha, user=user)
            except ValidationError as e:
                for msg in e.messages:
                    messages.error(request, msg)
                return render(request, 'funcionarios/mudar_senha.html')
            user.set_password(nova_senha)
            if hasattr(user, 'deve_mudar_senha'):
                user.deve_mudar_senha = False
            user.save()
            
            # Reconecta o usuário pois a mudança de senha invalida a sessão
            login(request, user)
            
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('dashboard:index')
            
    return render(request, 'funcionarios/mudar_senha.html')

def logout_view(request):
    """Logout customizado"""
    logout(request)
    return redirect('funcionarios:login')

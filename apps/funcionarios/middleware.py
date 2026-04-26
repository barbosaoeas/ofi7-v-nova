from django.shortcuts import redirect
from django.urls import reverse

class ForcarMudancaSenhaMiddleware:
    """
    Middleware que verifica se o usuário autenticado precisa mudar a senha.
    Se sim, redireciona para a tela de mudança de senha, bloqueando o acesso a outras páginas.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Verifica se o usuário tem o atributo 'deve_mudar_senha'
            if getattr(request.user, 'deve_mudar_senha', False):
                # Permite acesso à view de mudança de senha e logout
                url_mudar_senha = reverse('funcionarios:mudar_senha')
                url_logout = reverse('funcionarios:logout')
                
                # Permite também carregar arquivos estáticos (CSS/JS) e mídia
                if not request.path.startswith(url_mudar_senha) and \
                   not request.path.startswith(url_logout) and \
                   not request.path.startswith('/static/') and \
                   not request.path.startswith('/media/') and \
                   not request.path.startswith('/admin/'):
                    return redirect('funcionarios:mudar_senha')

            if getattr(request.user, 'perfil', '') == 'visual':
                url_logout = reverse('funcionarios:logout')
                if (
                    not request.path.startswith('/kanban/')
                    and not request.path.startswith(url_logout)
                    and not request.path.startswith('/static/')
                    and not request.path.startswith('/media/')
                ):
                    return redirect('kanban:producao')
        
        response = self.get_response(request)
        return response

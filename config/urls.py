"""
URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from apps.comissoes.views import relatorio_comissoes

urlpatterns = [
    # Redirecionar login padrão para o login customizado
    path('accounts/login/', RedirectView.as_view(pattern_name='funcionarios:login', permanent=False)),
    path('accounts/logout/', RedirectView.as_view(pattern_name='funcionarios:logout', permanent=False)),
    
    # Frontend
    path('', include('apps.dashboard.urls')),
    path('', include('apps.kanban.urls')),

    # Cadastros
    path('clientes/', include('apps.clientes.urls_crud')),
    path('veiculos/', include('apps.veiculos.urls_crud')),
    path('funcionarios/', include('apps.funcionarios.urls_crud')),
    path('pecas/', include('apps.pecas.urls_crud')),
    path('orcamentos/', include('apps.orcamentos.urls_crud')),
    path('ordens/', include('apps.ordens.urls_crud')),

    # Relatórios
    path('relatorios/comissoes/', relatorio_comissoes, name='relatorios_comissoes'),

    # Admin
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

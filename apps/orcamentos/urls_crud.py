from django.urls import path
from . import views_crud, views_etapas

app_name = 'orcamentos'

urlpatterns = [
    # Listagem
    path('', views_crud.orcamento_list, name='list'),

    # CRUD
    path('novo/', views_crud.orcamento_create, name='create'),
    path('<int:pk>/', views_crud.orcamento_detail, name='detail'),
    path('<int:pk>/editar/', views_crud.orcamento_update, name='update'),
    path('<int:pk>/deletar/', views_crud.orcamento_delete, name='delete'),

    # Revisões
    path('<int:pk>/revisao/iniciar/', views_crud.orcamento_revisao_iniciar, name='revisao_iniciar'),
    path('<int:pk>/revisao/<int:revisao_id>/confirmar/', views_crud.orcamento_revisao_confirmar, name='revisao_confirmar'),
    path('<int:pk>/revisao/<int:revisao_id>/imprimir/', views_crud.orcamento_revisao_imprimir, name='revisao_imprimir'),

    # Ações de status e OS
    path('<int:pk>/status/', views_crud.orcamento_mudar_status, name='mudar_status'),
    path('<int:pk>/gerar-os/', views_crud.orcamento_gerar_os, name='gerar_os'),

    # Aditivos
    path('<int:pk>/aditivos/pecas/novo/', views_crud.orcamento_aditivo_pecas_create, name='aditivo_pecas_create'),
    path('<int:pk>/aditivos/<int:aditivo_id>/imprimir/', views_crud.orcamento_aditivo_imprimir, name='aditivo_imprimir'),

    # HTMX
    path('veiculos-por-cliente/', views_crud.veiculos_por_cliente, name='veiculos_por_cliente'),
    path('verificar-capacidade-data/', views_crud.verificar_capacidade_data, name='verificar_capacidade_data'),

    # Etapas Padrão
    path('etapas/', views_etapas.etapa_list, name='etapa_list'),
    path('etapas/nova/', views_etapas.etapa_create, name='etapa_create'),
    path('etapas/<int:pk>/editar/', views_etapas.etapa_update, name='etapa_update'),
    path('etapas/<int:pk>/deletar/', views_etapas.etapa_delete, name='etapa_delete'),
]

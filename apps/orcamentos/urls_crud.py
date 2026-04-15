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

    # Ações de status e OS
    path('<int:pk>/status/', views_crud.orcamento_mudar_status, name='mudar_status'),
    path('<int:pk>/gerar-os/', views_crud.orcamento_gerar_os, name='gerar_os'),

    # HTMX
    path('veiculos-por-cliente/', views_crud.veiculos_por_cliente, name='veiculos_por_cliente'),
    path('verificar-capacidade-data/', views_crud.verificar_capacidade_data, name='verificar_capacidade_data'),

    # Etapas Padrão
    path('etapas/', views_etapas.etapa_list, name='etapa_list'),
    path('etapas/nova/', views_etapas.etapa_create, name='etapa_create'),
    path('etapas/<int:pk>/editar/', views_etapas.etapa_update, name='etapa_update'),
    path('etapas/<int:pk>/deletar/', views_etapas.etapa_delete, name='etapa_delete'),
]

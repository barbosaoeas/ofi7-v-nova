from django.urls import path
from . import views_crud

app_name = 'veiculos'

urlpatterns = [
    # Veículos
    path('', views_crud.veiculo_list, name='list'),
    path('novo/', views_crud.veiculo_create, name='create'),
    path('buscar-por-placa/', views_crud.veiculo_buscar_por_placa, name='buscar_por_placa'),
    path('<int:pk>/', views_crud.veiculo_detail, name='detail'),
    path('<int:pk>/editar/', views_crud.veiculo_update, name='update'),
    path('<int:pk>/deletar/', views_crud.veiculo_delete, name='delete'),
    
    # Fabricantes
    path('fabricantes/', views_crud.fabricante_list, name='fabricante_list'),
    path('fabricantes/novo/', views_crud.fabricante_create, name='fabricante_create'),
    path('fabricantes/<int:pk>/editar/', views_crud.fabricante_update, name='fabricante_update'),
    
    # Modelos
    path('modelos/', views_crud.modelo_list, name='modelo_list'),
    path('modelos/novo/', views_crud.modelo_create, name='modelo_create'),
    path('modelos/<int:pk>/editar/', views_crud.modelo_update, name='modelo_update'),
]

from django.urls import path
from . import views_crud

app_name = 'clientes'

urlpatterns = [
    path('', views_crud.cliente_list, name='list'),
    path('novo/', views_crud.cliente_create, name='create'),
    path('<int:pk>/', views_crud.cliente_detail, name='detail'),
    path('<int:pk>/editar/', views_crud.cliente_update, name='update'),
    path('<int:pk>/deletar/', views_crud.cliente_delete, name='delete'),
]

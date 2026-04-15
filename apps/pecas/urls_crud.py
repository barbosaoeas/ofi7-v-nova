from django.urls import path
from . import views_crud

app_name = 'pecas'

urlpatterns = [
    path('', views_crud.peca_list, name='list'),
    path('novo/', views_crud.peca_create, name='create'),
    path('<int:pk>/editar/', views_crud.peca_update, name='update'),
    path('<int:pk>/deletar/', views_crud.peca_delete, name='delete'),
]

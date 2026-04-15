from django.urls import path
from . import views_crud

app_name = 'ordens'

urlpatterns = [
    path('', views_crud.ordem_list, name='list'),
    path('<int:pk>/editar/', views_crud.ordem_update, name='update'),
]

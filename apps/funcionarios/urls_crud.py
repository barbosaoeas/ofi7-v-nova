from django.urls import path
from . import views_crud, views_login

app_name = 'funcionarios'

urlpatterns = [
    # Login / Auth
    path('login/', views_login.login_view, name='login'),
    path('login/autenticar/', views_login.autenticar_view, name='autenticar'),
    path('logout/', views_login.logout_view, name='logout'),
    path('mudar-senha/', views_login.mudar_senha_view, name='mudar_senha'),

    # CRUD de funcionários
    path('', views_crud.funcionario_list, name='list'),
    path('novo/', views_crud.funcionario_create, name='create'),
    path('<int:pk>/editar/', views_crud.funcionario_update, name='update'),
    path('<int:pk>/deletar/', views_crud.funcionario_delete, name='delete'),
    path('<int:pk>/reset-senha/', views_crud.funcionario_reset_password, name='reset_password'),
]

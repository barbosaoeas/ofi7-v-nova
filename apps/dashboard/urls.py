from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='index'),
    path('configuracoes/', views.configuracao_sistema, name='configuracao_sistema'),
]

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Funcionario, LogAcesso


@admin.register(Funcionario)
class FuncionarioAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'perfil', 'percentual_comissao_padrao', 'ativo']
    list_filter = ['perfil', 'ativo', 'data_admissao']
    search_fields = ['username', 'first_name', 'last_name', 'cpf', 'email']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('telefone', 'cpf', 'data_admissao', 'data_demissao')
        }),
        ('Configurações', {
            'fields': ('perfil', 'percentual_comissao_padrao', 'ativo')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em')
        }),
    )
    
    readonly_fields = ['criado_em', 'atualizado_em']


@admin.register(LogAcesso)
class LogAcessoAdmin(admin.ModelAdmin):
    list_display = ['criado_em', 'usuario', 'evento', 'ip', 'caminho']
    list_filter = ['evento', 'criado_em']
    search_fields = ['usuario__username', 'usuario__first_name', 'usuario__last_name', 'ip', 'caminho', 'user_agent']
    ordering = ['-criado_em']

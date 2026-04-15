from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Funcionario


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


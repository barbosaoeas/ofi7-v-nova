from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cpf_cnpj', 'telefone', 'cidade', 'ativo', 'criado_em']
    list_filter = ['tipo', 'ativo', 'estado']
    search_fields = ['nome', 'cpf_cnpj', 'telefone', 'email']
    readonly_fields = ['criado_em', 'atualizado_em']


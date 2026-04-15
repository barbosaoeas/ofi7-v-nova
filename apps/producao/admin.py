from django.contrib import admin
from .models import EtapaPadrao


@admin.register(EtapaPadrao)
class EtapaPadraoAdmin(admin.ModelAdmin):
    list_display = ['sequencia', 'nome', 'cor', 'gera_comissao', 'percentual_comissao_padrao', 'ativa']
    list_filter = ['ativa', 'gera_comissao']
    search_fields = ['nome']
    readonly_fields = ['criado_em', 'atualizado_em']


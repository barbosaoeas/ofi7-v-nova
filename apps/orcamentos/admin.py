from django.contrib import admin
from .models import Orcamento, OrcamentoItem, OrcamentoAditivo


class OrcamentoItemInline(admin.TabularInline):
    model = OrcamentoItem
    extra = 1
    fields = ['descricao', 'etapa', 'valor', 'ordem']


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cliente', 'veiculo', 'status', 'valor_total_servicos', 'data_orcamento']
    list_filter = ['status', 'data_orcamento']
    search_fields = ['numero', 'cliente__nome', 'veiculo__placa']
    readonly_fields = ['numero', 'criado_em', 'atualizado_em', 'valor_total_servicos', 'valor_total_com_desconto']
    inlines = [OrcamentoItemInline]
    
    def valor_total_servicos(self, obj):
        return f"R$ {obj.valor_total_servicos:,.2f}"
    valor_total_servicos.short_description = 'Valor Total'


@admin.register(OrcamentoAditivo)
class OrcamentoAditivoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'orcamento', 'status', 'criado_por', 'criado_em']
    list_filter = ['status']
    search_fields = ['numero', 'orcamento__numero', 'orcamento__cliente__nome']

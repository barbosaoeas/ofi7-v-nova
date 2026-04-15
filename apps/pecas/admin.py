from django.contrib import admin
from .models import Peca


@admin.register(Peca)
class PecaAdmin(admin.ModelAdmin):
    list_display = ['descricao', 'veiculo', 'status', 'prazo_compra', 'prazo_chegada', 'esta_atrasada']
    list_filter = ['status', 'fornecedor_tipo', 'prazo_chegada']
    search_fields = ['descricao', 'veiculo__placa', 'fornecedor_nome']
    readonly_fields = ['criado_em', 'atualizado_em', 'esta_atrasada', 'valor_venda']
    
    def esta_atrasada(self, obj):
        return '⚠️ Sim' if obj.esta_atrasada else 'Não'
    esta_atrasada.short_description = 'Atrasada'


from django.contrib import admin
from .models import OrdemServico, OrdemEtapa


class OrdemEtapaInline(admin.TabularInline):
    model = OrdemEtapa
    extra = 0
    fields = ['sequencia', 'nome', 'funcionario', 'status', 'data_programada', 'valor_servico']
    readonly_fields = ['sequencia', 'nome']


@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cliente', 'veiculo', 'status', 'percentual_conclusao', 'data_abertura']
    list_filter = ['status', 'data_abertura']
    search_fields = ['numero', 'cliente__nome', 'veiculo__placa']
    readonly_fields = ['numero', 'criado_em', 'atualizado_em', 'valor_total', 'percentual_conclusao']
    inlines = [OrdemEtapaInline]
    
    def percentual_conclusao(self, obj):
        return f"{obj.percentual_conclusao}%"
    percentual_conclusao.short_description = '% Conclusão'


@admin.register(OrdemEtapa)
class OrdemEtapaAdmin(admin.ModelAdmin):
    list_display = ['ordem', 'nome', 'funcionario', 'status', 'data_programada', 'data_inicio', 'data_fim']
    list_filter = ['status', 'nome', 'data_programada']
    search_fields = ['ordem__numero', 'nome', 'funcionario__first_name']
    readonly_fields = ['criado_em', 'atualizado_em', 'tempo_execucao', 'valor_comissao_estimado']


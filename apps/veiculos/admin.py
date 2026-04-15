from django.contrib import admin
from .models_fabricantes import Fabricante, ModeloVeiculo, CorVeiculo
from .models import Veiculo


@admin.register(CorVeiculo)
class CorVeiculoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'codigo_hex', 'ativo', 'criado_em']
    list_filter = ['ativo']
    search_fields = ['nome']
    readonly_fields = ['criado_em', 'atualizado_em']


@admin.register(Fabricante)
class FabricanteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'pais_origem', 'ativo', 'criado_em']
    list_filter = ['ativo', 'pais_origem']
    search_fields = ['nome', 'pais_origem']
    readonly_fields = ['criado_em', 'atualizado_em']


@admin.register(ModeloVeiculo)
class ModeloVeiculoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'fabricante', 'categoria', 'ativo', 'criado_em']
    list_filter = ['fabricante', 'categoria', 'ativo']
    search_fields = ['nome', 'fabricante__nome']
    readonly_fields = ['criado_em', 'atualizado_em']
    autocomplete_fields = ['fabricante']


@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ['placa', 'get_descricao', 'get_cor', 'ano_modelo', 'cliente', 'criado_em']
    list_filter = ['modelo_veiculo__fabricante', 'cor_veiculo', 'ano_modelo']
    search_fields = ['placa', 'marca', 'modelo', 'chassi', 'cliente__nome', 'modelo_veiculo__nome']
    readonly_fields = ['criado_em', 'atualizado_em']
    autocomplete_fields = ['cliente', 'modelo_veiculo', 'cor_veiculo']

    def get_descricao(self, obj):
        return obj.descricao_completa
    get_descricao.short_description = 'Veículo'

    def get_cor(self, obj):
        return obj.cor_display
    get_cor.short_description = 'Cor'


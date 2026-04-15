from django.contrib import admin
from .models import Comissao


@admin.register(Comissao)
class ComissaoAdmin(admin.ModelAdmin):
    list_display = ['funcionario', 'ordem', 'etapa', 'valor', 'status_pagamento', 'criado_em']
    list_filter = ['status_pagamento', 'criado_em', 'data_pagamento']
    search_fields = ['funcionario__first_name', 'ordem__numero', 'etapa__nome']
    readonly_fields = ['criado_em', 'atualizado_em', 'valor']
    
    def valor(self, obj):
        return f"R$ {obj.valor:,.2f}"
    valor.short_description = 'Valor'


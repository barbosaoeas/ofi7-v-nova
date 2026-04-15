from django.contrib import admin

from .models import ConfiguracaoSistema


@admin.register(ConfiguracaoSistema)
class ConfiguracaoSistemaAdmin(admin.ModelAdmin):
    list_display = ('nome_empresa', 'telefone', 'email', 'atualizado_em')

    def has_add_permission(self, request):
        if ConfiguracaoSistema.objects.exists():
            return False
        return super().has_add_permission(request)

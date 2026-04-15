from .models import ConfiguracaoSistema


def sistema_config(request):
    return {
        'sistema_config': ConfiguracaoSistema.objects.first()
    }

from apps.orcamentos.models import Orcamento


def navbar_agenda_orcamentos(request):
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', False):
        return {'navbar_orcamentos_pendentes': [], 'navbar_orcamentos_pendentes_total': 0}

    perfil = getattr(user, 'perfil', '')
    pode_ver = user.is_superuser or perfil in ['admin', 'gerente', 'supervisor', 'orcamentista']
    if not pode_ver:
        return {'navbar_orcamentos_pendentes': [], 'navbar_orcamentos_pendentes_total': 0}

    total = Orcamento.objects.filter(status__in=['rascunho', 'enviado']).count()
    return {
        'navbar_orcamentos_pendentes': [],
        'navbar_orcamentos_pendentes_total': total,
    }

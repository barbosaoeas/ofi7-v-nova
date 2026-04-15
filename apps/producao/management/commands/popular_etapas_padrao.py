"""
Command para popular etapas padrão do sistema
"""
from django.core.management.base import BaseCommand
from apps.producao.models import EtapaPadrao, ETAPAS_PADRAO


class Command(BaseCommand):
    help = 'Popula as etapas padrão do sistema Kanban'

    def handle(self, *args, **kwargs):
        self.stdout.write('Criando etapas padrão...')
        
        criadas = 0
        atualizadas = 0
        
        for etapa_data in ETAPAS_PADRAO:
            etapa, created = EtapaPadrao.objects.update_or_create(
                nome=etapa_data['nome'],
                defaults={
                    'sequencia': etapa_data['sequencia'],
                    'cor': etapa_data['cor'],
                    'ativa': True,
                    'gera_comissao': True,
                }
            )
            
            if created:
                criadas += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Criada: {etapa.nome}')
                )
            else:
                atualizadas += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Atualizada: {etapa.nome}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nConcluído! {criadas} criadas, {atualizadas} atualizadas.'
            )
        )


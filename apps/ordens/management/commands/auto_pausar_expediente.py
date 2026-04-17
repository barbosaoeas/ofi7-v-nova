from django.core.management.base import BaseCommand

from apps.ordens.services import SessaoService


class Command(BaseCommand):
    help = 'Pausa automaticamente sessões abertas ao fim do expediente quando não há horas extras autorizadas.'

    def handle(self, *args, **options):
        total = SessaoService.auto_pausar_sessoes_sem_extra()
        self.stdout.write(self.style.SUCCESS(f'OK: {total} sessão(ões) pausada(s).'))

import os
import django
import sys

# Configurar o ambiente Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.orcamentos.models import EtapaPadrao

def povoar_etapas():
    print("Iniciando o povoamento do banco com as Etapas Padrão do Orçamento...")

    etapas = [
        ("Desmontagem", 10),
        ("Funilaria", 20),
        ("Preparação", 30),
        ("Pintura", 40),
        ("Montagem", 50),
        ("Polimento", 60),
        ("Lavagem", 70),
        ("Preparação Entrega", 80),
    ]

    for nome, ordem in etapas:
        etapa, created = EtapaPadrao.objects.get_or_create(
            nome=nome,
            defaults={"ordem_default": ordem}
        )
        if created:
            print(f"✅ Etapa '{nome}' criada.")
        else:
            print(f"ℹ️ Etapa '{nome}' já existia.")

    print("\nPovoamento de Etapas concluído com sucesso!")

if __name__ == "__main__":
    povoar_etapas()

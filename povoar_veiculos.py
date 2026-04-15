import os
import django
import sys

# Configurar o ambiente Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

try:
    from apps.veiculos.models_fabricantes import Fabricante, ModeloVeiculo, CorVeiculo
except ImportError:
    # Fallback caso estejam todos no models principal
    from apps.veiculos.models import Fabricante, ModeloVeiculo, CorVeiculo

def povoar_dados():
    print("Iniciando o povoamento do banco com fabricantes, modelos e cores...")

    cores = [
        ("Branco", "#FFFFFF"),
        ("Preto", "#000000"),
        ("Prata", "#C0C0C0"),
        ("Cinza", "#808080"),
        ("Vermelho", "#FF0000"),
        ("Azul", "#0000FF"),
        ("Marrom", "#8B4513"),
        ("Verde", "#008000"),
    ]

    for nome, hex_code in cores:
        CorVeiculo.objects.get_or_create(nome=nome, defaults={"codigo_hex": hex_code})
    print(f"✅ {len(cores)} Cores cadastradas/verificadas.")

    fabricantes_modelos = {
        "Chevrolet": [("Onix", "hatch"), ("Prisma", "sedan"), ("S10", "pickup"), ("Tracker", "suv"), ("Cruze", "sedan"), ("Spin", "van")],
        "Volkswagen": [("Gol", "hatch"), ("Polo", "hatch"), ("Virtus", "sedan"), ("Saveiro", "pickup"), ("Nivus", "suv"), ("T-Cross", "suv"), ("Jetta", "sedan")],
        "Fiat": [("Uno", "hatch"), ("Palio", "hatch"), ("Mobi", "hatch"), ("Argo", "hatch"), ("Strada", "pickup"), ("Toro", "pickup"), ("Fiorino", "van"), ("Cronos", "sedan")],
        "Toyota": [("Corolla", "sedan"), ("Hilux", "pickup"), ("Yaris", "hatch"), ("SW4", "suv")],
        "Honda": [("Civic", "sedan"), ("Fit", "hatch"), ("HR-V", "suv"), ("City", "sedan")],
        "Ford": [("Ka", "hatch"), ("Fiesta", "hatch"), ("EcoSport", "suv"), ("Ranger", "pickup")],
        "Hyundai": [("HB20", "hatch"), ("HB20S", "sedan"), ("Creta", "suv"), ("Tucson", "suv")],
        "Renault": [("Kwid", "hatch"), ("Sandero", "hatch"), ("Logan", "sedan"), ("Duster", "suv"), ("Oroch", "pickup")],
        "Nissan": [("Versa", "sedan"), ("Kicks", "suv"), ("Frontier", "pickup")],
        "Jeep": [("Renegade", "suv"), ("Compass", "suv"), ("Commander", "suv")],
        "Peugeot": [("208", "hatch"), ("2008", "suv")]
    }

    total_modelos = 0
    for fab_nome, modelos in fabricantes_modelos.items():
        fab, _ = Fabricante.objects.get_or_create(nome=fab_nome)
        for mod_nome, categoria in modelos:
            ModeloVeiculo.objects.get_or_create(
                fabricante=fab,
                nome=mod_nome,
                defaults={"categoria": categoria}
            )
            total_modelos += 1

    print(f"✅ {len(fabricantes_modelos)} Fabricantes e {total_modelos} Modelos cadastrados/verificados.")
    print("\nPovoamento concluído com sucesso!")

if __name__ == "__main__":
    povoar_dados()

"""
Script para popular Fabricantes e Modelos de Veículos
Execute: python popular_fabricantes.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.veiculos.models_fabricantes import Fabricante, ModeloVeiculo

print("=" * 60)
print("  POPULANDO FABRICANTES E MODELOS DE VEÍCULOS")
print("=" * 60)
print()

# Dados: Fabricante → [Modelos]
DADOS = {
    'Chevrolet': {
        'pais': 'Estados Unidos',
        'modelos': [
            ('Onix', 'hatch'), ('Prisma', 'sedan'), ('Tracker', 'suv'),
            ('S10', 'pickup'), ('Spin', 'van'), ('Cruze', 'sedan'),
            ('Montana', 'pickup'), ('Trailblazer', 'suv'),
        ]
    },
    'Fiat': {
        'pais': 'Itália',
        'modelos': [
            ('Uno', 'hatch'), ('Palio', 'hatch'), ('Argo', 'hatch'),
            ('Mobi', 'hatch'), ('Toro', 'pickup'), ('Strada', 'pickup'),
            ('Fiorino', 'van'), ('Ducato', 'van'),
        ]
    },
    'Volkswagen': {
        'pais': 'Alemanha',
        'modelos': [
            ('Gol', 'hatch'), ('Polo', 'hatch'), ('Virtus', 'sedan'),
            ('T-Cross', 'suv'), ('Taos', 'suv'), ('Amarok', 'pickup'),
            ('Saveiro', 'pickup'), ('Nivus', 'suv'),
        ]
    },
    'Toyota': {
        'pais': 'Japão',
        'modelos': [
            ('Corolla', 'sedan'), ('Yaris', 'sedan'), ('Hilux', 'pickup'),
            ('SW4', 'suv'), ('RAV4', 'suv'), ('Etios', 'sedan'),
            ('Camry', 'sedan'),
        ]
    },
    'Honda': {
        'pais': 'Japão',
        'modelos': [
            ('Civic', 'sedan'), ('City', 'sedan'), ('HR-V', 'suv'),
            ('CR-V', 'suv'), ('Fit', 'hatch'), ('WR-V', 'suv'),
        ]
    },
    'Ford': {
        'pais': 'Estados Unidos',
        'modelos': [
            ('Ka', 'hatch'), ('Fiesta', 'hatch'), ('Fusion', 'sedan'),
            ('Ranger', 'pickup'), ('EcoSport', 'suv'), ('Territory', 'suv'),
        ]
    },
    'Hyundai': {
        'pais': 'Coreia do Sul',
        'modelos': [
            ('HB20', 'hatch'), ('Creta', 'suv'), ('Tucson', 'suv'),
            ('ix35', 'suv'), ('Azera', 'sedan'), ('Elantra', 'sedan'),
        ]
    },
    'Renault': {
        'pais': 'França',
        'modelos': [
            ('Kwid', 'hatch'), ('Sandero', 'hatch'), ('Logan', 'sedan'),
            ('Duster', 'suv'), ('Captur', 'suv'), ('Oroch', 'pickup'),
        ]
    },
    'Jeep': {
        'pais': 'Estados Unidos',
        'modelos': [
            ('Renegade', 'suv'), ('Compass', 'suv'), ('Commander', 'suv'),
            ('Wrangler', 'suv'), ('Grand Cherokee', 'suv'),
        ]
    },
    'Nissan': {
        'pais': 'Japão',
        'modelos': [
            ('Versa', 'sedan'), ('Kicks', 'suv'), ('Frontier', 'pickup'),
            ('Sentra', 'sedan'), ('March', 'hatch'),
        ]
    },
}

total_fabricantes = 0
total_modelos = 0

for nome_fabricante, dados in DADOS.items():
    # Criar ou obter fabricante
    fabricante, created = Fabricante.objects.get_or_create(
        nome=nome_fabricante,
        defaults={'pais_origem': dados['pais']}
    )
    
    if created:
        print(f"✅ Fabricante criado: {nome_fabricante} ({dados['pais']})")
        total_fabricantes += 1
    else:
        print(f"ℹ️  Fabricante já existe: {nome_fabricante}")
    
    # Criar modelos
    for nome_modelo, categoria in dados['modelos']:
        modelo, created = ModeloVeiculo.objects.get_or_create(
            fabricante=fabricante,
            nome=nome_modelo,
            defaults={'categoria': categoria}
        )
        
        if created:
            print(f"   ✅ Modelo: {nome_modelo} ({categoria})")
            total_modelos += 1

print()
print("=" * 60)
print(f"  ✅ CONCLUÍDO!")
print("=" * 60)
print(f"  📊 {total_fabricantes} fabricantes criados")
print(f"  📊 {total_modelos} modelos criados")
print(f"  📊 Total de fabricantes: {Fabricante.objects.count()}")
print(f"  📊 Total de modelos: {ModeloVeiculo.objects.count()}")
print("=" * 60)
print()

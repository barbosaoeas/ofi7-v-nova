"""
Script para popular as principais Cores de Veículos
Execute: python popular_cores.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.veiculos.models_fabricantes import CorVeiculo

print("=" * 60)
print("  POPULANDO CORES DE VEICULOS")
print("=" * 60)
print()

# Lista de cores principais (Nome, Hex)
CORES = [
    ('Branco', '#FFFFFF'),
    ('Preto', '#000000'),
    ('Prata', '#C0C0C0'),
    ('Cinza', '#808080'),
    ('Vermelho', '#FF0000'),
    ('Azul', '#0000FF'),
    ('Verde', '#008000'),
    ('Amarelo', '#FFFF00'),
    ('Bege', '#F5F5DC'),
    ('Marrom', '#A52A2A'),
    ('Laranja', '#FFA500'),
    ('Vinho', '#800000'),
    ('Grafite', '#383838'),
    ('Champagne', '#F1E9D2'),
]

total_criado = 0
total_existente = 0

for nome, hex_code in CORES:
    cor, created = CorVeiculo.objects.get_or_create(
        nome=nome,
        defaults={'codigo_hex': hex_code}
    )
    if created:
        print(f"   OK - Cor criada: {nome}")
        total_criado += 1
    else:
        print(f"   INFO - Cor ja existe: {nome}")
        total_existente += 1

print("\n" + "=" * 60)
print(f"  CONCLUIDO! {total_criado} criadas, {total_existente} ja existiam.")
print("=" * 60)
print()

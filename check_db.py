import os
import sys
sys.path.insert(0, r'c:\ofi7 renovado')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from django.db import connection
cur = connection.cursor()
cur.execute("PRAGMA table_info(veiculos_veiculo)")
cols = [r[1] for r in cur.fetchall()]
print("Colunas no banco:", cols)
print()
print("Tem foto_principal:", 'foto_principal' in cols)
print("Tem modelo_veiculo_id:", 'modelo_veiculo_id' in cols)

# Checar migration state
from django.db.migrations.executor import MigrationExecutor
executor = MigrationExecutor(connection)
applied = executor.loader.applied_migrations
print()
print("Migrations aplicadas:", sorted([str(m) for m in applied if 'veiculos' in str(m)]))

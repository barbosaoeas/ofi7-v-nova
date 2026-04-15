"""
Script para popular dados de teste no sistema
Execute: python popular_dados_teste.py
"""
import os
import django
import sys

# Forçar saída UTF-8 para evitar erros de encoding no Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.clientes.models import Cliente
from apps.veiculos.models import Veiculo
from apps.funcionarios.models import Funcionario
from apps.orcamentos.models import Orcamento, OrcamentoItem
from apps.ordens.services import OrdemServicoService
from datetime import date, timedelta

print("=" * 50)
print("  POPULANDO DADOS DE TESTE")
print("=" * 50)
print()

# 1. Criar Cliente
print("1. Criando Cliente...")
cliente, created = Cliente.objects.get_or_create(
    cpf_cnpj="123.456.789-00",
    defaults={
        'tipo': 'fisica',
        'categoria': 'ambos',
        'nome': 'João Silva',
        'telefone': '11999999999',
        'email': 'joao@email.com',
        'cep': '01000-000',
        'endereco': 'Rua Teste',
        'numero': '123',
        'bairro': 'Centro',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'ativo': True
    }
)
if created:
    print(f"   OK - Cliente criado: {cliente.nome} (ID: {cliente.id})")
else:
    # Atualiza para 'ambos' se já existia
    cliente.categoria = 'ambos'
    cliente.save()
    print(f"   INFO - Cliente já existe: {cliente.nome} (ID: {cliente.id}) - Categoria atualizada para 'ambos'")

# 2. Criar Veículo
print("\n2. Criando Veículo...")
veiculo, created = Veiculo.objects.get_or_create(
    placa="ABC1234",
    defaults={
        'cliente': cliente,
        'marca': 'Chevrolet',
        'modelo': 'Onix',
        'ano_fabricacao': 2020,
        'ano_modelo': 2020,
        'cor': 'Branco',
        'km_atual': 15000
    }
)
if created:
    print(f"   OK - Veículo criado: {veiculo.marca} {veiculo.modelo} - {veiculo.placa} (ID: {veiculo.id})")
else:
    print(f"   INFO - Veículo já existe: {veiculo.marca} {veiculo.modelo} - {veiculo.placa} (ID: {veiculo.id})")

# 3. Criar Funcionário
print("\n3. Criando Funcionário...")
funcionario, created = Funcionario.objects.get_or_create(
    username="jose",
    defaults={
        'first_name': 'José',
        'last_name': 'Santos',
        'email': 'jose@email.com',
        'telefone': '11988888888',
        'cpf': '987.654.321-00',
        'perfil': 'operacional',
        'percentual_comissao_padrao': 12.00,
        'ativo': True
    }
)
if created:
    funcionario.set_password('jose123')
    funcionario.save()
    print(f"   OK - Funcionário criado: {funcionario.get_full_name()} (ID: {funcionario.id})")
    print(f"      Login: jose / Senha: jose123")
else:
    print(f"   INFO - Funcionário já existe: {funcionario.get_full_name()} (ID: {funcionario.id})")

# 4. Criar Orçamento
print("\n4. Criando Orçamento...")
admin = Funcionario.objects.filter(is_superuser=True).first()
if not admin:
    print("   ERRO: Nenhum superusuário encontrado. Crie um admin primeiro.")
else:
    orcamento, created = Orcamento.objects.get_or_create(
        cliente=cliente,
        veiculo=veiculo,
        criado_por=admin,
        defaults={
            'validade': date.today() + timedelta(days=30),
            'desconto': 0,
            'observacoes': 'Cliente solicitou urgência'
        }
    )
    if created:
        print(f"   OK - Orçamento criado: {orcamento.numero} (ID: {orcamento.id})")
        
    # 5. Criar Itens
    print("\n5. Criando Itens...")
    if created:
        item1 = OrcamentoItem.objects.create(
            orcamento=orcamento,
            descricao="Reparo Parachoque Dianteiro",
            etapa_nome="Funilaria",
            valor=450.00
        )
        item2 = OrcamentoItem.objects.create(
            orcamento=orcamento,
            descricao="Pintura Parachoque Dianteiro",
            etapa_nome="Pintura",
            valor=600.00
        )
        print("   OK - Itens criados!")
    else:
        print("   INFO - Itens já existem")

    # 6. Aprovar Orçamento e Gerar OS
    print("\n6. Gerando Ordem de Serviço...")
    if orcamento.status != 'aprovado':
        orcamento.status = 'aprovado'
        orcamento.save()
        
        os_servico = OrdemServicoService.criar_de_orcamento(orcamento.id, admin)
        print(f"   OK - OS Gerada: {os_servico.numero}")
    else:
        print("   INFO - OS já existe para este orçamento")

print("\n" + "=" * 50)
print("  DADOS POPULADOS COM SUCESSO!")
print("=" * 50)
print()
print("📋 RESUMO:")
print(f"   Cliente: {cliente.nome}")
print(f"   Veículo: {veiculo.marca} {veiculo.modelo} - {veiculo.placa}")
print(f"   Funcionário: {funcionario.get_full_name()} (Login: jose / Senha: jose123)")
if 'orcamento' in locals():
    print(f"   Orçamento: {orcamento.numero} - Status: {orcamento.status}")
print()
print("🧪 TESTE AGORA:")
print("   1. Acesse: http://localhost:8000/admin/")
print("   2. Menu Peças: http://localhost:8000/pecas/")
print()

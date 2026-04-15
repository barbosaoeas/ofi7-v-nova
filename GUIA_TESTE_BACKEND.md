# 🧪 Guia de Teste do Backend

Este guia mostra como testar o backend do sistema passo a passo.

## 1️⃣ Configurar e Rodar o Backend

```bash
# 1. Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar .env
copy .env.example .env

# 4. Migrar banco
python manage.py makemigrations
python manage.py migrate

# 5. Popular etapas padrão
python manage.py popular_etapas_padrao

# 6. Criar superusuário
python manage.py createsuperuser
# Username: admin
# Password: admin123

# 7. Rodar servidor
python manage.py runserver
```

## 2️⃣ Acessar Admin

Abra: http://localhost:8000/admin/

Login: admin / admin123

### Criar dados de teste:

1. **Cliente**
   - Nome: João Silva
   - Telefone: (11) 99999-9999
   - CPF: 123.456.789-00

2. **Veículo**
   - Cliente: João Silva
   - Placa: ABC-1234
   - Marca: Chevrolet
   - Modelo: Onix
   - Ano: 2020

3. **Funcionário** (além do admin)
   - Username: jose
   - First name: José
   - Last name: Santos
   - Perfil: Funcionário
   - Percentual comissão: 12%
   - Ativo: Sim
   - Password: jose123

4. **Orçamento**
   - Cliente: João Silva
   - Veículo: ABC-1234
   - Criado por: admin
   - Status: Aprovado

5. **Itens do Orçamento**
   - Descrição: Reparo lateral esquerda
   - Etapa: Funilaria
   - Valor: R$ 800,00
   
   - Descrição: Pintura completa lateral
   - Etapa: Pintura
   - Valor: R$ 1.200,00

6. **Criar OS a partir do Orçamento**
   - No Django shell:
   
```python
python manage.py shell

from apps.ordens.services import OrdemServicoService
from apps.orcamentos.models import Orcamento
from apps.funcionarios.models import Funcionario

orcamento = Orcamento.objects.first()
admin = Funcionario.objects.get(username='admin')

os = OrdemServicoService.criar_de_orcamento(
    orcamento_id=orcamento.id,
    criado_por=admin
)

print(f"OS criada: {os.numero}")
print(f"Etapas criadas: {os.etapas.count()}")
```

7. **Programar Etapa para Funcionário**
   - No Admin, vá em Ordens de Serviço > Etapas
   - Edite a etapa de "Funilaria"
   - Atribuir funcionário: José Santos
   - Data programada: Hoje
   - Salvar

## 3️⃣ Testar API

### Obter Token

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"jose\", \"password\": \"jose123\"}"
```

Copie o `access` token recebido.

### Minhas Etapas

```bash
curl -X GET http://localhost:8000/api/ordens/etapas/minhas-etapas/ \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### Iniciar Etapa

```bash
curl -X POST http://localhost:8000/api/ordens/etapas/1/iniciar/ \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json"
```

### Concluir Etapa (sem peça pendente)

```bash
curl -X POST http://localhost:8000/api/ordens/etapas/1/concluir/ \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d "{\"tem_peca_pendente\": false}"
```

### Verificar Comissão Gerada

```bash
curl -X GET http://localhost:8000/api/comissoes/comissoes/minhas/ \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## 4️⃣ Swagger UI

Melhor forma de testar: http://localhost:8000/api/docs/

1. Clique em "Authorize"
2. Cole o token JWT
3. Teste todas as APIs interativamente

## 5️⃣ Fluxo Completo de Teste

### Cenário: Funcionário executa tarefa

1. Funcionário acessa app (faz login)
2. Vê suas tarefas: `GET /api/ordens/etapas/minhas-etapas/`
3. Inicia a tarefa: `POST /api/ordens/etapas/{id}/iniciar/`
4. Trabalha na tarefa...
5. Conclui a tarefa: `POST /api/ordens/etapas/{id}/concluir/`
6. Sistema gera comissão automaticamente
7. Funcionário vê comissão: `GET /api/comissoes/comissoes/minhas/`

### Cenário: Tarefa bloqueada por peça

1. Funcionário inicia etapa
2. Durante execução, percebe falta de peça
3. Conclui marcando peça pendente:
```json
{
  "tem_peca_pendente": true,
  "observacao_peca": "Precisa para-choque dianteiro"
}
```
4. Sistema:
   - Marca etapa como "aguardando_peca"
   - Cria registro de Peça
   - NÃO gera comissão
5. Quando peça chegar:
   - Supervisor marca como recebida: `POST /api/pecas/pecas/{id}/marcar-recebida/`
   - Etapa volta para "pendente"
   - Pode ser reprogramada

## ✅ Checklist de Testes

- [ ] Criar cliente, veículo, funcionário
- [ ] Criar orçamento e aprovar
- [ ] Gerar OS via service
- [ ] Programar etapa para funcionário
- [ ] Obter token JWT
- [ ] Listar minhas etapas
- [ ] Iniciar etapa
- [ ] Tentar iniciar segunda etapa (deve falhar)
- [ ] Concluir etapa
- [ ] Verificar comissão gerada
- [ ] Verificar próxima etapa liberada
- [ ] Testar fluxo com peça pendente
- [ ] Marcar peça como recebida
- [ ] Aprovar comissão (como supervisor)

## 🐛 Problemas Comuns

**Erro de importação circular:**
- Reinicie o servidor

**Token expirado:**
- Gere novo token com `/api/token/`

**Funcionário não pode iniciar etapa:**
- Verifique se não tem outra em andamento
- Verifique se etapa está com status "pendente"

**Comissão não foi gerada:**
- Verifique se concluiu com `tem_peca_pendente=false`
- Verifique se etapa foi realmente marcada como "concluido"


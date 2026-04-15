# ❓ Perguntas Frequentes (FAQ)

## 🔐 Autenticação

### Como faço login?
Use `POST /api/token/` com username e password. Salve o token `access` retornado.

### Token expirou, o que fazer?
Faça login novamente para obter um novo token.

### Como usar o token nas requisições?
Adicione header: `Authorization: Bearer SEU_TOKEN`

---

## 👨‍🔧 Funcionários e Tarefas

### Posso iniciar várias tarefas ao mesmo tempo?
**NÃO**. O sistema permite apenas 1 tarefa em andamento por funcionário. Esta validação é feita no backend.

### O que acontece ao concluir uma tarefa?
Depende:
- **Sem peça pendente:** Gera comissão automaticamente + libera próxima etapa
- **Com peça pendente:** Marca como "aguardando_peca" + cria registro de Peça + NÃO gera comissão

### Como sei qual percentual de comissão vou receber?
O sistema usa hierarquia:
1. Percentual definido na etapa
2. Percentual padrão do funcionário
3. 10% (padrão do sistema)

### E se eu não conseguir concluir a tarefa?
O supervisor pode desatribuir a tarefa de você no admin Django.

---

## 📦 Peças

### Como funciona o fluxo de peças?
1. Funcionário conclui tarefa marcando "tem peça pendente"
2. Sistema cria registro de Peça automaticamente
3. Supervisor vê a solicitação no sistema
4. Quando peça chegar, marca como recebida
5. Etapa bloqueada volta para "pendente"
6. Supervisor pode reprogramar a etapa

### Posso editar uma peça solicitada?
Sim, através do Django Admin.

### Como vejo peças atrasadas?
`GET /api/pecas/pecas/atrasadas/` ou `GET /api/pecas/pecas/alertas/`

---

## 💰 Comissões

### Quando a comissão é gerada?
Automaticamente ao concluir uma etapa **sem** marcar peça pendente.

### Posso editar o valor da comissão?
Supervisores podem ajustar valores no Django Admin antes de aprovar.

### Como funciona o status de comissão?
- `pendente`: Recém criada
- `aprovada`: Supervisor aprovou
- `paga`: Foi paga ao funcionário
- `cancelada`: Cancelada

### Se refizer um serviço, gera nova comissão?
Sim. Se a etapa for reaberta e concluída novamente, gera nova comissão.

---

## 🔄 Ordens de Serviço

### Como criar uma OS?
Via Django Shell:
```python
from apps.ordens.services import OrdemServicoService
from apps.orcamentos.models import Orcamento

os = OrdemServicoService.criar_de_orcamento(
    orcamento_id=1,
    criado_por=funcionario
)
```

### O que acontece quando aprovo um orçamento?
Nada automaticamente. Você precisa manualmente chamar o service para gerar a OS.

### Posso pular etapas?
Não no fluxo automático. Mas o supervisor pode ajustar manualmente no admin.

### Como funciona a sequência de etapas?
Definida no campo `sequencia` do model. Etapas padrão:
1. Pátio
2. Desmontagem
3. Funilaria
4. Preparação Pintura
5. Pintura
6. Montagem
7. Polimento
8. Preparação Entrega
9. Finalizado

---

## 🔧 Problemas Técnicos

### Erro: "Token inválido"
- Gere novo token fazendo login novamente
- Verifique se está usando `Bearer` antes do token

### Erro: "Funcionário já tem tarefa em andamento"
- Conclua a tarefa atual antes de iniciar nova
- Se travou, peça ao supervisor para desatribuir no admin

### Flutter não conecta no backend
- Verifique o `baseUrl` em `lib/core/api/api_endpoints.dart`
- Use IP da máquina, não localhost (exceto emulador Android que usa 10.0.2.2)
- Backend está rodando? `python manage.py runserver`

### Comissão não foi gerada
- Etapa foi concluída sem peça pendente?
- Etapa tem funcionário atribuído?
- Veja logs no terminal do Django

### Migrations não funcionam
```bash
# Delete db.sqlite3 e migrations antigas
python manage.py makemigrations
python manage.py migrate
```

---

## 📱 Flutter

### Onde configurar o IP do servidor?
`flutter_app/lib/core/api/api_endpoints.dart`

Exemplos:
- Android Emulator: `http://10.0.2.2:8000`
- iOS Simulator: `http://localhost:8000`
- Dispositivo físico: `http://192.168.1.XXX:8000` (IP da sua máquina)

### Como debugar erros de API?
Adicione prints no `ApiClient`:
```dart
print('Response: ${response.body}');
```

### App trava ao fazer requisição
- Verifique conexão de rede
- Backend está respondendo?
- Token é válido?

---

## 🏗️ Arquitetura

### Onde fica a lógica de negócio?
**Backend**, nos arquivos `services.py` de cada app.

### E no Flutter?
**NUNCA**. Flutter apenas consome API e gerencia UI.

### Posso adicionar uma regra no Flutter?
Se for validação de UI (campos vazios, etc): SIM  
Se for regra de negócio (cálculos, validações críticas): **NÃO**

### Como adicionar uma nova etapa padrão?
Edite `apps/producao/models.py` no array `ETAPAS_PADRAO` e rode:
```bash
python manage.py popular_etapas_padrao
```

---

## 📊 Dados de Teste

### Como criar dados de teste rapidamente?
Use o Django Admin: http://localhost:8000/admin/

Ou via shell:
```python
python manage.py shell

from apps.clientes.models import Cliente
from apps.veiculos.models import Veiculo

cliente = Cliente.objects.create(
    nome="Teste Cliente",
    telefone="11999999999"
)

veiculo = Veiculo.objects.create(
    cliente=cliente,
    placa="TEST123",
    marca="Chevrolet",
    modelo="Onix"
)
```

### Tem um script para popular tudo?
Ainda não. Recomendamos usar o admin para criar dados iniciais.

---

## 🚀 Deploy

### Como colocar em produção?
1. Configurar PostgreSQL
2. Ajustar `settings.py` (DEBUG=False, ALLOWED_HOSTS)
3. Coletar arquivos estáticos: `python manage.py collectstatic`
4. Usar Gunicorn/uWSGI
5. Configurar Nginx
6. Usar HTTPS
7. Configurar variáveis de ambiente

### Preciso de servidor específico?
Recomendado:
- Backend: Ubuntu 20.04+ com Python 3.11
- Banco: PostgreSQL 14+
- Flutter: Compilado para Android/iOS

---

## 📚 Documentação

### Onde vejo todos os endpoints?
http://localhost:8000/api/docs/ (Swagger UI)

### Tem documentação de cada campo?
Sim, nos docstrings dos models e serializers.

### Como testar uma API sem o Flutter?
Use Swagger UI, Postman ou curl (veja `EXEMPLOS_API.md`)

---

## 🤝 Contribuindo

### Como adicionar um novo app?
1. `python manage.py startapp apps/nome_app`
2. Adicionar em `INSTALLED_APPS` no settings
3. Criar models
4. Criar services com regras de negócio
5. Criar serializers e views
6. Adicionar rotas

### Posso modificar o prompt original?
Sim, mas mantenha os princípios:
- Backend = regras
- Services isolados
- Flutter = interface
- Modularidade

---

## ✅ Boas Práticas

### O que FAZER:
✅ Colocar regras de negócio em Services  
✅ Validar no backend  
✅ Documentar endpoints  
✅ Tratar erros  
✅ Testar antes de commitar  

### O que NÃO fazer:
❌ Colocar lógica de negócio no Flutter  
❌ Editar models diretamente no shell de produção  
❌ Commitar com `DEBUG=True`  
❌ Hardcodar valores  
❌ Ignorar erros de validação  

---

**Não encontrou sua dúvida?** Verifique os arquivos:
- README.md
- DOCUMENTACAO_API.md
- GUIA_TESTE_BACKEND.md
- RESUMO_PROJETO.md


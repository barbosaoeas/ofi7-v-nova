# Sistema de Gestão de Oficina

Sistema completo de gestão para oficinas de funilaria e pintura, desenvolvido 100% com Django.

## 🏗️ Arquitetura

### Backend e Frontend (Django)
- **clientes** - Gestão de clientes
- **veiculos** - Cadastro de veículos
- **funcionarios** - Usuários e perfis
- **orcamentos** - Orçamentos e itens
- **ordens** - Ordens de Serviço e Etapas
- **producao** - Controle de Kanban
- **pecas** - Controle de peças
- **comissoes** - Comissões automáticas

### Princípios
✅ Lógica Centralizada = Toda regra de negócio no Backend  
✅ Services = Lógica de negócio isolada dos Models/Views  
✅ Frontend Web = Django Templates + Tailwind CSS + HTMX  

## 🚀 Setup do Projeto

### 1. Criar ambiente virtual

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar ambiente

Copie `.env.example` para `.env` e configure:

```bash
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
```

### 4. Migrar banco de dados

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Popular etapas padrão

```bash
python manage.py popular_etapas_padrao
```

### 6. Criar superusuário

```bash
python manage.py createsuperuser
```

### 7. Rodar servidor

```bash
python manage.py runserver
```

## 🔄 Fluxo Principal

1. **Criar orçamento** → Inserir serviços com valores
2. **Aprovar orçamento** → Gerar Ordem de Serviço (OS)
3. **OS gera etapas** automaticamente
4. **Supervisor programa** tarefas para funcionários
5. **Funcionários executam** via interface Web
6. **Sistema controla** peças automaticamente
7. **Comissão gerada** ao concluir etapa

## 📦 Etapas do Kanban

1. Pátio
2. Desmontagem
3. Funilaria
4. Preparação Pintura
5. Pintura
6. Montagem
7. Polimento
8. Preparação Entrega
9. Finalizado

## 🎯 Status

- ✅ Models implementados
- ✅ Services com regras de negócio
- ✅ Admin configurado
- ✅ Frontend Web (Tailwind + HTMX)

## 📝 Próximos Passos

1. Refinar fluxos de produção
2. Adicionar relatórios de comissão
3. Testes completos de integração

## 🛠️ Tecnologias

- Python 3.11+
- Django 4.2
- HTMX
- Tailwind CSS
- PostgreSQL (produção) / SQLite (dev)


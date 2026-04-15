# 🚀 Instruções de Setup

## ⚡ Método Rápido (Recomendado)

### Windows - Usando scripts automáticos:

#### Opção 1: Arquivo .BAT (mais compatível)
1. **Duplo clique em:** `setup.bat`
2. Aguarde a instalação (pode demorar 2-5 minutos)
3. Quando terminar, execute: `criar_superuser.bat`
4. Crie usuário admin (username: admin, senha: admin123 ou a que preferir)
5. Execute: `rodar_servidor.bat`
6. Acesse: http://localhost:8000/admin/

#### Opção 2: PowerShell Script
1. Abra PowerShell **como Administrador**
2. Execute: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
3. Navegue até a pasta: `cd "c:\ofi7 renovado"`
4. Execute: `.\setup.ps1`
5. Siga as instruções na tela

---

## 🔧 Método Manual (se scripts falharem)

### 1. Abrir PowerShell na pasta do projeto

```powershell
cd "c:\ofi7 renovado"
```

### 2. Criar ambiente virtual (se ainda não existe)

```powershell
python -m venv venv
```

### 3. Ativar ambiente virtual

```powershell
.\venv\Scripts\activate
```

💡 **Dica:** Você saberá que ativou quando aparecer `(venv)` antes do prompt:
```
(venv) PS C:\ofi7 renovado>
```

### 4. Instalar dependências

```powershell
pip install Django==4.2.7
pip install djangorestframework==3.14.0
pip install djangorestframework-simplejwt==5.3.0
pip install django-cors-headers==4.3.0
pip install python-decouple==3.8
pip install pillow==10.1.0
pip install drf-spectacular==0.26.5
```

**OU instale tudo de uma vez:**
```powershell
pip install -r requirements.txt
```

### 5. Verificar instalação

```powershell
python -m django --version
```

Deve mostrar: `4.2.7`

### 6. Criar banco de dados

```powershell
python manage.py makemigrations
python manage.py migrate
```

### 7. Popular etapas padrão

```powershell
python manage.py popular_etapas_padrao
```

Deve mostrar:
```
✓ Criada: Pátio
✓ Criada: Desmontagem
✓ Criada: Funilaria
...
Concluído! 9 criadas, 0 atualizadas.
```

### 8. Criar superusuário

```powershell
python manage.py createsuperuser
```

Digite:
- **Username:** admin
- **Email:** (pode deixar em branco, aperte Enter)
- **Password:** admin123 (ou a que preferir)
- **Password (again):** admin123

### 9. Rodar servidor

```powershell
python manage.py runserver
```

Você verá:
```
Django version 4.2.7, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

## ✅ Verificar se funcionou

### 1. Acessar Admin
- Abra navegador: http://localhost:8000/admin/
- Login: admin / admin123
- Você deve ver o painel do Django Admin

### 2. Acessar API Docs
- Abra: http://localhost:8000/api/docs/
- Você deve ver a documentação Swagger da API

### 3. Testar API
- Na documentação Swagger, clique em "Authorize"
- Vá em `/api/token/` e teste fazer login
- Copie o token e autorize
- Teste outros endpoints

---

## 🐛 Problemas Comuns

### Erro: "python não é reconhecido"
**Solução:** Instale Python 3.11+ de https://www.python.org/
- ✅ Marque "Add Python to PATH" durante instalação

### Erro: "pip install falha"
**Solução 1:** Atualize pip:
```powershell
python -m pip install --upgrade pip
```

**Solução 2:** Desabilite temporariamente antivírus e tente novamente

**Solução 3:** Instale pacotes um por um (ao invés de `requirements.txt`)

### Erro: "No module named 'django'"
**Solução:** Você não ativou o ambiente virtual
```powershell
.\venv\Scripts\activate
```

### Erro: "python manage.py não funciona"
**Solução:** Verifique se está na pasta correta:
```powershell
cd "c:\ofi7 renovado"
dir manage.py  # Deve existir
```

### Servidor não inicia
**Solução:** Porta 8000 já está em uso?
```powershell
# Use outra porta
python manage.py runserver 8080
```

Acesse: http://localhost:8080/

---

## 📱 Próximos Passos

Depois que o backend estiver rodando:

1. **Criar dados de teste** no admin
   - Cliente
   - Veículo
   - Funcionário
   - Orçamento
   - OS

2. **Testar API** via Swagger (http://localhost:8000/api/docs/)

3. **Acessar Dashboard**
   - Abra: http://localhost:8000/
   - Explore as funcionalidades web

---

## 🆘 Ainda com problemas?

Leia:
- `FAQ.md` - Perguntas frequentes
- `GUIA_TESTE_BACKEND.md` - Como testar
- `DOCUMENTACAO_API.md` - Documentação da API

Ou abra uma issue no repositório.


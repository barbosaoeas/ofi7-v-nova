# 🔧 Reativar Recursos Desabilitados

Durante o setup, alguns recursos foram **temporariamente desabilitados** porque as dependências não instalaram automaticamente. Vamos reativá-los agora!

---

## 📦 **O QUE FOI DESABILITADO:**

### 1. ✅ **django-filter** (Filtros avançados nas APIs)
### 2. ✅ **drf-spectacular** (Documentação Swagger)

---

## 🚀 **COMO REATIVAR:**

### **1️⃣ INSTALAR AS DEPENDÊNCIAS:**

```powershell
# Ative o ambiente virtual
.\venv\Scripts\activate

# Instale os pacotes
pip install django-filter drf-spectacular
```

---

### **2️⃣ REATIVAR DJANGO-FILTER:**

**Arquivos afetados:**
- `apps/clientes/views.py`
- `apps/veiculos/views.py`
- `apps/funcionarios/views.py`
- `apps/orcamentos/views.py`
- `apps/producao/views.py`

**O que fazer:**

Nos arquivos acima, **descomente** as linhas:

**ANTES (comentado):**
```python
# from django_filters.rest_framework import DjangoFilterBackend
```

**DEPOIS (descomentado):**
```python
from django_filters.rest_framework import DjangoFilterBackend
```

E nos ViewSets, adicione novamente:

**ANTES:**
```python
filter_backends = [filters.SearchFilter, filters.OrderingFilter]
```

**DEPOIS:**
```python
filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
filterset_fields = ['campo1', 'campo2']  # Adicione os campos de filtro
```

**Exemplo completo (ClienteViewSet):**
```python
from django_filters.rest_framework import DjangoFilterBackend

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'ativo', 'cidade', 'estado']  # ← Adicione isso
    search_fields = ['nome', 'cpf_cnpj', 'telefone', 'email']
    ordering_fields = ['nome', 'criado_em']
    ordering = ['nome']
```

**Benefício:** Permite filtros como `?tipo=fisica&ativo=true`

---

### **3️⃣ REATIVAR DRF-SPECTACULAR (Swagger UI):**

#### **A. Descomentar em `config/settings.py`:**

**Linha ~29:**
```python
INSTALLED_APPS = [
    # ...
    'drf_spectacular',  # ← Descomente
]
```

**Linha ~113:**
```python
REST_FRAMEWORK = {
    # ...
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',  # ← Descomente
}
```

#### **B. Descomentar em `config/urls.py`:**

**Linhas ~8-9:**
```python
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView  # ← Descomente
```

**Linhas ~14-16:**
```python
path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  # ← Descomente
path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),  # ← Descomente
```

#### **C. Descomentar decoradores `@extend_schema` nas views:**

**Arquivos afetados:**
- `apps/ordens/views.py`
- `apps/pecas/views.py`
- `apps/comissoes/views.py`

**Descomente:**
```python
from drf_spectacular.utils import extend_schema, OpenApiParameter  # ← Linha 8

# E os decoradores @extend_schema antes das actions
@extend_schema(
    summary="Título",
    description="Descrição",
    responses={200: Serializer}
)
@action(detail=False, methods=['get'])
def minha_action(self, request):
    ...
```

**Benefício:** Documentação interativa em http://localhost:8000/api/docs/

---

## ✅ **VERIFICAR SE FUNCIONOU:**

### **1. Django-filter:**
```
GET http://localhost:8000/api/clientes/clientes/?tipo=fisica&ativo=true
```
Deve filtrar apenas clientes pessoa física ativos.

### **2. DRF-Spectacular:**
Acesse: **http://localhost:8000/api/docs/**

Deve aparecer a interface Swagger UI completa!

---

## 🔄 **SCRIPT AUTOMÁTICO (OPCIONAL):**

Se quiser, posso criar um script que faz todas essas alterações automaticamente. Me avise!

---

## 📝 **RESUMO RÁPIDO:**

```powershell
# 1. Instalar
pip install django-filter drf-spectacular

# 2. Descomentar imports e configurações
# (Ver detalhes acima)

# 3. Reiniciar servidor
python manage.py runserver

# 4. Testar
# http://localhost:8000/api/docs/
```

---

## 🎯 **STATUS ATUAL DO PROJETO:**

### ✅ **FUNCIONANDO (sem dependências extras):**
- Todos os CRUDs
- Autenticação JWT
- Busca por texto
- Ordenação
- Services com regras de negócio
- Admin Django

### ⚠️ **DESABILITADO (facilmente reativável):**
- Filtros avançados (django-filter)
- Documentação Swagger (drf-spectacular)

### 🚧 **PENDENTE:**
- App Flutter (estrutura criada, precisa testar)
- Dados de teste populados

---

**Quer que eu:**
1. Crie um script para reativar tudo automaticamente?
2. Ajude a configurar o Flutter?
3. Crie dados de teste no backend?

Me diga! 😊

# Setup PowerShell Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SETUP - Sistema de Gestao de Oficina" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Python
Write-Host "[1/7] Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "OK - $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERRO: Python nao encontrado!" -ForegroundColor Red
    Write-Host "Instale Python 3.11+ de https://www.python.org/" -ForegroundColor Red
    pause
    exit 1
}

# 2. Criar ambiente virtual
Write-Host ""
Write-Host "[2/7] Criando ambiente virtual..." -ForegroundColor Yellow
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO: Falha ao criar ambiente virtual" -ForegroundColor Red
        pause
        exit 1
    }
    Write-Host "OK - Ambiente virtual criado!" -ForegroundColor Green
} else {
    Write-Host "Ambiente virtual ja existe - OK!" -ForegroundColor Green
}

# 3. Ativar ambiente virtual
Write-Host ""
Write-Host "[3/7] Ativando ambiente virtual..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# 4. Instalar dependências
Write-Host ""
Write-Host "[4/7] Instalando dependencias (pode demorar)..." -ForegroundColor Yellow
Write-Host "Aguarde..." -ForegroundColor Gray
pip install --quiet --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "AVISO: Erro ao instalar algumas dependencias" -ForegroundColor Yellow
    Write-Host "Tente executar manualmente: pip install -r requirements.txt" -ForegroundColor Yellow
} else {
    Write-Host "OK - Dependencias instaladas!" -ForegroundColor Green
}

# 5. Criar .env
Write-Host ""
Write-Host "[5/7] Criando arquivo .env..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "OK - Arquivo .env criado!" -ForegroundColor Green
} else {
    Write-Host "Arquivo .env ja existe - OK!" -ForegroundColor Green
}

# 6. Migrations
Write-Host ""
Write-Host "[6/7] Criando banco de dados..." -ForegroundColor Yellow
python manage.py makemigrations
python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Falha ao criar banco de dados" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "OK - Banco de dados criado!" -ForegroundColor Green

# 7. Popular etapas
Write-Host ""
Write-Host "[7/7] Populando etapas padrao..." -ForegroundColor Yellow
python manage.py popular_etapas_padrao
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Falha ao popular etapas" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "OK - Etapas populadas!" -ForegroundColor Green

# Conclusão
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SETUP CONCLUIDO COM SUCESSO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Criar superusuario (admin):" -ForegroundColor White
Write-Host "   python manage.py createsuperuser" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Rodar o servidor:" -ForegroundColor White
Write-Host "   python manage.py runserver" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Acessar o admin:" -ForegroundColor White
Write-Host "   http://localhost:8000/admin/" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Acessar documentacao da API:" -ForegroundColor White
Write-Host "   http://localhost:8000/api/docs/" -ForegroundColor Gray
Write-Host ""
pause


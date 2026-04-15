@echo off
echo ========================================
echo   SETUP - Sistema de Gestao de Oficina
echo ========================================
echo.

REM Verifica se venv existe
if not exist "venv\Scripts\activate.bat" (
    echo [1/7] Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ERRO: Falha ao criar ambiente virtual
        echo Certifique-se de ter Python 3.11+ instalado
        pause
        exit /b 1
    )
    echo OK - Ambiente virtual criado!
) else (
    echo [1/7] Ambiente virtual ja existe - OK!
)

echo.
echo [2/7] Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo.
echo [3/7] Instalando dependencias (isso pode demorar)...
echo Por favor, aguarde...
pip install --quiet --disable-pip-version-check -r requirements-dev.txt
if errorlevel 1 (
    echo.
    echo ERRO: Falha ao instalar com requirements-dev.txt
    echo Tentando instalar pacotes individualmente...
    pip install Django==4.2.7
    pip install djangorestframework==3.14.0
    pip install djangorestframework-simplejwt==5.3.0
    pip install django-cors-headers==4.3.0
    pip install python-decouple==3.8
    pip install Pillow==10.1.0
    pip install drf-spectacular==0.26.5
)
echo OK - Dependencias instaladas!

echo.
echo [4/7] Criando arquivo .env...
if not exist ".env" (
    copy .env.example .env > nul
    echo OK - Arquivo .env criado!
) else (
    echo Arquivo .env ja existe - OK!
)

echo.
echo [5/7] Criando banco de dados...
python manage.py makemigrations
python manage.py migrate
if errorlevel 1 (
    echo ERRO: Falha ao criar banco de dados
    pause
    exit /b 1
)
echo OK - Banco de dados criado!

echo.
echo [6/7] Populando etapas padrao do sistema...
python manage.py popular_etapas_padrao
if errorlevel 1 (
    echo ERRO: Falha ao popular etapas
    pause
    exit /b 1
)
echo OK - Etapas populadas!

echo.
echo [7/7] Configuracao concluida!
echo.
echo ========================================
echo   SETUP CONCLUIDO COM SUCESSO!
echo ========================================
echo.
echo Proximos passos:
echo.
echo 1. Criar superusuario (admin):
echo    execute: criar_superuser.bat
echo.
echo 2. Rodar o servidor:
echo    execute: rodar_servidor.bat
echo.
echo 3. Acessar o admin:
echo    http://localhost:8000/admin/
echo.
echo 4. Acessar documentacao da API:
echo    http://localhost:8000/api/docs/
echo.
pause


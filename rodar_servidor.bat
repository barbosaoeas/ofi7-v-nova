@echo off
echo ========================================
echo   INICIANDO SERVIDOR DJANGO
echo ========================================
echo.

REM Ativa o ambiente virtual
call venv\Scripts\activate.bat

echo Servidor rodando em: http://localhost:8000/
echo.
echo Para parar o servidor: Pressione Ctrl+C
echo.
echo ========================================
echo   ENDPOINTS DISPONIVEIS:
echo ========================================
echo.
echo - Admin:         http://localhost:8000/admin/
echo - API Docs:      http://localhost:8000/api/docs/
echo - API Schema:    http://localhost:8000/api/schema/
echo.
echo ========================================
echo.

python manage.py runserver


@echo off
echo ========================================
echo   CRIAR SUPERUSUARIO (ADMIN)
echo ========================================
echo.

REM Ativa o ambiente virtual
call venv\Scripts\activate.bat

echo Voce vai criar um usuario administrador.
echo Sera solicitado:
echo   - Username (ex: admin)
echo   - Email (opcional, pode deixar em branco)
echo   - Password (minimo 8 caracteres)
echo   - Password (novamente para confirmar)
echo.

python manage.py createsuperuser

echo.
echo ========================================
echo.
echo Superusuario criado com sucesso!
echo.
echo Acesse: http://localhost:8000/admin/
echo.
pause


@echo off
echo ========================================
echo   INSTALANDO DEPENDENCIAS FRONTEND
echo ========================================
echo.

call venv\Scripts\activate.bat

echo Instalando pacotes...
pip install django-tailwind==3.8.0
pip install django-htmx==1.17.2
pip install django-widget-tweaks==1.5.0

echo.
echo ========================================
echo   INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Proximos passos:
echo 1. Execute: python manage.py tailwind init
echo 2. Execute: python manage.py tailwind install
echo 3. Execute: python manage.py tailwind start
echo.
pause

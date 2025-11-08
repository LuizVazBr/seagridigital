@echo off
REM Script para executar o cliente GUI garantindo que o Python correto seja usado

echo Verificando Python...
python --version

echo.
echo Verificando customtkinter...
python -c "import customtkinter; print('customtkinter OK')" 2>nul
if errorlevel 1 (
    echo customtkinter nao encontrado. Instalando...
    python -m pip install customtkinter
)

echo.
echo Iniciando cliente GUI...
python client.py







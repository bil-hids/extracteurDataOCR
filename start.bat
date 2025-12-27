@echo off
REM Script de démarrage pour Windows

echo ========================================
echo Extracteur de Donnees - Demarrage
echo ========================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou n'est pas dans le PATH
    echo Veuillez installer Python 3.11+ depuis https://www.python.org/
    pause
    exit /b 1
)

echo Installation/Verification des dependances...
python install_dependencies.py

echo.
echo Demarrage du serveur...
echo.
python run.py

pause


@echo off
setlocal
cd /d "%~dp0"

echo.
echo Perseus - preparando ambiente local...
echo.

set "PY_CMD="
where py >nul 2>nul
if %errorlevel%==0 set "PY_CMD=py -3"

if not defined PY_CMD (
  where python >nul 2>nul
  if %errorlevel%==0 set "PY_CMD=python"
)

if not defined PY_CMD (
  echo Python 3 nao foi encontrado neste computador.
  echo Instale o Python 3.12 ou superior e marque a opcao "Add Python to PATH".
  echo Depois execute este arquivo novamente.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual na primeira execucao...
  %PY_CMD% -m venv .venv
  if errorlevel 1 goto :erro
)

set "VPY=.venv\Scripts\python.exe"

"%VPY%" -c "import pdfplumber, openpyxl, reportlab" >nul 2>nul
if errorlevel 1 (
  echo Instalando dependencias do Perseus...
  "%VPY%" -m pip install -r requirements.txt
  if errorlevel 1 goto :erro
)

echo Abrindo o Perseus no navegador...
"%VPY%" app.py
if errorlevel 1 goto :erro
exit /b 0

:erro
echo.
echo Nao foi possivel iniciar o Perseus.
echo Copie a mensagem acima e envie para o suporte do projeto.
pause
exit /b 1

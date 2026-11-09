@echo off
setlocal
cd /d "%~dp0frontend"
where node.exe >nul 2>nul
if errorlevel 1 (
  echo Node.js nao encontrado neste Windows.
  pause
  exit /b 1
)
node --env-file=.env.local scripts\check-local.mjs
if errorlevel 1 (
  pause
  exit /b 1
)
if not exist node_modules\next\package.json (
  echo Instalando a interface. Aguarde...
  call npm.cmd ci
  if errorlevel 1 (
    pause
    exit /b 1
  )
)
echo.
echo Abra http://127.0.0.1:3001/jarvis no navegador.
echo A chave individual esta em ACESSO-LOCAL.txt, na pasta deste pacote.
echo Mantenha esta janela e o Ollama abertos.
echo.
call npm.cmd run dev -- --hostname 127.0.0.1 --port 3001
pause

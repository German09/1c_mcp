@echo off
setlocal EnableExtensions

rem Working directory = folder of this script (proxy/)
cd /d "%~dp0"

if not exist "logs" mkdir "logs"

set "LOG=%~dp0logs\service.log"
echo ===== %DATE% %TIME% starting =====>> "%LOG%"

rem Optional local overrides: copy env.example to .env and edit
if exist "%~dp0.env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%~dp0.env") do (
    if not "%%A"=="" set "%%A=%%B"
  )
)

if "%UPSTREAM_URL%"=="" (
  echo ERROR: UPSTREAM_URL is not set. Create proxy\.env or set AppEnvironmentExtra in NSSM.>> "%LOG%"
  echo ERROR: UPSTREAM_URL is not set.
  exit /b 1
)

if not exist "%~dp0.venv\Scripts\python.exe" (
  echo ERROR: .venv not found at "%~dp0.venv\Scripts\python.exe">> "%LOG%"
  echo ERROR: create venv and install requirements on THIS machine.
  exit /b 1
)

set "PYTHONPATH=%~dp0"
set "PORT=%PORT%"
if "%PORT%"=="" set "PORT=8080"
if "%ANONYMIZATION_ENABLED%"=="" set "ANONYMIZATION_ENABLED=true"
if "%LOG_LEVEL%"=="" set "LOG_LEVEL=INFO"

echo UPSTREAM_URL=%UPSTREAM_URL%>> "%LOG%"
echo PORT=%PORT%>> "%LOG%"
echo Using "%~dp0.venv\Scripts\python.exe">> "%LOG%"

"%~dp0.venv\Scripts\python.exe" -m anonymizing_proxy >> "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo ===== %DATE% %TIME% exited code %RC% =====>> "%LOG%"
exit /b %RC%

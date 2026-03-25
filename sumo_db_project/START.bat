@echo off
REM ============================================================
REM  INICIO RÁPIDO - Sistema de BD para SUMO
REM  San José, Costa Rica
REM ============================================================

echo.
echo ============================================================
echo   Sistema de Base de Datos SUMO - Inicio Rápido
echo ============================================================
echo.

REM Verificar que Docker está corriendo
echo [1/4] Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo  X ERROR: Docker no está instalado o no está corriendo
    echo.
    echo  Instala Docker Desktop desde:
    echo  https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo  √ Docker detectado

REM Levantar los contenedores
echo.
echo [2/4] Iniciando contenedores...
docker-compose up -d
if errorlevel 1 (
    echo  X ERROR: No se pudieron iniciar los contenedores
    pause
    exit /b 1
)
echo  √ Contenedores iniciados

REM Esperar a que la BD esté lista
echo.
echo [3/4] Esperando a que PostgreSQL esté listo...
timeout /t 10 /nobreak >nul
echo  √ PostgreSQL listo

REM Verificar Python
echo.
echo [4/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  ! ADVERTENCIA: Python no detectado
    echo  Descarga Python desde: https://www.python.org/downloads/
) else (
    echo  √ Python detectado
)

echo.
echo ============================================================
echo  TODO LISTO!
echo ============================================================
echo.
echo  Servicios disponibles:
echo   - PostgreSQL:  localhost:5432
echo   - pgAdmin:     http://localhost:5050
echo   - Grafana:     http://localhost:3000
echo.
echo  Credenciales:
echo   - PostgreSQL:  postgres / sumo123
echo   - pgAdmin:     admin@sumo.com / admin123
echo   - Grafana:     admin / admin123
echo.
echo  Próximos pasos:
echo   1. Instala psycopg2: pip install psycopg2-binary
echo   2. Importa tus datos: python sumo_importer.py --dir "ruta\a\archivos" --run-name "Mi_Simulacion"
echo   3. Consulta los datos en pgAdmin: http://localhost:5050
echo.
echo ============================================================

pause

@echo off
REM ============================================================
REM  EJEMPLO: Importar datos de SUMO a PostgreSQL
REM  Ajusta la ruta a tus archivos XML
REM ============================================================

echo.
echo ============================================================
echo   Importando datos de SUMO...
echo ============================================================
echo.

REM AJUSTA ESTA RUTA A DONDE ESTÁN TUS ARCHIVOS XML
set DATA_DIR=C:\BigData\Proyecto_Nube\Simulacion

REM Nombre de la simulación
set RUN_NAME=San_Jose_Barcelona_Test_01

echo Directorio de datos: %DATA_DIR%
echo Nombre de simulación: %RUN_NAME%
echo.

REM Ejecutar el importador
python sumo_importer.py ^
  --dir "%DATA_DIR%" ^
  --run-name "%RUN_NAME%" ^
  --host localhost ^
  --port 5432 ^
  --database sumo_traffic ^
  --user postgres ^
  --password sumo123

if errorlevel 1 (
    echo.
    echo X ERROR en la importación
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  IMPORTACIÓN COMPLETADA!
echo ============================================================
echo.
echo  Ahora puedes:
echo   1. Ver los datos en pgAdmin: http://localhost:5050
echo   2. Ejecutar consultas SQL desde queries.sql
echo   3. Crear dashboards en Grafana: http://localhost:3000
echo.
echo ============================================================

pause

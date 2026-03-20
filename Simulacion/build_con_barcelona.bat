@echo off
REM ============================================================
REM  build_con_barcelona.bat - San Jose CR
REM  Abre con Bloc de Notas y cambia los numeros
REM ============================================================
REM
REM  DENSIDAD por franja (vehiculos/hora/km):
REM    0  = sin vehiculos en esa franja
REM    10 = poco trafico
REM    40 = trafico normal
REM    80 = hora pico
REM ============================================================

REM --- MADRUGADA (00-05h) ---
set D_PASS_MAD=10
set D_MOTO_MAD=5
set D_BUS_MAD=0
set D_TRUCK_MAD=3

REM --- MANANA (05-07h) ---
set D_PASS_MAN=20
set D_MOTO_MAN=10
set D_BUS_MAN=4
set D_TRUCK_MAN=8

REM --- HORA PICO AM (07-09h) ---
set D_PASS_PAM=40
set D_MOTO_PAM=20
set D_BUS_PAM=7
set D_TRUCK_PAM=20

REM --- DIA (09-17h) ---
set D_PASS_DIA=20
set D_MOTO_DIA=10
set D_BUS_DIA=5
set D_TRUCK_DIA=12

REM --- HORA PICO PM (17-19h) ---
set D_PASS_PPM=40
set D_MOTO_PPM=20
set D_BUS_PPM=7
set D_TRUCK_PPM=20

REM --- NOCHE (19-24h) ---
set D_PASS_NOC=20
set D_MOTO_NOC=8
set D_BUS_NOC=2
set D_TRUCK_NOC=5

REM --- FRINGE FACTOR ---
set FRINGE=10

REM ============================================================
REM  NO MODIFICAR NADA DEBAJO DE ESTA LINEA
REM ============================================================

echo.
echo ============================================================
echo  Configuracion:
echo  Pico AM: pass=%D_PASS_PAM%  moto=%D_MOTO_PAM%  bus=%D_BUS_PAM%  truck=%D_TRUCK_PAM%
echo  Pico PM: pass=%D_PASS_PPM%  moto=%D_MOTO_PPM%  bus=%D_BUS_PPM%  truck=%D_TRUCK_PPM%
echo  Dia:     pass=%D_PASS_DIA%  moto=%D_MOTO_DIA%  bus=%D_BUS_DIA%  truck=%D_TRUCK_DIA%
echo  Madrug:  pass=%D_PASS_MAD%  moto=%D_MOTO_MAD%  bus=%D_BUS_MAD%  truck=%D_TRUCK_MAD%
echo ============================================================
echo.

echo [1/5] Generando transporte publico (24h)...
python "%SUMO_HOME%\tools\ptlines2flows.py" -n osm.net.xml.gz -b 0 -e 86400 -p 600 ^
  --random-begin --seed 42 --ptstops osm_stops.add.xml --ptlines osm_ptlines.xml ^
  -o osm_pt.rou.xml --ignore-errors --vtype-prefix pt_ ^
  --stopinfos-file stopinfos.xml --routes-file vehroutes.xml ^
  --trips-file trips.trips.xml --min-stops 0 --extend-to-fringe --verbose

echo [2/5] Generando buses por franjas...
if %D_BUS_MAD% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_BUS_MAD% -o osm.bus.mad.xml -r osm.bus.mad.rou.xml -b 0 -e 18000 --trip-attributes "departLane=\"best\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class bus --vclass bus --prefix busmad --min-distance 600 --seed 42
if %D_BUS_MAN% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_BUS_MAN% -o osm.bus.man.xml -r osm.bus.man.rou.xml -b 18000 -e 25200 --trip-attributes "departLane=\"best\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class bus --vclass bus --prefix busman --min-distance 600 --seed 42
if %D_BUS_PAM% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_BUS_PAM% -o osm.bus.pam.xml -r osm.bus.pam.rou.xml -b 25200 -e 32400 --trip-attributes "departLane=\"best\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class bus --vclass bus --prefix buspam --min-distance 600 --seed 42
if %D_BUS_DIA% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_BUS_DIA% -o osm.bus.dia.xml -r osm.bus.dia.rou.xml -b 32400 -e 61200 --trip-attributes "departLane=\"best\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class bus --vclass bus --prefix busdia --min-distance 600 --seed 42
if %D_BUS_PPM% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_BUS_PPM% -o osm.bus.ppm.xml -r osm.bus.ppm.rou.xml -b 61200 -e 68400 --trip-attributes "departLane=\"best\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class bus --vclass bus --prefix busppm --min-distance 600 --seed 42
if %D_BUS_NOC% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_BUS_NOC% -o osm.bus.noc.xml -r osm.bus.noc.rou.xml -b 68400 -e 86400 --trip-attributes "departLane=\"best\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class bus --vclass bus --prefix busnoc --min-distance 600 --seed 42

echo [3/5] Generando motos por franjas...
if %D_MOTO_MAD% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_MOTO_MAD% -o osm.moto.mad.xml -r osm.moto.mad.rou.xml -b 0 -e 18000 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class motorcycle --vclass motorcycle --prefix motomad --max-distance 1200 --seed 43
if %D_MOTO_MAN% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_MOTO_MAN% -o osm.moto.man.xml -r osm.moto.man.rou.xml -b 18000 -e 25200 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class motorcycle --vclass motorcycle --prefix motoman --max-distance 1200 --seed 43
if %D_MOTO_PAM% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_MOTO_PAM% -o osm.moto.pam.xml -r osm.moto.pam.rou.xml -b 25200 -e 32400 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class motorcycle --vclass motorcycle --prefix motopam --max-distance 1200 --seed 43
if %D_MOTO_DIA% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_MOTO_DIA% -o osm.moto.dia.xml -r osm.moto.dia.rou.xml -b 32400 -e 61200 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class motorcycle --vclass motorcycle --prefix motodia --max-distance 1200 --seed 43
if %D_MOTO_PPM% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_MOTO_PPM% -o osm.moto.ppm.xml -r osm.moto.ppm.rou.xml -b 61200 -e 68400 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class motorcycle --vclass motorcycle --prefix motoppm --max-distance 1200 --seed 43
if %D_MOTO_NOC% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_MOTO_NOC% -o osm.moto.noc.xml -r osm.moto.noc.rou.xml -b 68400 -e 86400 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class motorcycle --vclass motorcycle --prefix motonoc --max-distance 1200 --seed 43

echo [4/5] Generando carros por franjas...
if %D_PASS_MAD% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_PASS_MAD% -o osm.pass.mad.xml -r osm.pass.mad.rou.xml -b 0 -e 18000 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class passenger --vclass passenger --prefix vehmad --min-distance 300 --allow-fringe.min-length 1000 --lanes --seed 44
if %D_PASS_MAN% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_PASS_MAN% -o osm.pass.man.xml -r osm.pass.man.rou.xml -b 18000 -e 25200 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class passenger --vclass passenger --prefix vehman --min-distance 300 --allow-fringe.min-length 1000 --lanes --seed 44
if %D_PASS_PAM% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_PASS_PAM% -o osm.pass.pam.xml -r osm.pass.pam.rou.xml -b 25200 -e 32400 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class passenger --vclass passenger --prefix vehpam --min-distance 300 --allow-fringe.min-length 1000 --lanes --seed 44
if %D_PASS_DIA% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_PASS_DIA% -o osm.pass.dia.xml -r osm.pass.dia.rou.xml -b 32400 -e 61200 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class passenger --vclass passenger --prefix vehdia --min-distance 300 --allow-fringe.min-length 1000 --lanes --seed 44
if %D_PASS_PPM% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_PASS_PPM% -o osm.pass.ppm.xml -r osm.pass.ppm.rou.xml -b 61200 -e 68400 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class passenger --vclass passenger --prefix vehppm --min-distance 300 --allow-fringe.min-length 1000 --lanes --seed 44
if %D_PASS_NOC% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_PASS_NOC% -o osm.pass.noc.xml -r osm.pass.noc.rou.xml -b 68400 -e 86400 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class passenger --vclass passenger --prefix vehnoc --min-distance 300 --allow-fringe.min-length 1000 --lanes --seed 44

echo [5/5] Generando camiones por franjas...
if %D_TRUCK_MAD% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_TRUCK_MAD% -o osm.truck.mad.xml -r osm.truck.mad.rou.xml -b 0 -e 18000 --trip-attributes "departLane=\"best\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class truck --vclass truck --prefix truckmad --min-distance 600 --seed 45
if %D_TRUCK_MAN% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_TRUCK_MAN% -o osm.truck.man.xml -r osm.truck.man.rou.xml -b 18000 -e 25200 --trip-attributes "departLane=\"best\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class truck --vclass truck --prefix truckman --min-distance 600 --seed 45
if %D_TRUCK_PAM% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_TRUCK_PAM% -o osm.truck.pam.xml -r osm.truck.pam.rou.xml -b 25200 -e 32400 --trip-attributes "departLane=\"best\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class truck --vclass truck --prefix truckpam --min-distance 600 --seed 45
if %D_TRUCK_DIA% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_TRUCK_DIA% -o osm.truck.dia.xml -r osm.truck.dia.rou.xml -b 32400 -e 61200 --trip-attributes "departLane=\"best\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class truck --vclass truck --prefix truckdia --min-distance 600 --seed 45
if %D_TRUCK_PPM% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_TRUCK_PPM% -o osm.truck.ppm.xml -r osm.truck.ppm.rou.xml -b 61200 -e 68400 --trip-attributes "departLane=\"best\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class truck --vclass truck --prefix truckppm --min-distance 600 --seed 45
if %D_TRUCK_NOC% GTR 0 python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml.gz --fringe-factor %FRINGE% --insertion-density %D_TRUCK_NOC% -o osm.truck.noc.xml -r osm.truck.noc.rou.xml -b 68400 -e 86400 --trip-attributes "departLane=\"best\"" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class truck --vclass truck --prefix trucknoc --min-distance 600 --seed 45

echo.
echo ============================================================
echo  Listo! Ahora ejecuta: run.bat
echo ============================================================
pause

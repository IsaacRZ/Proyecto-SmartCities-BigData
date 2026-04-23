# 🚀 GUÍA RÁPIDA DE INSTALACIÓN
## Sistema de Base de Datos para SUMO - 5 Minutos

---

## ⚡ Instalación Ultra Rápida

### Paso 1: Instalar Docker Desktop (5 min)
1. Descargar: https://www.docker.com/products/docker-desktop/
2. Instalar (siguiente, siguiente, finalizar)
3. Reiniciar PC
4. Abrir Docker Desktop y esperar a que inicie

### Paso 2: Extraer el Proyecto (30 seg)
1. Descomprimir `sumo_db_project.zip`
2. Abrir carpeta en el explorador

### Paso 3: Iniciar Todo (2 min)
1. Hacer doble clic en: **START.bat**
2. Esperar a que termine (~1-2 minutos primera vez)
3. ¡Listo! ✅

---

## 📊 Importar tus Datos de SUMO

### Opción A: Script Rápido
1. Editar `IMPORT_EXAMPLE.bat`
2. Cambiar esta línea:
   ```batch
   set DATA_DIR=C:\TU\RUTA\A\ARCHIVOS\XML
   ```
3. Hacer doble clic en `IMPORT_EXAMPLE.bat`

### Opción B: Línea de Comandos
```bash
# Instalar dependencia
pip install psycopg2-binary

# Importar
python sumo_importer.py --dir "C:\ruta\a\tus\archivos" --run-name "Mi_Simulacion"
```

---

## 🔍 Ver tus Datos

### pgAdmin (Interfaz Gráfica)
1. Abrir: http://localhost:5050
2. Login: `admin@sumo.com` / `admin123`
3. Add Server:
   - Name: `SUMO Traffic`
   - Host: `timescaledb`
   - Port: `5432`
   - Database: `sumo_traffic`
   - User: `postgres`
   - Password: `sumo123`
4. Explorar tablas en: Servers → SUMO Traffic → Databases → sumo_traffic → Schemas → public → Tables

### Consultas SQL
- Abrir `queries.sql` para ver +50 consultas útiles
- Copiar y pegar en pgAdmin

### Grafana (Dashboards)
1. Abrir: http://localhost:3000
2. Login: `admin` / `admin123`
3. Seguir guía en `GRAFANA_SETUP.md`

---

## 📁 Archivos Importantes

| Archivo | Descripción |
|---------|-------------|
| `START.bat` | Inicia todo automáticamente |
| `IMPORT_EXAMPLE.bat` | Ejemplo de importación |
| `sumo_importer.py` | Script principal de importación |
| `queries.sql` | +50 consultas SQL útiles |
| `README.md` | Documentación completa |
| `GRAFANA_SETUP.md` | Cómo crear dashboards |
| `docker-compose.yml` | Configuración de Docker |

---

## 🎯 Archivos XML que se Procesan

Tu simulación SUMO genera estos archivos que el sistema importa:

✅ **tripinfos.xml** → Tabla `vehicle_trips`
- Información de cada viaje completado
- Duración, velocidad, distancia, tiempos de espera

✅ **edgeData.xml** → Tabla `edge_data`
- Datos por calle/carretera
- Velocidades, densidad, ocupación

✅ **stats.xml** → Tabla `simulation_stats`
- Estadísticas globales de la simulación
- Vehículos activos, colisiones, teleports

✅ **stopinfos.xml** → Tabla `pt_stops`
- Paradas de transporte público
- Pasajeros, retrasos

---

## 🔧 Comandos Útiles

```bash
# Ver estado de contenedores
docker ps

# Ver logs
docker-compose logs -f

# Detener todo (datos se mantienen)
docker-compose down

# Reiniciar
docker-compose up -d

# BORRAR TODO (incluyendo datos)
docker-compose down -v
```

---

## 💡 Consultas SQL de Ejemplo

### Ver últimos viajes
```sql
SELECT vehicle_id, vehicle_type, period, duration, avg_speed
FROM vehicle_trips
ORDER BY time DESC
LIMIT 20;
```

### Tráfico por franja horaria
```sql
SELECT * FROM traffic_by_period;
```

### Calles congestionadas
```sql
SELECT * FROM congested_streets LIMIT 10;
```

### Comparar hora pico AM vs PM
```sql
SELECT period, COUNT(*) as viajes, 
       AVG(waiting_time) as espera_promedio
FROM vehicle_trips
WHERE period IN ('PICO_AM', 'PICO_PM')
GROUP BY period;
```

---

## 🆘 Solución de Problemas

### Docker no inicia
```bash
wsl --update
```

### Error "port 5432 already in use"
- Tienes PostgreSQL instalado localmente
- Opción 1: Detener PostgreSQL local
- Opción 2: Cambiar puerto en `docker-compose.yml`:
  ```yaml
  ports:
    - "5433:5432"  # Usar 5433 en vez de 5432
  ```

### Python no reconocido
- Instalar desde: https://www.python.org/downloads/
- Marcar: ☑ "Add Python to PATH"

### psycopg2 error
```bash
pip install psycopg2-binary
```

---

## 🌐 Deployment en Cloud (Gratis)

### Oracle Cloud (Recomendado)
- 2 VMs gratis PARA SIEMPRE
- 200GB almacenamiento
- Guía completa en `README.md` sección 10

### AWS Free Tier
- 12 meses gratis
- t2.micro

### Google Cloud
- $300 créditos iniciales
- e2-micro siempre gratis

---

## 📊 Estructura de Datos

### Tablas Principales
- `vehicle_trips` - Viajes completados (TIME-SERIES)
- `edge_data` - Datos por calle (TIME-SERIES)
- `simulation_stats` - Estadísticas globales (TIME-SERIES)
- `pt_stops` - Paradas de buses (TIME-SERIES)
- `simulation_runs` - Registro de simulaciones
- `vehicle_types` - Tipos de vehículos
- `time_periods` - Franjas horarias

### Vistas Útiles
- `traffic_by_period` - Tráfico por franja horaria
- `congested_streets` - Top calles congestionadas
- `simulation_summary` - Resumen de simulaciones

---

## ✅ Checklist de Verificación

- [ ] Docker Desktop instalado y corriendo
- [ ] Proyecto descomprimido
- [ ] `START.bat` ejecutado sin errores
- [ ] pgAdmin abierto en http://localhost:5050
- [ ] Conexión a BD creada en pgAdmin
- [ ] Python instalado
- [ ] psycopg2-binary instalado
- [ ] Datos importados con `sumo_importer.py`
- [ ] Consultas SQL funcionando
- [ ] (Opcional) Grafana configurado

---

## 📧 Para tu Proyecto Académico

### Documentación Sugerida
1. **Introducción**: Problema de tráfico en San José
2. **Metodología**: SUMO + PostgreSQL/TimescaleDB
3. **Implementación**: Capturas de pgAdmin, código SQL
4. **Resultados**: Gráficas, consultas, insights
5. **Conclusiones**: Análisis de franjas horarias

### Gráficas Recomendadas
- Vehículos activos por minuto (línea)
- Velocidad promedio por hora (barras)
- Tráfico por tipo de vehículo (pie)
- Comparación pico AM vs PM (tabla)
- Top 10 calles congestionadas (barras horizontales)

### Capturas de Pantalla Útiles
- pgAdmin mostrando tablas con datos
- Consulta SQL con resultados
- Dashboard de Grafana (si aplica)
- Docker Desktop con contenedores corriendo

---

## 🎓 Recursos Adicionales

- **Documentación SUMO**: https://sumo.dlr.de/docs/
- **TimescaleDB Docs**: https://docs.timescale.com/
- **PostgreSQL Tutorial**: https://www.postgresqltutorial.com/
- **Grafana Docs**: https://grafana.com/docs/

---

**¡Éxito con tu proyecto! 🚀**

Si tienes dudas:
1. Revisa `README.md` (documentación completa)
2. Consulta `queries.sql` (ejemplos de consultas)
3. Lee `GRAFANA_SETUP.md` (si usas visualización)

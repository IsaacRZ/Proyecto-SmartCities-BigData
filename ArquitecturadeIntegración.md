## 🏗️ Arquitectura de Integración

### **Batch Layer → Barcelona Open Data (Datos Históricos Reales)**
URL del dataset: https://opendata-ajuntament.barcelona.cat/data/es/dataset/trams
Fecha de descarga: 18 de Febrero 2026

```
Barcelona Sensors (Real)
    ↓
6 meses de datos históricos
    ↓
PySpark Batch Processing
    ↓
Genera:
- Baselines estadísticos (promedio vehículos por hora/día)
- Patrones de congestión (distribuciones reales)
- Modelos ML entrenados con datos REALES
- Vistas materializadas en BigQuery
```

### **Speed Layer → SUMO San José (Simulación Calibrada)**

```
SUMO Simulator (San José, CR)
    ↓
Calibrado con patrones de Barcelona
    ↓
Genera eventos streaming cada 10 seg
    ↓
PySpark Streaming consume eventos
    ↓
Aplica modelos entrenados con Barcelona
    ↓
Predicciones en tiempo real → BigQuery
```


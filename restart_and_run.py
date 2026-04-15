#!/usr/bin/env python3
"""
Reinicia el kernel de Jupyter y ejecuta FASE 1

Uso: python restart_and_run.py
"""

import os
import sys
import subprocess
import time

print("="*70)
print("🔄 REINICIANDO KERNEL Y EJECUTANDO FASE 1")
print("="*70)

# Cambiar directorio
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Opción 1: Usar jupyter nbconvert para reiniciar
print("\n1️⃣ Opción: Usando nbconvert para reiniciar kernel...")
notebook_path = "notebooks/03_smart_cities_pipeline.ipynb"

# Reiniciar el kernel y ejecutar solo celdas 1-5 (FASE 1)
cmd = [
    "jupyter", "nbconvert",
    "--to", "notebook",
    "--execute",
    "--ExecutePreprocessor.timeout=300",
    "--output", notebook_path,
    notebook_path
]

print(f"Ejecutando: {' '.join(cmd)}\n")
try:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ Notebook ejecutado exitosamente")
        print("\nOutput:")
        print(result.stdout)
    else:
        print("❌ Error ejecutando notebook:")
        print(result.stderr)
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print("\n2️⃣ Opción alternativa: Reinicia manualmente")
    print("   - En Jupyter: Kernel → Restart Kernel")
    print("   - Luego ejecuta los cells en orden")

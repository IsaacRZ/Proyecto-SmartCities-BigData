#!/usr/bin/env python3
"""
Setup de Hadoop para Windows - Descarga winutils.exe necesario para Spark
Ejecutar: python scripts/setup_windows_hadoop.py
"""

import os
import sys
import urllib.request
from pathlib import Path

def setup_hadoop_windows():
    """Configura HADOOP_HOME con winutils para Spark en Windows"""

    if sys.platform != "win32":
        print("✓ Este script es solo para Windows")
        return True

    # Versión de Hadoop compatible con Spark 3.x
    HADOOP_VERSION = "3.2.2"

    # Directorio base
    hadoop_home = Path(os.environ.get("USERPROFILE", "C:\\Users\\Default")) / ".hadoop" / f"hadoop-{HADOOP_VERSION}"
    bin_dir = hadoop_home / "bin"

    print(f"Instalando Hadoop {HADOOP_VERSION} en: {hadoop_home}")

    # Crear directorios
    bin_dir.mkdir(parents=True, exist_ok=True)

    # URLs para winutils
    winutils_url = f"https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-{HADOOP_VERSION}/bin/winutils.exe"
    hadoop_url = f"https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-{HADOOP_VERSION}/bin/hadoop.dll"

    # Descargar winutils.exe
    winutils_path = bin_dir / "winutils.exe"
    if not winutils_path.exists():
        print(f"Descargando winutils.exe...")
        try:
            urllib.request.urlretrieve(winutils_url, winutils_path)
            print(f"[OK] winutils.exe descargado")
        except Exception as e:
            print(f"[ERROR] Error descargando winutils.exe: {e}")
            print(f"  Descarga manual desde: {winutils_url}")
            return False
    else:
        print(f"[OK] winutils.exe ya existe")

    # Descargar hadoop.dll
    hadoop_dll_path = bin_dir / "hadoop.dll"
    if not hadoop_dll_path.exists():
        print(f"Descargando hadoop.dll...")
        try:
            urllib.request.urlretrieve(hadoop_url, hadoop_dll_path)
            print(f"[OK] hadoop.dll descargado")
        except Exception as e:
            print(f"[ERROR] Error descargando hadoop.dll: {e}")
            return False
    else:
        print(f"[OK] hadoop.dll ya existe")

    # Configurar variables de entorno
    os.environ["HADOOP_HOME"] = str(hadoop_home)
    os.environ["hadoop.home.dir"] = str(hadoop_home)

    # Agregar al PATH
    current_path = os.environ.get("PATH", "")
    if str(bin_dir) not in current_path:
        os.environ["PATH"] = str(bin_dir) + ";" + current_path

    print("\n" + "="*60)
    print("[OK] HADOOP_HOME configurado exitosamente")
    print(f"  HADOOP_HOME = {hadoop_home}")
    print(f"  PATH actualizado con: {bin_dir}")
    print("="*60)

    # Guardar configuración persistente (.env)
    env_file = Path(__file__).parent.parent / ".env"
    env_content = f"""# Configuración de Hadoop para Windows
# Generado automaticmente por setup_windows_hadoop.py
HADOOP_HOME={hadoop_home}
hadoop.home.dir={hadoop_home}
PATH={bin_dir};%PATH%
"""
    env_file.write_text(env_content)
    print(f"\n[OK] Configuracion guardada en: {env_file}")

    print("\nPróximos pasos:")
    print("  1. Reinicia tu terminal o ejecuta: setx HADOOP_HOME " + str(hadoop_home))
    print("  2. Ejecuta: setx PATH " + str(bin_dir) + ";%PATH%")
    print("  3. Vuelve a ejecutar: python run_pipeline.py")

    return True

if __name__ == "__main__":
    success = setup_hadoop_windows()
    sys.exit(0 if success else 1)

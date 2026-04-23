
# Script para agregar tipos de vehículos dinámicamente desde archivos XML de SUMO


import xml.etree.ElementTree as ET
import psycopg2
from pathlib import Path
import argparse

def extract_vehicle_types(xml_dir):
    # Extraer todos los tipos de vehículos de los XMLs
    vtypes = set()
    
    # Buscar en todos los archivos .xml
    for xml_file in Path(xml_dir).glob('*.xml'):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Buscar vTypes en diferentes estructuras
            for vtype in root.findall('.//vType'):
                vtype_id = vtype.get('id')
                if vtype_id:
                    vtypes.add(vtype_id)
            
            # Buscar types en trips
            for trip in root.findall('.//trip'):
                vtype = trip.get('type')
                if vtype:
                    vtypes.add(vtype)
                    
            # Buscar en tripinfo
            for tripinfo in root.findall('.//tripinfo'):
                vtype = tripinfo.get('vType')
                if vtype:
                    vtypes.add(vtype)
                    
        except Exception as e:
            continue
    
    return vtypes

def insert_vehicle_types(vtypes, db_config):
    # Insertar tipos de vehículos en la base de datos
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    
    # Mapeo de prefijos a vclass
    vclass_mapping = {
        'moto': 'motorcycle',
        'bus': 'bus',
        'veh': 'passenger',
        'truck': 'truck',
        'pt_': 'bus',
    }
    
    inserted = 0
    for vtype_id in vtypes:
        # Determinar vclass basado en el nombre
        vclass = 'passenger'  # default
        for prefix, vc in vclass_mapping.items():
            if vtype_id.startswith(prefix):
                vclass = vc
                break
        
        try:
            cur.execute("""
                INSERT INTO vehicle_types (vtype_id, vclass, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (vtype_id) DO NOTHING
            """, (vtype_id, vclass, f'Tipo generado automáticamente: {vtype_id}'))
            
            if cur.rowcount > 0:
                inserted += 1
                print(f"  ✓ Agregado: {vtype_id} ({vclass})")
        except Exception as e:
            print(f"  ✗ Error con {vtype_id}: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    return inserted

def main():
    parser = argparse.ArgumentParser(description='Agregar tipos de vehículos desde XMLs de SUMO')
    parser.add_argument('--dir', required=True, help='Directorio con archivos XML')
    parser.add_argument('--host', default='localhost', help='Host de PostgreSQL')
    parser.add_argument('--port', default='5432', help='Puerto de PostgreSQL')
    parser.add_argument('--database', default='sumo_traffic', help='Nombre de la base de datos')
    parser.add_argument('--user', default='postgres', help='Usuario de PostgreSQL')
    parser.add_argument('--password', default='sumo123', help='Contraseña de PostgreSQL')
    
    args = parser.parse_args()
    
    db_config = {
        'host': args.host,
        'port': args.port,
        'database': args.database,
        'user': args.user,
        'password': args.password
    }
    
    print(f"→ Buscando tipos de vehículos en {args.dir}...")
    vtypes = extract_vehicle_types(args.dir)
    
    print(f"\n✓ Encontrados {len(vtypes)} tipos de vehículos")
    
    print(f"\n→ Insertando tipos en la base de datos...")
    inserted = insert_vehicle_types(vtypes, db_config)
    
    print(f"\n✓ {inserted} tipos nuevos agregados")
    print(f"✓ Total en sistema: {len(vtypes)}")

if __name__ == '__main__':
    main()
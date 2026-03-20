"""
SUMO XML Parser - Importador de Datos de Simulación a PostgreSQL
Procesa archivos XML generados por SUMO y los almacena en TimescaleDB
"""

import xml.etree.ElementTree as ET
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime, timedelta
import gzip
import os
from pathlib import Path
from typing import List, Dict, Optional
import argparse


class SUMODatabaseImporter:
    """Importador de datos XML de SUMO a PostgreSQL/TimescaleDB"""
    
    def __init__(self, db_config: Dict[str, str]):
        """
        Inicializar conexión a la base de datos
        
        Args:
            db_config: Diccionario con host, database, user, password, port
        """
        self.conn = psycopg2.connect(**db_config)
        self.cur = self.conn.cursor()
        self.run_id = None
        self.simulation_start = datetime.now()
        
    def create_simulation_run(self, run_name: str, config_file: Optional[str] = None) -> int:
        """Crear un nuevo registro de simulación"""
        self.cur.execute("""
            INSERT INTO simulation_runs (run_name, start_time, config_file, status)
            VALUES (%s, %s, %s, 'running')
            RETURNING run_id
        """, (run_name, self.simulation_start, config_file))
        self.run_id = self.cur.fetchone()[0]
        self.conn.commit()
        print(f"✓ Simulación creada: run_id={self.run_id}, name={run_name}")
        return self.run_id
    
    def get_time_period(self, seconds: float) -> str:
        """Determinar franja horaria desde segundos de simulación"""
        hour = int(seconds // 3600) % 24
        
        if 0 <= hour < 5:
            return 'MADRUGADA'
        elif 5 <= hour < 7:
            return 'MAÑANA'
        elif 7 <= hour < 9:
            return 'PICO_AM'
        elif 9 <= hour < 17:
            return 'DIA'
        elif 17 <= hour < 19:
            return 'PICO_PM'
        else:
            return 'NOCHE'
    
    def parse_tripinfo(self, xml_file: str, batch_size: int = 1000):
        """
        Parsear tripinfo.xml - Información de viajes completados
        
        Args:
            xml_file: Ruta al archivo tripinfo.xml
            batch_size: Tamaño de lote para inserciones
        """
        print(f"\n→ Procesando {xml_file}...")
        
        if not os.path.exists(xml_file):
            print(f"  ⚠ Archivo no encontrado: {xml_file}")
            return
        
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        trips = []
        for tripinfo in root.findall('.//tripinfo'):
            depart = float(tripinfo.get('depart', 0))
            timestamp = self.simulation_start + timedelta(seconds=depart)
            
            trip = (
                timestamp,                                    # time
                self.run_id,                                  # run_id
                tripinfo.get('id'),                          # vehicle_id
                tripinfo.get('vType'),                       # vehicle_type
                depart,                                      # depart_time
                float(tripinfo.get('arrival', depart)),     # arrival_time
                float(tripinfo.get('duration', 0)),         # duration
                float(tripinfo.get('routeLength', 0)),      # route_length
                float(tripinfo.get('waitingTime', 0)),      # waiting_time
                float(tripinfo.get('timeLoss', 0)),         # time_loss
                float(tripinfo.get('departDelay', 0)),      # depart_delay
                tripinfo.get('departLane'),                  # depart_lane
                tripinfo.get('fromEdge'),                    # from_edge
                tripinfo.get('toEdge'),                      # to_edge
                float(tripinfo.get('maxSpeed', 0)),         # max_speed
                float(tripinfo.get('routeLength', 0)) / max(float(tripinfo.get('duration', 1)), 1),  # avg_speed
                self.get_time_period(depart),                # period
                True                                          # completed
            )
            trips.append(trip)
            
            if len(trips) >= batch_size:
                self._insert_trips_batch(trips)
                trips = []
        
        if trips:
            self._insert_trips_batch(trips)
        
        print(f"  ✓ Viajes procesados exitosamente")
    
    def _insert_trips_batch(self, trips: List[tuple]):
        """Insertar lote de viajes"""
        execute_batch(self.cur, """
            INSERT INTO vehicle_trips (
                time, run_id, vehicle_id, vehicle_type, depart_time,
                arrival_time, duration, route_length, waiting_time,
                time_loss, depart_delay, depart_lane, from_edge, to_edge,
                max_speed, avg_speed, period, completed
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, trips)
        self.conn.commit()
    
    def parse_edge_data(self, xml_file: str, batch_size: int = 1000):
        """
        Parsear edgeData.xml - Datos agregados por calle
        
        Args:
            xml_file: Ruta al archivo edgeData.xml
            batch_size: Tamaño de lote para inserciones
        """
        print(f"\n→ Procesando {xml_file}...")
        
        if not os.path.exists(xml_file):
            print(f"  ⚠ Archivo no encontrado: {xml_file}")
            return
        
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        edges = []
        for interval in root.findall('.//interval'):
            begin = float(interval.get('begin', 0))
            timestamp = self.simulation_start + timedelta(seconds=begin)
            
            for edge in interval.findall('edge'):
                edge_data = (
                    timestamp,                                  # time
                    self.run_id,                               # run_id
                    edge.get('id'),                           # edge_id
                    begin,                                     # interval_begin
                    float(interval.get('end', begin)),        # interval_end
                    int(edge.get('sampledSeconds', 0)),       # num_vehicles (aprox)
                    float(edge.get('speed', 0)),              # avg_speed
                    float(edge.get('occupancy', 0)),          # avg_occupancy
                    float(edge.get('density', 0)),            # avg_density
                    float(edge.get('waitingTime', 0)),        # avg_waiting_time
                    float(edge.get('traveltime', 0)),         # total_travel_time
                    float(edge.get('CO2_abs', 0)),            # total_co2
                    float(edge.get('fuel_abs', 0))            # total_fuel
                )
                edges.append(edge_data)
                
                if len(edges) >= batch_size:
                    self._insert_edges_batch(edges)
                    edges = []
        
        if edges:
            self._insert_edges_batch(edges)
        
        print(f"  ✓ Datos de calles procesados exitosamente")
    
    def _insert_edges_batch(self, edges: List[tuple]):
        """Insertar lote de datos de calles"""
        execute_batch(self.cur, """
            INSERT INTO edge_data (
                time, run_id, edge_id, interval_begin, interval_end,
                num_vehicles, avg_speed, avg_occupancy, avg_density,
                avg_waiting_time, total_travel_time, total_co2, total_fuel
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, edges)
        self.conn.commit()
    
    def parse_stats(self, xml_file: str):
        """
        Parsear stats.xml - Estadísticas generales de simulación
        
        Args:
            xml_file: Ruta al archivo stats.xml
        """
        print(f"\n→ Procesando {xml_file}...")
        
        if not os.path.exists(xml_file):
            print(f"  ⚠ Archivo no encontrado: {xml_file}")
            return
        
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Datos de performance
        perf = root.find('.//performance')
        if perf is not None:
            begin = float(perf.get('begin', 0))
            timestamp = self.simulation_start + timedelta(seconds=begin)
            
            # Vehículos
            vehicles = root.find('.//vehicles')
            teleports = root.find('.//teleports')
            safety = root.find('.//safety')
            trip_stats = root.find('.//vehicleTripStatistics')
            
            self.cur.execute("""
                INSERT INTO simulation_stats (
                    time, run_id, timestep,
                    vehicles_loaded, vehicles_inserted, vehicles_running, vehicles_waiting,
                    teleports_total, teleports_jam, teleports_yield,
                    collisions, emergency_stops, emergency_braking,
                    avg_route_length, avg_speed, avg_duration, 
                    avg_waiting_time, avg_time_loss, total_travel_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                timestamp,
                self.run_id,
                begin,
                int(vehicles.get('loaded', 0)) if vehicles is not None else 0,
                int(vehicles.get('inserted', 0)) if vehicles is not None else 0,
                int(vehicles.get('running', 0)) if vehicles is not None else 0,
                int(vehicles.get('waiting', 0)) if vehicles is not None else 0,
                int(teleports.get('total', 0)) if teleports is not None else 0,
                int(teleports.get('jam', 0)) if teleports is not None else 0,
                int(teleports.get('yield', 0)) if teleports is not None else 0,
                int(safety.get('collisions', 0)) if safety is not None else 0,
                int(safety.get('emergencyStops', 0)) if safety is not None else 0,
                int(safety.get('emergencyBraking', 0)) if safety is not None else 0,
                float(trip_stats.get('routeLength', 0)) if trip_stats is not None else 0,
                float(trip_stats.get('speed', 0)) if trip_stats is not None else 0,
                float(trip_stats.get('duration', 0)) if trip_stats is not None else 0,
                float(trip_stats.get('waitingTime', 0)) if trip_stats is not None else 0,
                float(trip_stats.get('timeLoss', 0)) if trip_stats is not None else 0,
                float(trip_stats.get('totalTravelTime', 0)) if trip_stats is not None else 0
            ))
            self.conn.commit()
        
        print(f"  ✓ Estadísticas procesadas exitosamente")
    
    def parse_stopinfos(self, xml_file: str, batch_size: int = 1000):
        """
        Parsear stopinfos.xml - Paradas de transporte público
        
        Args:
            xml_file: Ruta al archivo stopinfos.xml
            batch_size: Tamaño de lote para inserciones
        """
        print(f"\n→ Procesando {xml_file}...")
        
        if not os.path.exists(xml_file):
            print(f"  ⚠ Archivo no encontrado: {xml_file}")
            return
        
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        stops = []
        for stopinfo in root.findall('.//stopinfo'):
            started = float(stopinfo.get('started', 0))
            timestamp = self.simulation_start + timedelta(seconds=started)
            
            stop = (
                timestamp,                                    # time
                self.run_id,                                  # run_id
                stopinfo.get('id'),                          # stop_id
                stopinfo.get('vehicleID'),                   # vehicle_id
                started,                                      # started
                float(stopinfo.get('ended', started)),       # ended
                float(stopinfo.get('delay', 0)),             # delay
                int(stopinfo.get('initialPersons', 0)),      # passengers_boarding (aprox)
                0,                                            # passengers_alighting
                int(stopinfo.get('loadedPersons', 0))        # passengers_loaded
            )
            stops.append(stop)
            
            if len(stops) >= batch_size:
                self._insert_stops_batch(stops)
                stops = []
        
        if stops:
            self._insert_stops_batch(stops)
        
        print(f"  ✓ Paradas de transporte público procesadas")
    
    def _insert_stops_batch(self, stops: List[tuple]):
        """Insertar lote de paradas"""
        execute_batch(self.cur, """
            INSERT INTO pt_stops (
                time, run_id, stop_id, vehicle_id, started, ended,
                delay, passengers_boarding, passengers_alighting, passengers_loaded
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, stops)
        self.conn.commit()
    
    def finalize_simulation(self):
        """Marcar simulación como completada"""
        if self.run_id:
            self.cur.execute("""
                UPDATE simulation_runs
                SET end_time = %s, status = 'completed'
                WHERE run_id = %s
            """, (datetime.now(), self.run_id))
            self.conn.commit()
            print(f"\n✓ Simulación {self.run_id} finalizada")
    
    def close(self):
        """Cerrar conexión"""
        self.cur.close()
        self.conn.close()


def main():
    """Función principal - CLI"""
    parser = argparse.ArgumentParser(
        description='Importar datos de simulación SUMO a PostgreSQL/TimescaleDB'
    )
    parser.add_argument('--dir', required=True, help='Directorio con archivos XML de SUMO')
    parser.add_argument('--run-name', required=True, help='Nombre de la simulación')
    parser.add_argument('--host', default='localhost', help='Host de PostgreSQL')
    parser.add_argument('--port', default='5432', help='Puerto de PostgreSQL')
    parser.add_argument('--database', default='sumo_traffic', help='Nombre de la base de datos')
    parser.add_argument('--user', default='postgres', help='Usuario de PostgreSQL')
    parser.add_argument('--password', default='sumo123', help='Contraseña de PostgreSQL')
    
    args = parser.parse_args()
    
    # Configuración de BD
    db_config = {
        'host': args.host,
        'port': args.port,
        'database': args.database,
        'user': args.user,
        'password': args.password
    }
    
    # Inicializar importador
    importer = SUMODatabaseImporter(db_config)
    
    try:
        # Crear registro de simulación
        importer.create_simulation_run(args.run_name)
        
        # Buscar y procesar archivos
        data_dir = Path(args.dir)
        
        # Procesar archivos en orden
        files_to_process = {
            'tripinfos.xml': importer.parse_tripinfo,
            'edgeData.xml': importer.parse_edge_data,
            'stats.xml': importer.parse_stats,
            'stopinfos.xml': importer.parse_stopinfos
        }
        
        for filename, parse_func in files_to_process.items():
            file_path = data_dir / filename
            if file_path.exists():
                parse_func(str(file_path))
            else:
                print(f"⚠ Archivo no encontrado: {filename}")
        
        # Finalizar
        importer.finalize_simulation()
        
        print("\n" + "="*60)
        print("✓ IMPORTACIÓN COMPLETADA EXITOSAMENTE")
        print("="*60)
        print(f"\nPuedes ver los datos con:")
        print(f"  psql -h {args.host} -U {args.user} -d {args.database}")
        print(f"\nO conectarte a pgAdmin en http://localhost:5050")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        importer.close()


if __name__ == '__main__':
    main()

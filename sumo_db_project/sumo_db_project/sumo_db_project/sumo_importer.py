import xml.etree.ElementTree as ET
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import sys

class SumoImporter:
    def __init__(self, db_config):
        self.conn = psycopg2.connect(**db_config)
        self.cur = self.conn.cursor()
        self.run_id = None
        self.simulation_start = datetime.now()
        
    def create_simulation_run(self, run_name, config_file=None):
        # Crear registro de simulación
        self.cur.execute("""
            INSERT INTO simulation_runs (run_name, start_time, config_file, status)
            VALUES (%s, %s, %s, 'running')
            RETURNING run_id
        """, (run_name, self.simulation_start, config_file))
        
        self.run_id = self.cur.fetchone()[0]
        self.conn.commit()
        print(f"✓ Simulación creada: run_id={self.run_id}, name={run_name}")
        
    def get_period(self, hour):
        # Determinar período del día
        if 0 <= hour < 5: return 'MADRUGADA'
        elif 5 <= hour < 7: return 'MAÑANA'
        elif 7 <= hour < 9: return 'PICO_AM'
        elif 9 <= hour < 17: return 'DIA'
        elif 17 <= hour < 19: return 'PICO_PM'
        else: return 'NOCHE'
    
    def safe_float(self, value, default=0.0):
        if value is None or value == '': return default
        try: return float(value)
        except (ValueError, TypeError): return default
    
    def safe_int(self, value, default=0):
        if value is None or value == '': return default
        try: return int(float(value))
        except (ValueError, TypeError): return default
    
    def safe_bool(self, value):
        if value is None: return False
        return str(value).lower() in ('true', '1', 'yes')

    def parse_tripinfo(self, xml_file):
        """Parsear tripinfos.xml"""
        print(f"→ Procesando {xml_file}...")
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            trips = []
            for tripinfo in root.findall('tripinfo'):
                depart = self.safe_float(tripinfo.get('depart'))
                trip_time = self.simulation_start + timedelta(seconds=depart)
                trip_data = (
                    trip_time, self.run_id, tripinfo.get('id', 'unknown'),
                    tripinfo.get('vType', 'unknown'), depart,
                    self.safe_float(tripinfo.get('arrival')), self.safe_float(tripinfo.get('duration')),
                    self.safe_float(tripinfo.get('routeLength')), self.safe_float(tripinfo.get('waitingTime')),
                    self.safe_float(tripinfo.get('timeLoss')), self.safe_float(tripinfo.get('speedFactor', 1.0)),
                    self.safe_float(tripinfo.get('vaporized', 0)), depart,
                    self.safe_float(tripinfo.get('arrival')), self.safe_bool(tripinfo.get('vaporized')),
                    self.get_period(trip_time.hour), self.safe_float(tripinfo.get('departDelay')),
                    self.safe_float(tripinfo.get('stopTime'))
                )
                trips.append(trip_data)
            if trips: self._insert_trips_batch(trips)
        except Exception as e: print(f"  ✗ Error en tripinfo: {e}")

    def _insert_trips_batch(self, trips):
        execute_batch(self.cur, """
            INSERT INTO vehicle_trips (
                time, run_id, vehicle_id, vehicle_type, depart, arrival, duration,
                route_length, waiting_time, time_loss, avg_speed, max_speed,
                departed, arrived, vaporized, period, depart_delay, stop_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, trips)
        self.conn.commit()

    def parse_edge_data(self, xml_file):
        """Parsear edgeData.xml"""
        print(f"→ Procesando {xml_file}...")
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            edge_records = []
            for interval in root.findall('interval'):
                begin = self.safe_float(interval.get('begin'))
                timestamp = self.simulation_start + timedelta(seconds=begin)
                for edge in interval.findall('edge'):
                    edge_records.append((
                        timestamp, self.run_id, edge.get('id'), begin,
                        self.safe_float(interval.get('end', begin)),
                        self.safe_int(self.safe_float(edge.get('sampledSeconds', 0))),
                        self.safe_float(edge.get('speed')), self.safe_float(edge.get('occupancy')),
                        self.safe_float(edge.get('density')), self.safe_float(edge.get('waitingTime')),
                        self.safe_float(edge.get('traveltime'))
                    ))
            if edge_records: self._insert_edges_batch(edge_records)
        except Exception as e: print(f"  ✗ Error en edgeData: {e}")

    def _insert_edges_batch(self, edges):
        execute_batch(self.cur, """
            INSERT INTO edge_data (
                time, run_id, edge_id, begin_time, end_time, num_vehicles,
                avg_speed, avg_occupancy, avg_density, avg_waiting_time, avg_travel_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, edges)
        self.conn.commit()

    def parse_stats(self, xml_file):
        # Parsear stats.xml de SUMO
        print(f"→ Procesando {xml_file}...")
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Buscamos los bloques específicos del XML de estadísticas finales
            perf = root.find('performance')
            vehs = root.find('vehicles')
            teleports = root.find('teleports')
            safety = root.find('safety')
            trip_stats = root.find('vehicleTripStatistics')
            
            end_sim_time = self.safe_float(perf.get('end')) if perf is not None else 0.0
            timestamp = self.simulation_start + timedelta(seconds=end_sim_time)

            stat_data = (
                timestamp,
                self.run_id,
                self.safe_int(end_sim_time),
                self.safe_int(vehs.get('loaded')) if vehs is not None else 0,
                self.safe_int(vehs.get('inserted')) if vehs is not None else 0,
                self.safe_int(vehs.get('running')) if vehs is not None else 0,
                self.safe_int(vehs.get('waiting')) if vehs is not None else 0,
                self.safe_int(vehs.get('ended')) if vehs is not None else 0,
                self.safe_int(trip_stats.get('count')) if trip_stats is not None else 0,
                self.safe_int(safety.get('collisions')) if safety is not None else 0,
                self.safe_int(teleports.get('total')) if teleports is not None else 0,
                self.safe_float(trip_stats.get('totalTravelTime')) if trip_stats is not None else 0.0,
                self.safe_float(trip_stats.get('waitingTime')) if trip_stats is not None else 0.0
            )
            
            self._insert_stats_batch([stat_data])
            print(f"  ✓ Resumen de estadísticas guardado en simulation_stats")
        except Exception as e:
            print(f"  ✗ Error procesando estadísticas: {e}")

    def _insert_stats_batch(self, stats):
        execute_batch(self.cur, """
            INSERT INTO simulation_stats (
                time, run_id, step, vehicles_loaded, vehicles_inserted,
                vehicles_running, vehicles_waiting, vehicles_ended, vehicles_arrived,
                vehicles_collisions, vehicles_teleports, total_travel_time, total_waiting_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, stats)
        self.conn.commit()

    def parse_stopinfo(self, xml_file):
        """Parsear stopinfos.xml"""
        print(f"→ Procesando {xml_file}...")
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            stop_records = []
            for stopinfo in root.findall('stopinfo'):
                until = self.safe_float(stopinfo.get('until'))
                timestamp = self.simulation_start + timedelta(seconds=until)
                stop_records.append((
                    timestamp, self.run_id, stopinfo.get('id'), stopinfo.get('vehicle'),
                    self.safe_float(stopinfo.get('delay')), self.safe_int(stopinfo.get('loaded')),
                    self.safe_int(stopinfo.get('unloaded')), self.safe_int(stopinfo.get('loadedPersons'))
                ))
            if stop_records: self._insert_stops_batch(stop_records)
        except Exception as e: print(f"  ✗ Error en stopinfo: {e}")

    def _insert_stops_batch(self, stops):
        execute_batch(self.cur, """
            INSERT INTO pt_stops (
                time, run_id, stop_id, vehicle_id, delay,
                passengers_loaded, passengers_unloaded, passengers_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, stops)
        self.conn.commit()

    def finalize_simulation(self):
        self.cur.execute("""
            UPDATE simulation_runs SET end_time = %s, status = 'completed' WHERE run_id = %s
        """, (datetime.now(), self.run_id))
        self.conn.commit()
        print(f"✓ Simulación {self.run_id} finalizada")

    def close(self):
        self.cur.close()
        self.conn.close()

def main():
    parser = argparse.ArgumentParser(description='Importar datos SUMO a PostgreSQL')
    parser.add_argument('--dir', required=True)
    parser.add_argument('--run-name', required=True)
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', default='5432')
    parser.add_argument('--database', default='sumo_traffic')
    parser.add_argument('--user', default='postgres')
    parser.add_argument('--password', default='sumo123')
    
    args = parser.parse_args()
    db_config = {'host': args.host, 'port': args.port, 'database': args.database, 'user': args.user, 'password': args.password}
    
    data_dir = Path(args.dir)
    files_to_parse = {
        'tripinfos.xml': 'parse_tripinfo',
        'edgeData.xml': 'parse_edge_data',
        'stats.xml': 'parse_stats',
        'stopinfos.xml': 'parse_stopinfo'
    }
    
    try:
        importer = SumoImporter(db_config)
        importer.create_simulation_run(args.run_name)
        for filename, parse_func in files_to_parse.items():
            file_path = data_dir / filename
            if file_path.exists(): getattr(importer, parse_func)(str(file_path))
        importer.finalize_simulation()
    except Exception as e: print(f"✗ ERROR: {e}")
    finally: importer.close()

if __name__ == '__main__':
    main()
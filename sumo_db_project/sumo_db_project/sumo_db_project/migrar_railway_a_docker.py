import psycopg2
from psycopg2.extras import execute_values


# CONFIGURACIÓN

railway_config = {
    'host': 'caboose.proxy.rlwy.net',
    'port': '17768',
    'database': 'railway',
    'user': 'postgres',
    'password': 'GoSmDUXwjTOZWZNBOZqlFdNsAqWdJKCV'
}

docker_config = {
    'host': 'localhost',
    'port': '5432',
    'database': 'sumo_traffic',
    'user': 'postgres',
    'password': 'sumo123'
}

def main():
    print("=" * 60)
    print("MIGRACIÓN TOTAL: RAILWAY -> DOCKER (TIMESCALEDB)")
    print("=" * 60)
    
    r_conn = d_conn = None

    try:
        r_conn = psycopg2.connect(**railway_config)
        r_cur = r_conn.cursor()
        
        d_conn = psycopg2.connect(**docker_config)
        d_cur = d_conn.cursor()
        print("✓ Conexiones establecidas.")

        # --- PASO 0: SINCRONIZAR VEHICLE_TYPES ---
        print("\n Buscando tipos de vehículos nuevos en Railway...")
        r_cur.execute('SELECT DISTINCT vehicle_type FROM vehicle_trips WHERE vehicle_type IS NOT NULL')
        tipos_en_origen = r_cur.fetchall()

        if tipos_en_origen:
            datos_tipos = []
            for (vtype,) in tipos_en_origen:
                vclass = 'passenger'
                if 'moto' in vtype.lower(): vclass = 'motorcycle'
                elif 'bus' in vtype.lower(): vclass = 'bus'
                elif 'truck' in vtype.lower(): vclass = 'truck'
                
                datos_tipos.append((vtype, vclass, f"Detectado: {vtype}"))

            execute_values(d_cur, """
                INSERT INTO vehicle_types (vtype_id, vclass, description)
                VALUES %s ON CONFLICT (vtype_id) DO NOTHING
            """, datos_tipos)
            d_conn.commit()
            print(f" Catálogo de tipos actualizado ({len(datos_tipos)} tipos).")

        # --- 1. SIMULATION RUNS ---
        print("\n→ Sincronizando simulation_runs...")
        r_cur.execute('SELECT run_id, run_name, start_time, end_time, config_file, status FROM simulation_runs')
        runs = r_cur.fetchall()
        execute_values(d_cur, """
            INSERT INTO simulation_runs (run_id, run_name, start_time, end_time, config_file, status) 
            VALUES %s ON CONFLICT (run_id) DO NOTHING
        """, runs)
        d_conn.commit()

        # --- 2. VEHICLE TRIPS ---
        print("→ Migrando vehicle_trips...")
        r_cur.execute("""
            SELECT "time", run_id, vehicle_id, vehicle_type, depart, duration, 
                   route_length, waiting_time, time_loss, avg_speed, period 
            FROM vehicle_trips
        """)
        
        while True:
            batch = r_cur.fetchmany(5000)
            if not batch: break
            execute_values(d_cur, """
                INSERT INTO vehicle_trips (
                    "time", run_id, vehicle_id, vehicle_type, depart_time, duration, 
                    route_length, waiting_time, time_loss, avg_speed, period
                ) VALUES %s ON CONFLICT DO NOTHING
            """, batch)
            d_conn.commit()
            print("   Lote de viajes insertado...")

        # --- 3. EDGE DATA 
        print("\n→ Migrando edge_data...")
        r_cur.execute("""
            SELECT "time", run_id, edge_id, begin_time, end_time, num_vehicles, 
                   avg_speed, avg_occupancy, avg_density, avg_waiting_time 
            FROM edge_data
        """)

        while True:
            batch = r_cur.fetchmany(5000)
            if not batch: break
            
            cleaned_batch = []
            for r in batch:
                # Mapeamos los datos de Railway al esquema de 15 columnas de Docker
                new_row = (
                    r[0], r[1], r[2],       # time, run_id, edge_id
                    r[3], r[4],             # interval_begin, interval_end (copia de begin/end)
                    r[5], r[6], r[7], r[8], r[9], # num_veh, speed, occ, dens, wait
                    0.0, 0.0, 0.0,          # total_travel_time, co2, fuel (relleno)
                    r[3], r[4]              # begin_time, end_time
                )
                cleaned_batch.append(new_row)

            execute_values(d_cur, """
                INSERT INTO edge_data (
                    "time", "run_id", "edge_id", "interval_begin", "interval_end",
                    "num_vehicles", "avg_speed", "avg_occupancy", "avg_density", "avg_waiting_time",
                    "total_travel_time", "total_co2", "total_fuel", "begin_time", "end_time"
                ) VALUES %s ON CONFLICT DO NOTHING
            """, cleaned_batch)
            d_conn.commit()
            print("  ⏳ Lote de calles (edge_data) insertado...")

        # --- 4. STATS Y STOPS ---
        print("\n→ Sincronizando simulation_stats...")
        r_cur.execute('SELECT "time", run_id, step, vehicles_loaded, vehicles_inserted, vehicles_running, vehicles_waiting FROM simulation_stats')
        stats = r_cur.fetchall()
        
        if stats:
            # Limpiamos los datos: si step es None, lo cambiamos a 0
            cleaned_stats = []
            for s in stats:
                # s[0]=time, s[1]=run_id, s[2]=step...
                new_stat = (s[0], s[1], s[2] if s[2] is not None else 0, s[3], s[4], s[5], s[6])
                cleaned_stats.append(new_stat)

            execute_values(d_cur, """
                INSERT INTO simulation_stats (
                    "time", run_id, timestep, vehicles_loaded, vehicles_inserted, 
                    vehicles_running, vehicles_waiting
                ) VALUES %s ON CONFLICT DO NOTHING
            """, cleaned_stats)
        d_conn.commit()
        print("\n" + "=" * 60)
        print("✓ MIGRACIÓN FINALIZADA EXITOSAMENTE")
        print("=" * 60)

    except Exception as e:
        print(f"\n ERROR CRÍTICO: {e}")
        if d_conn: d_conn.rollback()
    finally:
        if r_conn: r_conn.close()
        if d_conn: d_conn.close()

if __name__ == '__main__':
    main()
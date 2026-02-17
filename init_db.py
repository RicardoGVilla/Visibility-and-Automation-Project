import sqlite3
import json

def init_database():
    conn = sqlite3.connect('vessel_tracking.db')
    cursor = conn.cursor()
    
    # Drop old tables
    cursor.execute('DROP TABLE IF EXISTS routes')
    cursor.execute('DROP TABLE IF EXISTS vessels')
    cursor.execute('DROP TABLE IF EXISTS ports')
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            status TEXT DEFAULT 'normal'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vessels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            current_latitude REAL NOT NULL,
            current_longitude REAL NOT NULL,
            status TEXT DEFAULT 'on_time'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            region_from TEXT,
            region_to TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_line_id INTEGER,
            name TEXT NOT NULL,
            waypoints TEXT NOT NULL,
            color TEXT NOT NULL,
            origin_port_id INTEGER,
            destination_port_id INTEGER,
            FOREIGN KEY (service_line_id) REFERENCES service_lines(id),
            FOREIGN KEY (origin_port_id) REFERENCES ports(id),
            FOREIGN KEY (destination_port_id) REFERENCES ports(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voyages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER,
            vessel_id INTEGER,
            departure_date TEXT,
            arrival_date TEXT,
            status TEXT DEFAULT 'scheduled',
            FOREIGN KEY (route_id) REFERENCES routes(id),
            FOREIGN KEY (vessel_id) REFERENCES vessels(id)
        )
    ''')
    
    # Insert ports
    ports_data = [
        ('Chittagong', 22.3569, 91.7832, 'normal'),
        ('Colombo', 6.9271, 79.8612, 'normal'),
        ('Halifax', 44.6488, -63.5752, 'normal'),
        ('Montreal', 45.5017, -73.5673, 'normal'),
        ('Rotterdam', 51.9244, 4.4777, 'normal'),
        ('Norfolk, VA', 36.8468, -76.2852, 'normal'),
        ('Southampton', 50.9097, -1.4044, 'normal'),
        ('Boston, MA', 42.3601, -71.0589, 'strike'),
        ('Hamburg', 53.5511, 9.9937, 'normal'),
        ('Felixstowe', 51.9613, 1.2977, 'normal'),
        ('New York', 40.6692, -74.0445, 'normal')
    ]
    cursor.executemany('INSERT INTO ports (name, latitude, longitude, status) VALUES (?, ?, ?, ?)', ports_data)
    
    # Insert vessels
    vessels_data = [
        ('CMA CGM ARCTIC', 5.5, 80.0, 'on_time'),
        ('MSC MEDITERRANEAN', 45.0, -35.0, 'delayed'),
        ('HAPAG LLOYD EXPRESS', 45.0, -55.0, 'on_time'),
        ('MAERSK SEALAND', 48.0, -30.0, 'on_time')
    ]
    cursor.executemany('INSERT INTO vessels (name, current_latitude, current_longitude, status) VALUES (?, ?, ?, ?)', vessels_data)
    
    # Insert service lines
    service_lines_data = [
        ('Asia-North America Service', 'Asia', 'North America'),
        ('Europe-North America Service', 'Europe', 'North America')
    ]
    cursor.executemany('INSERT INTO service_lines (name, region_from, region_to) VALUES (?, ?, ?)', service_lines_data)
    
    # Insert routes
    routes_data = [
        (1, 'Chittagong-Montreal Route', json.dumps([[22.3569, 91.7832], [6.9271, 79.8612], [30.0, 32.5], [36.0, -5.5], [44.6488, -63.5752], [45.5017, -73.5673]]), '#2E86AB', 1, 4),
        (2, 'Rotterdam-Norfolk Route', json.dumps([[51.9244, 4.4777], [36.8468, -76.2852]]), '#F18F01', 5, 6),
        (2, 'Southampton-Boston Route', json.dumps([[50.9097, -1.4044], [42.3601, -71.0589]]), '#9B59B6', 7, 8),
        (2, 'Hamburg-New York Route', json.dumps([[53.5511, 9.9937], [51.9244, 4.4777], [51.9613, 1.2977], [50.0, -10.0], [48.0, -30.0], [42.0, -50.0], [40.6692, -74.0445]]), '#E74C3C', 9, 11)
    ]
    cursor.executemany('INSERT INTO routes (service_line_id, name, waypoints, color, origin_port_id, destination_port_id) VALUES (?, ?, ?, ?, ?, ?)', routes_data)
    
    # Insert voyages
    voyages_data = [
        (1, 1, '2026-01-28 12:30', '2026-03-10', 'in_transit'),
        (2, 2, '2026-02-05 14:00', '2026-02-20', 'delayed'),
        (3, 3, '2026-02-12 10:00', '2026-02-20', 'in_transit'),
        (4, 4, '2026-02-15 08:00', '2026-02-28', 'in_transit')
    ]
    cursor.executemany('INSERT INTO voyages (route_id, vessel_id, departure_date, arrival_date, status) VALUES (?, ?, ?, ?, ?)', voyages_data)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_database()

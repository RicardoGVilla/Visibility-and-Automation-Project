import sqlite3
import json

def init_database():
    conn = sqlite3.connect('vessel_tracking.db')
    cursor = conn.cursor()
    
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
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            waypoints TEXT NOT NULL,
            color TEXT NOT NULL,
            vessel_id INTEGER,
            origin_port_id INTEGER,
            destination_port_id INTEGER,
            FOREIGN KEY (vessel_id) REFERENCES vessels(id),
            FOREIGN KEY (origin_port_id) REFERENCES ports(id),
            FOREIGN KEY (destination_port_id) REFERENCES ports(id)
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
        ('Boston, MA', 42.3601, -71.0589, 'strike')
    ]
    cursor.executemany('INSERT INTO ports (name, latitude, longitude, status) VALUES (?, ?, ?, ?)', ports_data)
    
    # Insert vessels
    vessels_data = [
        ('CMA CGM ARCTIC', 5.5, 80.0, 'on_time'),
        ('MSC MEDITERRANEAN', 45.0, -35.0, 'delayed'),
        ('HAPAG LLOYD EXPRESS', 45.0, -55.0, 'on_time')
    ]
    cursor.executemany('INSERT INTO vessels (name, current_latitude, current_longitude, status) VALUES (?, ?, ?, ?)', vessels_data)
    
    # Insert routes
    routes_data = [
        ('Asia-North America Line', json.dumps([[22.3569, 91.7832], [6.9271, 79.8612], [30.0, 32.5], [36.0, -5.5], [44.6488, -63.5752], [45.5017, -73.5673]]), '#2E86AB', 1, 1, 4),
        ('Europe-Norfolk Line', json.dumps([[51.9244, 4.4777], [36.8468, -76.2852]]), '#F18F01', 2, 5, 6),
        ('UK-Boston Line', json.dumps([[50.9097, -1.4044], [42.3601, -71.0589]]), '#9B59B6', 3, 7, 8)
    ]
    cursor.executemany('INSERT INTO routes (name, waypoints, color, vessel_id, origin_port_id, destination_port_id) VALUES (?, ?, ?, ?, ?, ?)', routes_data)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()

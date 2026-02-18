from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException
import sqlite3
import json
import random
from geopy.geocoders import Nominatim
import time

app = Flask(__name__)

# Global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors
    if isinstance(e, HTTPException):
        return jsonify({'error': e.description}), e.code
    # Non-HTTP exceptions
    return jsonify({'error': str(e)}), 500
geolocator = Nominatim(user_agent="vessel_tracking_app_v1", timeout=10)

def get_coordinates(port_name):
    try:
        time.sleep(1)
        location = geolocator.geocode(port_name)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Geocoding error for {port_name}: {e}")
    return None, None

def get_or_create_port(cursor, port_name):
    cursor.execute('SELECT id, latitude, longitude FROM ports WHERE name = ?', (port_name,))
    port = cursor.fetchone()
    
    if port:
        return port[0], port[1], port[2]
    
    lat, lon = get_coordinates(port_name)
    if lat and lon:
        cursor.execute('INSERT INTO ports (name, latitude, longitude) VALUES (?, ?, ?)', (port_name, lat, lon))
        return cursor.lastrowid, lat, lon
    
    return None, None, None

def generate_waypoints(origin_lat, origin_lon, dest_lat, dest_lon):
    waypoints = [[origin_lat, origin_lon]]
    mid_lat = (origin_lat + dest_lat) / 2
    mid_lon = (origin_lon + dest_lon) / 2
    waypoints.append([mid_lat, mid_lon])
    waypoints.append([dest_lat, dest_lon])
    return waypoints

def get_or_create_route(cursor, origin_port_id, dest_port_id, origin_lat, origin_lon, dest_lat, dest_lon, origin_name, dest_name):
    cursor.execute('SELECT id FROM routes WHERE origin_port_id = ? AND destination_port_id = ?', 
                   (origin_port_id, dest_port_id))
    route = cursor.fetchone()
    
    if route:
        return route[0]
    
    cursor.execute('SELECT id FROM service_lines WHERE name = ?', ('Unassigned',))
    service_line = cursor.fetchone()
    
    if not service_line:
        cursor.execute('INSERT INTO service_lines (name, region_from, region_to) VALUES (?, ?, ?)', 
                       ('Unassigned', 'Unknown', 'Unknown'))
        service_line_id = cursor.lastrowid
    else:
        service_line_id = service_line[0]
    
    waypoints = generate_waypoints(origin_lat, origin_lon, dest_lat, dest_lon)
    route_name = f'{origin_name}-{dest_name} Route'
    color = f'#{random.randint(0, 0xFFFFFF):06x}'
    
    cursor.execute('''INSERT INTO routes (service_line_id, name, waypoints, color, origin_port_id, destination_port_id) 
                      VALUES (?, ?, ?, ?, ?, ?)''',
                   (service_line_id, route_name, json.dumps(waypoints), color, origin_port_id, dest_port_id))
    return cursor.lastrowid

@app.route('/webhook/shipment', methods=['POST'])
def receive_shipment():
    try:
        payload = request.json
        shipment = None
        # Handle both list and dict payloads for 'included'
        included = []
        if isinstance(payload, list):
            for entry in payload:
                if isinstance(entry, dict) and 'included' in entry:
                    included.extend(entry['included'])
        elif isinstance(payload, dict):
            included = payload.get('included', [])
        for item in included:
            if item['type'] == 'shipment':
                shipment = item
                break
        if not shipment:
            return jsonify({'error': 'No shipment data found'}), 400
        attrs = shipment['attributes']
        origin_name = attrs.get('port_of_lading_name')
        dest_name = attrs.get('port_of_discharge_name')
        vessel_name = attrs.get('pod_vessel_name')
        departure_date = attrs.get('pol_atd_at')
        arrival_date = attrs.get('pod_eta_at')
        if not all([origin_name, dest_name, vessel_name]):
            return jsonify({'error': 'Missing required fields'}), 400
        conn = sqlite3.connect('vessel_tracking.db')
        cursor = conn.cursor()
        origin_port_id, origin_lat, origin_lon = get_or_create_port(cursor, origin_name)
        dest_port_id, dest_lat, dest_lon = get_or_create_port(cursor, dest_name)
        if not origin_port_id or not dest_port_id:
            conn.close()
            return jsonify({'error': 'Could not geocode ports'}), 400
        cursor.execute('SELECT id FROM vessels WHERE name = ?', (vessel_name,))
        vessel = cursor.fetchone()
        if not vessel:
            cursor.execute('INSERT INTO vessels (name, current_latitude, current_longitude) VALUES (?, ?, ?)', 
                           (vessel_name, 0.0, 0.0))
            vessel_id = cursor.lastrowid
        else:
            vessel_id = vessel[0]
        route_id = get_or_create_route(cursor, origin_port_id, dest_port_id, 
                                        origin_lat, origin_lon, dest_lat, dest_lon,
                                        origin_name, dest_name)
        cursor.execute('''INSERT INTO voyages (route_id, vessel_id, departure_date, arrival_date, status) 
                          VALUES (?, ?, ?, ?, ?)''',
                       (route_id, vessel_id, departure_date, arrival_date, 'in_transit'))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Voyage created successfully'}), 201
    except Exception as e:
        # This will be caught by the global error handler, but we keep it for clarity
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)

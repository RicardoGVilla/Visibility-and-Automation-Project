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

    route_name = f'{origin_name}-{dest_name} Route'
    color = f'#{random.randint(0, 0xFFFFFF):06x}'
    cursor.execute('''INSERT INTO routes (service_line_id, name, color, origin_port_id, destination_port_id) 
                      VALUES (?, ?, ?, ?, ?)''',
                   (service_line_id, route_name, color, origin_port_id, dest_port_id))
    return cursor.lastrowid

@app.route('/webhook/shipment', methods=['POST'])
def receive_shipment():
    try:
        payload = request.json
        shipment = None
        included = []
        if isinstance(payload, list):
            for entry in payload:
                if isinstance(entry, dict) and 'included' in entry:
                    included.extend(entry['included'])
        # Always extract shipment and included
        included = []
        if isinstance(payload, dict):
            included = payload.get('included', [])
        shipment = None
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
        # Compose full legs: origin + transshipments (from events) + port of discharge + final destination
        port_lookup = {p['id']: p['attributes']['name'] for p in included if p['type'] == 'port' and 'attributes' in p and 'name' in p['attributes']}
        container = next((item for item in included if item['type'] == 'container'), None)
        legs = []
        if container and 'relationships' in container and 'transport_events' in container['relationships']:
            event_ids = [e['id'] for e in container['relationships']['transport_events']['data'] if 'id' in e]
            events = [item for item in included if item['type'] == 'transport_event' and item['id'] in event_ids]
            def get_event_time(ev):
                return ev.get('attributes', {}).get('timestamp') or ''
            events.sort(key=get_event_time)
            for ev in events:
                port_id = None
                if 'relationships' in ev and 'location' in ev['relationships'] and ev['relationships']['location']['data']:
                    port_id = ev['relationships']['location']['data']['id']
                if port_id and port_id in port_lookup:
                    legs.append(port_lookup[port_id])
        full_legs = []
        if origin_name:
            full_legs.append(origin_name)
        for port in legs:
            if port not in (origin_name, dest_name) and port not in full_legs:
                full_legs.append(port)
        if dest_name and dest_name not in full_legs:
            full_legs.append(dest_name)
        destination_name = attrs.get('destination_name')
        if destination_name and destination_name not in full_legs:
            full_legs.append(destination_name)

        # Use the last port in full_legs as the true destination for the route
        true_dest_name = full_legs[-1] if full_legs else dest_name
        origin_port_id, origin_lat, origin_lon = get_or_create_port(cursor, origin_name)
        dest_port_id, dest_lat, dest_lon = get_or_create_port(cursor, true_dest_name)
        if not origin_port_id or not dest_port_id:
            conn.close()
            return jsonify({'error': 'Could not geocode ports'}), 400
        cursor.execute('SELECT id FROM vessels WHERE name = ?', (vessel_name,))
        vessel = cursor.fetchone()
        if not vessel:
            # Set vessel's initial location to the origin port's coordinates
            vessel_lat = origin_lat if origin_lat is not None else 0.0
            vessel_lon = origin_lon if origin_lon is not None else 0.0
            cursor.execute('INSERT INTO vessels (name, current_latitude, current_longitude) VALUES (?, ?, ?)', 
                           (vessel_name, vessel_lat, vessel_lon))
            vessel_id = cursor.lastrowid
        else:
            vessel_id = vessel[0]
        route_id = get_or_create_route(cursor, origin_port_id, dest_port_id, 
                                        origin_lat, origin_lon, dest_lat, dest_lon,
                                        origin_name, true_dest_name)
        # Store the full_legs as before
        cursor.execute('''INSERT INTO voyages (route_id, vessel_id, departure_date, arrival_date, status, legs) 
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (route_id, vessel_id, departure_date, arrival_date, 'in_transit', json.dumps(full_legs)))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Voyage created successfully', 'legs': full_legs}), 201
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
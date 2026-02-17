import sqlite3
import json
from models import Vessel, Port, ShippingRoute, Voyage

class VesselTrackingService:
    def __init__(self, db_path='vessel_tracking.db'):
        self.db_path = db_path
    
    def get_voyages(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT v.id, v.departure_date, v.arrival_date, v.status,
                   r.name, r.waypoints, r.color,
                   op.name, op.latitude, op.longitude, op.status,
                   dp.name, dp.latitude, dp.longitude, dp.status,
                   ve.name, ve.current_latitude, ve.current_longitude, ve.status
            FROM voyages v
            JOIN routes r ON v.route_id = r.id
            JOIN ports op ON r.origin_port_id = op.id
            JOIN ports dp ON r.destination_port_id = dp.id
            JOIN vessels ve ON v.vessel_id = ve.id
        ''')
        
        voyages = []
        for row in cursor.fetchall():
            # Parse data
            waypoints = json.loads(row[5])
            
            # Create objects
            origin_port = Port(row[7], [row[8], row[9]], row[10])
            destination_port = Port(row[11], [row[12], row[13]], row[14])
            
            route = ShippingRoute(
                name=row[4],
                waypoints=waypoints,
                color=row[6],
                origin_port=origin_port,
                destination_port=destination_port
            )
            
            vessel = Vessel(row[15], [row[16], row[17]], row[18])
            
            voyage = Voyage(
                route=route,
                vessel=vessel,
                departure_date=row[1],
                arrival_date=row[2],
                status=row[3]
            )
            voyages.append(voyage)
        
        conn.close()
        return voyages

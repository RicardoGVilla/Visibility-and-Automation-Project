import sqlite3
import json
from models import Vessel, Port, ShippingRoute

class VesselTrackingService:
    def __init__(self, db_path='vessel_tracking.db'):
        self.db_path = db_path
    
    def get_routes(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.id, r.name, r.waypoints, r.color,
                   v.name, v.current_latitude, v.current_longitude, v.status,
                   op.name, op.latitude, op.longitude, op.status,
                   dp.name, dp.latitude, dp.longitude, dp.status
            FROM routes r
            JOIN vessels v ON r.vessel_id = v.id
            JOIN ports op ON r.origin_port_id = op.id
            JOIN ports dp ON r.destination_port_id = dp.id
        ''')
        
        routes = []
        for row in cursor.fetchall():
            # Parse data
            waypoints = json.loads(row[2])
            
            # Create objects
            vessel = Vessel(row[4], [row[5], row[6]], row[7])
            origin_port = Port(row[8], [row[9], row[10]], row[11])
            destination_port = Port(row[12], [row[13], row[14]], row[15])
            
            route = ShippingRoute(
                name=row[1],
                waypoints=waypoints,
                color=row[3],
                vessel=vessel,
                origin_port=origin_port,
                destination_port=destination_port
            )
            routes.append(route)
        
        conn.close()
        return routes

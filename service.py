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
            SELECT v.id, v.departure_date, v.arrival_date, v.status, v.legs,
                   r.name, r.color,
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
            fk_errors = []
            # Check origin port
            if row[7] is None or row[8] is None or row[9] is None:
                fk_errors.append("origin_port")
            # Check destination port
            if row[11] is None or row[12] is None or row[13] is None:
                fk_errors.append("destination_port")
            # Check route
            if row[5] is None or row[6] is None:
                fk_errors.append("route")
            # Check vessel
            if row[15] is None or row[16] is None or row[17] is None:
                fk_errors.append("vessel")
            if fk_errors:
                print(f"Skipping voyage due to missing or invalid foreign key(s): {', '.join(fk_errors)}")
                continue
            try:
                origin_port = Port(row[7], [row[8], row[9]], row[10])
                destination_port = Port(row[11], [row[12], row[13]], row[14])
                route = ShippingRoute(
                    name=row[5],
                    color=row[6],
                    origin_port=origin_port,
                    destination_port=destination_port
                )
                vessel = Vessel(row[15], [row[16], row[17]], row[18])
            except Exception as e:
                print(f"Skipping voyage due to error constructing objects: {e}")
                continue
            # Parse legs JSON and exclude origin/destination for transshipment_ports
            legs = []
            try:
                legs = json.loads(row[4]) if row[4] else []
            except Exception as e:
                print(f"Error parsing legs for voyage: {e}")
                legs = []
            transshipment_ports = []
            if legs and len(legs) > 2:
                transshipment_ports = legs[1:-1]
            voyage = Voyage(
                route=route,
                vessel=vessel,
                departure_date=row[1],
                arrival_date=row[2],
                status=row[3],
                transshipment_ports=transshipment_ports
            )
            voyages.append(voyage)
        conn.close()
        return voyages

class Vessel:
    def __init__(self, name, current_location, status='on_time'):
        self.name = name
        self.current_location = current_location
        self.status = status

class Port:
    def __init__(self, name, location, status='normal'):
        self.name = name
        self.location = location
        self.status = status

class ShippingRoute:
    def __init__(self, name, color, origin_port, destination_port):
        self.name = name
        self.color = color
        self.origin_port = origin_port
        self.destination_port = destination_port

class Voyage:
    def __init__(self, route, vessel, departure_date, arrival_date, status='scheduled', transshipment_ports=None):
        self.route = route
        self.vessel = vessel
        self.departure_date = departure_date
        self.arrival_date = arrival_date
        self.status = status
        self.transshipment_ports = transshipment_ports if transshipment_ports is not None else []

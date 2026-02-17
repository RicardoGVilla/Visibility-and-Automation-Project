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
    def __init__(self, name, waypoints, color, vessel, origin_port, destination_port):
        self.name = name
        self.waypoints = waypoints # path of the route as list of lat/lon pairs
        self.color = color
        self.vessel = vessel
        self.origin_port = origin_port
        self.destination_port = destination_port

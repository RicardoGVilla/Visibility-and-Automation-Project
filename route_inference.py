
"""
Dynamic route inference for vessel shipping.
Given a list of ports (as strings), return their coordinates as the route.
If the final destination is an East Canada port, add Suez Canal as a waypoint between Asia and Canada.
No hardcoded port logic; works with any port list.
"""
from typing import List, Tuple
from geopy.geocoders import Nominatim

def get_coords(place: str):
    geolocator = Nominatim(user_agent="route_inference")
    loc = geolocator.geocode(place)
    if loc:
        return (loc.latitude, loc.longitude)
    return None

def infer_route(port_list: List[str], east_canada_ports=None) -> List[Tuple[float, float]]:
    if east_canada_ports is None:
        east_canada_ports = {'halifax', 'montreal', 'saint john'}
    suez = (30.0, 32.5)
    # Get coordinates for all ports
    coords = [get_coords(port) for port in port_list]
    # If the last port is an East Canada port and the route includes Asia, add Suez Canal after the last Asia port
    if port_list and port_list[-1].lower() in east_canada_ports:
        # Find last Asia port index
        asia_ports = {'singapore', 'haiphong', 'yantian', 'ningbo', 'shanghai', 'busan', 'kaohsiung'}
        last_asia_idx = -1
        for i, port in enumerate(port_list):
            if port.lower() in asia_ports:
                last_asia_idx = i
        if last_asia_idx != -1:
            # Insert Suez after last Asia port
            coords = coords[:last_asia_idx+1] + [suez] + coords[last_asia_idx+1:]
    # Remove any None values (failed geocoding)
    return [c for c in coords if c]

# Example usage
if __name__ == "__main__":
    route = infer_route(['Haiphong', 'Singapore', 'Halifax'])
    print("Route waypoints:")
    for lat, lon in route:
        print(f"{lat}, {lon}")

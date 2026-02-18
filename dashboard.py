import folium
from service import VesselTrackingService
import searoute as sr

class VesselTrackingDashboard:
    """
    the dashboard for visualizing maritime voyages, port statuses, 
    and vessel positions using Folium and Searoute
    """
    def __init__(self):
        # initialize the base map with global coverage and jump-wrap marker persistence
        self.map = folium.Map(location=[20, 0], tiles='CartoDB positron', zoom_start=2, world_copy_jump=True)
        self.voyages = []

    def load_data(self):
        """fetches voyage and vessel data from the tracking service module"""
        service = VesselTrackingService()
        self.voyages = service.get_voyages()

    def get_continuous_path(self, origin, destination):
        """
        calculates a route and adjusts longitudes to ensure 
        linear continuity across the International Date Line.
        """
        try:
            # normalize inputs to the standard [-180, 180] range for the routing engine
            o_lonlat = [(origin[1] + 180) % 360 - 180, origin[0]]
            d_lonlat = [(destination[1] + 180) % 360 - 180, destination[0]]

            # retrieve maritime-constrained path coordinates
            route = sr.searoute(o_lonlat, d_lonlat, units="km", append_orig_dest=True)
            raw_coords = route['geometry']['coordinates']
            # (processing logic for path continuity can go here if needed)
            return raw_coords
        except Exception as e:
            print(f"searoute failed: {e} → fallback straight line")
            return [[origin[1], origin[0]], [destination[1], destination[0]]]

    def render_routes(self):
        all_bounds = []  # for auto-fit

        for voyage in self.voyages:
            route = voyage.route
            feature_group = folium.FeatureGroup(name=route.name, show=True)

            origin = route.origin_port.location       # [lat, lon]
            destination = route.destination_port.location

            # Only use searoute for path, ignore waypoints
            path_segments = self.get_searoute_coords(origin, destination)

            # Draw each segment as separate PolyLine
            for segment in path_segments:
                if len(segment) < 2:
                    continue
                folium.PolyLine(
                    locations=segment,
                    color=route.color,
                    weight=3,
                    opacity=0.8,
                    dash_array='10, 5'
                ).add_to(feature_group)

            # Origin marker
            folium.Marker(
                origin,
                popup=route.origin_port.name
            ).add_to(feature_group)

            # Destination marker with optional strike
            if route.destination_port.status == 'strike':
                folium.Marker(
                    destination,
                    popup=f'<b style="color: orange;">⚠️ PORT STRIKE</b><br>{route.destination_port.name}',
                    icon=folium.Icon(color='orange', icon='exclamation-triangle', prefix='fa')
                ).add_to(feature_group)
            else:
                folium.Marker(
                    destination,
                    popup=route.destination_port.name
                ).add_to(feature_group)

            # Vessel marker
            vessel_color = 'red' if voyage.status == 'delayed' else 'green' if voyage.status == 'in_transit' else 'purple'
            vessel_popup = f'{voyage.vessel.name}<br>{"⚠️ DELAYED" if voyage.status == "delayed" else "Current Location"}'

            vessel_loc = voyage.vessel.current_location
            if vessel_loc and len(vessel_loc) == 2:
                folium.Marker(
                    vessel_loc,
                    icon=folium.Icon(icon='ship', prefix='fa', color=vessel_color),
                    popup=vessel_popup
                ).add_to(feature_group)

            feature_group.add_to(self.map)

            # Collect bounds
            all_bounds.extend([origin, destination, vessel_loc])

        if all_bounds:
            valid_points = [p for p in all_bounds if p and len(p) == 2 and all(isinstance(c, (int, float)) for c in p)]
            if valid_points:
                min_lat = min(p[0] for p in valid_points)
                max_lat = max(p[0] for p in valid_points)
                min_lon = min(p[1] for p in valid_points)
                max_lon = max(p[1] for p in valid_points)
                # Add some padding
                self.map.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]], padding=(0.15, 0.15))
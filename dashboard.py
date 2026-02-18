import folium
import sqlite3
import searoute as sr
from service import VesselTrackingService
from geopy.geocoders import Nominatim
try:
    from global_land_mask import globe
except ImportError:
    globe = None

class VesselTrackingDashboard:
    def __init__(self):
        self.map = folium.Map(
            location=[20, 0],
            tiles='CartoDB positron',
            zoom_start=2,
            world_copy_jump=True,
            height='60vh',  
            width='100%',
        )
        self.voyages = []
        self.geolocator = Nominatim(user_agent="vessel_dashboard_final_leg_only", timeout=10)

    def load_data(self):
        service = VesselTrackingService()
        self.voyages = service.get_voyages()

    def is_land(self, lat, lon):
        if globe:
            return globe.is_land(lat, lon)
        return False

    def unwrap_longitude(self, target_lon, reference_lon):
        delta = target_lon - reference_lon
        turns = round(delta / 360)
        return target_lon - (turns * 360)

    def get_port_coords(self, port_name):
        conn = sqlite3.connect('vessel_tracking.db')
        cursor = conn.cursor()
        cursor.execute('SELECT latitude, longitude FROM ports WHERE name = ?', (port_name,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return [row[0], row[1]]
        try:
            location = self.geolocator.geocode(port_name)
            if location:
                cursor.execute('INSERT INTO ports (name, latitude, longitude, status) VALUES (?, ?, ?, ?)', 
                               (port_name, location.latitude, location.longitude, 'normal'))
                conn.commit()
                conn.close()
                return [location.latitude, location.longitude]
        except:
            pass
        conn.close()
        return None

    def get_continuous_leg(self, start_coords, end_coords, global_ref_lon, force_sea_route=False):
        """
        Calculates path. 
        force_sea_route: If True, skips the land check and always tries searoute.
        """
        target_lat, target_lon = end_coords
        unwrapped_end_lon = self.unwrap_longitude(target_lon, global_ref_lon)

        # Apply land check ONLY if it is not a 'forced' sea route leg
        if not force_sea_route and self.is_land(target_lat, target_lon):
            return [[start_coords[0], start_coords[1]], [target_lat, unwrapped_end_lon]], True

        try:
            norm_start = [(start_coords[1] + 180) % 360 - 180, start_coords[0]]
            norm_end = [(target_lon + 180) % 360 - 180, target_lat]
            
            route = sr.searoute(norm_start, norm_end, units="km")
            raw_path = route['geometry']['coordinates']
            
            linear_path = []
            prev_lon = start_coords[1]
            for lon, lat in raw_path:
                actual_lon = self.unwrap_longitude(lon, prev_lon)
                linear_path.append([lat, actual_lon])
                prev_lon = actual_lon
            return linear_path, False
        except:
            return [[start_coords[0], start_coords[1]], [target_lat, unwrapped_end_lon]], True

    def render_routes(self):
        all_bounds = []
        for voyage in self.voyages:
            route = voyage.route
            feature_group = folium.FeatureGroup(name=route.name, show=True)
            
            transshipments = getattr(voyage, 'transshipment_ports', []) or []
            port_names = [route.origin_port.name] + transshipments + [route.destination_port.name]
            resolved_coords = [self.get_port_coords(n) for n in port_names if self.get_port_coords(n)]

            if not resolved_coords: continue

            current_pos = resolved_coords[0]
            current_ref_lon = current_pos[1]
            folium.Marker(current_pos, popup=f"Origin: {port_names[0]}").add_to(feature_group)

            num_legs = len(resolved_coords) - 1
            for i in range(num_legs):
                # RULE: Force sea route for all legs EXCEPT the final one
                is_final_leg = (i == num_legs - 1)
                force_sea = not is_final_leg
                
                leg_path, is_inland = self.get_continuous_leg(current_pos, resolved_coords[i+1], current_ref_lon, force_sea_route=force_sea)
                
                folium.PolyLine(
                    locations=leg_path,
                    color=route.color,
                    weight=2,
                    opacity=0.5
                ).add_to(feature_group)
                
                current_pos = leg_path[-1]
                current_ref_lon = current_pos[1]
                folium.Marker(current_pos, popup=port_names[i+1]).add_to(feature_group)
                all_bounds.extend(leg_path)

            v_loc = voyage.vessel.current_location
            if v_loc:
                v_lat, v_lon_u = v_loc[0], self.unwrap_longitude(v_loc[1], current_ref_lon)
                folium.Marker([v_lat, v_lon_u], icon=folium.Icon(color='green', icon='ship', prefix='fa')).add_to(feature_group)
                all_bounds.append([v_lat, v_lon_u])
            feature_group.add_to(self.map)

        if all_bounds:
            self.map.fit_bounds(all_bounds, padding=(0.1, 0.1))

    def generate(self):
        self.load_data()
        self.render_routes()
        folium.LayerControl(collapsed=False).add_to(self.map)
        self.map.save('index.html')

if __name__ == '__main__':
    dashboard = VesselTrackingDashboard()
    dashboard.generate()
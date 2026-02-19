import folium
import sqlite3
import math
import searoute as sr
from service import VesselTrackingService
from models import Port
from geopy.geocoders import Nominatim
try:
    from global_land_mask import globe
except ImportError:
    globe = None

class VesselTrackingDashboard:
    def handle_last_mile_leg(self, current_pos, end_pos, start_port_name, end_port_name, route, current_ref_lon, feature_group):
        leg_path, is_inland = self.get_continuous_leg(current_pos, end_pos, current_ref_lon, force_sea_route=False)
        # Log segment info
        if is_inland:
            print(f"[INFO] Fallback: Inland segment used from {start_port_name} ({current_pos}) to {end_port_name} ({end_pos}) (sea route not used)")
        else:
            print(f"[INFO] SeaRoute library used: Path generated from {start_port_name} ({current_pos}) to {end_port_name} ({end_pos})")
        folium.PolyLine(
            locations=leg_path,
            color=route.color,
            weight=2,
            opacity=0.5
        ).add_to(feature_group)
        folium.Marker(
            leg_path[-1],
            popup=folium.Popup(
                f"""
                <div style='padding:8px;min-width:160px;max-width:220px;background:#fff;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.12);border:1px solid #e0e0e0;'>
                    <div style='font-weight:bold;font-size:1.1em;color:#2c3e50;'>Port</div>
                    <div style='margin-top:4px;color:#555;'>{end_port_name}</div>
                </div>
                """,
                max_width=250
            )
        ).add_to(feature_group)
        return leg_path[-1], leg_path

    def add_custom_legend(self, route_infos):
        map_id = self.map._id
        map_var = f"map_{map_id.replace('-', '')}"
        row_html = "".join([
            f"<div class='legend-row'><span class='legend-color' style='background:{color};'></span><span style='color:#222'>{name}</span></div>"
            for name, color in route_infos
        ])
        legend_html = f"""
        <style>
        .custom-map-legend {{
            background: rgba(255,255,255,0.97);
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            padding: 12px 18px 12px 18px;
            min-width: 180px;
            font-size: 1em;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}
        .custom-map-legend .legend-title {{
            font-weight: bold;
            margin-bottom: 8px;
            color: #222;
        }}
        .custom-map-legend .legend-row {{
            margin-bottom: 6px;
            display: flex;
            align-items: center;
        }}
        .custom-map-legend .legend-color {{
            display:inline-block;
            width:18px;
            height:6px;
            margin-right:10px;
            border-radius:2px;
        }}
        </style>
        <script>
        (function() {{
            var legend = L.control({{position: 'topright'}});
            legend.onAdd = function(map) {{
                var div = L.DomUtil.create('div', 'custom-map-legend leaflet-control');
                div.innerHTML = `<div class='legend-title'>Route Legend</div>{row_html}`;
                return div;
            }};
            if (typeof {map_var} !== 'undefined') {{
                legend.addTo({map_var});
            }} else {{
                setTimeout(function() {{ legend.addTo({map_var}); }}, 500);
            }}
        }})();
        </script>
        """
        self.map.get_root().html.add_child(folium.Element(legend_html))

    def __init__(self):
        self.map = folium.Map(
            location=[20, 0],
            tiles='CartoDB Voyager',
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

    def sorting_dynamic_voyages(self, voyage):
        """
        Returns (sorted_port_names, sorted_coords) for a given voyage using nearest-neighbor logic.
        """
        origin = {'name': voyage.route.origin_port.name, 'coord': voyage.route.origin_port.location}
        destination = {'name': voyage.route.destination_port.name, 'coord': voyage.route.destination_port.location}
        others = []
        for t in voyage.transshipment_ports:
            if isinstance(t, dict) and 'name' in t and 'coordinates' in t:
                others.append({'name': t['name'], 'coord': t['coordinates']})
            elif isinstance(t, Port):
                others.append({'name': t.name, 'coord': t.location})
            elif isinstance(t, str):
                coord = self.get_port_coords(t)
                others.append({'name': t, 'coord': coord})
            else:
                try:
                    name, coord = t
                    others.append({'name': name, 'coord': coord})
                except Exception:
                    others.append({'name': str(t), 'coord': None})
        vessel = voyage.vessel
        if hasattr(vessel, 'current_location') and vessel.current_location is not None:
            others.append({'name': vessel.name + ' (vessel)', 'coord': vessel.current_location})
        others_with_coords = [p for p in others if p['coord'] is not None]
        def haversine(coord1, coord2):
            lat1, lon1 = coord1
            lat2, lon2 = coord2
            R = 6371
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        sorted_points = []
        current = origin
        pool = others_with_coords.copy()
        while pool:
            next_idx, next_point = min(enumerate(pool), key=lambda x: haversine(current['coord'], x[1]['coord']))
            sorted_points.append(next_point)
            current = next_point
            pool.pop(next_idx)
        coords_sorted = [origin] + sorted_points + [destination]
        port_names_sorted = [p['name'] for p in coords_sorted]
        coords_sorted_only = [p['coord'] for p in coords_sorted]
        # Print the ordered array
        print("[COORDINATES ORDERED]")
        for p in coords_sorted:
            print(f"  {p['name']}: {p['coord']}")
        print("---")
        return port_names_sorted, coords_sorted_only

    def is_land(self, lat, lon):
        if globe:
            return globe.is_land(lat, lon)
        return False

    # function returns an adjusted longitude value. ensures that when plotting routes crossing the 180° meridian, the path remains visually continuous and accurate, avoiding misleading jumps on the map
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
        target_lat, target_lon = end_coords
        # adjusted coordinates 
        unwrapped_end_lon = self.unwrap_longitude(target_lon, global_ref_lon)

        # if not forced sea route and if leg is on land 
        if not force_sea_route and self.is_land(target_lat, target_lon):
            # return a straight line 
            return [[start_coords[0], start_coords[1]], [target_lat, unwrapped_end_lon]], True

        try:
            linear_path = self.calculate_sea_leg(start_coords, [target_lat, target_lon])
            return linear_path, False
        except:
            return [[start_coords[0], start_coords[1]], [target_lat, unwrapped_end_lon]], True
    
    def calculate_sea_leg(self, start_coords, end_coords):
        """
        calculates a sea route leg using the searoute library, normalizes coordinates, unwraps longitude for continuity.
        returns a list of [lat, lon] pairs.
        """
        norm_start = [(start_coords[1] + 180) % 360 - 180, start_coords[0]]
        norm_end = [(end_coords[1] + 180) % 360 - 180, end_coords[0]]
        route = sr.searoute(norm_start, norm_end, units="km")
        raw_path = route['geometry']['coordinates']
        linear_path = []
        prev_lon = start_coords[1]
        for lon, lat in raw_path:
            actual_lon = self.unwrap_longitude(lon, prev_lon)
            linear_path.append([lat, actual_lon])
            prev_lon = actual_lon
        return linear_path

    def render_routes(self):
        all_bounds = []
        route_infos = []

        for voyage in self.voyages:
            route = voyage.route
            feature_group = folium.FeatureGroup(name=route.name, show=True)
            route_infos.append((route.name, route.color))
            port_names, resolved_coords = self.sorting_dynamic_voyages(voyage)
            if not resolved_coords:
                continue
            current_pos = resolved_coords[0]
            current_ref_lon = current_pos[1]
            folium.Marker(
                current_pos,
                popup=folium.Popup(
                    f"""
                    <div style='padding:8px;min-width:160px;max-width:220px;background:#fff;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.12);border:1px solid #e0e0e0;'>
                        <div style='font-weight:bold;font-size:1.1em;color:#2c3e50;'>Origin Port</div>
                        <div style='margin-top:4px;color:#555;'>{port_names[0]}</div>
                    </div>
                    """,
                    max_width=250
                )
            ).add_to(feature_group)
            num_legs = len(resolved_coords) - 1

            for i in range(num_legs):
                is_final_leg = (i == num_legs - 1)
                # Set port names for logging
                start_port_name = port_names[i]
                end_port_name = port_names[i+1]
                start_port_coords = resolved_coords[i]
                end_port_coords = resolved_coords[i+1]
                # Exception: if not Pacific and only two legs, always use searoute
                route_name_lower = route.name.lower()
                is_pacific = 'pacific' in route_name_lower or 'pacific' in start_port_name.lower() or 'pacific' in end_port_name.lower()
                force_sea_override = False
                if num_legs == 1 and not is_pacific:
                    force_sea_override = True
                if is_final_leg:
                    current_pos, leg_path = self.handle_last_mile_leg(current_pos, end_port_coords, start_port_name, end_port_name, route, current_ref_lon, feature_group)
                else:
                    leg_path, is_inland = self.get_continuous_leg(current_pos, end_port_coords, current_ref_lon, force_sea_route=(True or force_sea_override))
                    # Log segment info
                    if is_inland:
                        print(f"[INFO] Fallback: Inland segment used from {start_port_name} ({start_port_coords}) to {end_port_name} ({end_port_coords}) (sea route not used)")
                    else:
                        print(f"[INFO] SeaRoute library used: Path generated from {start_port_name} ({start_port_coords}) to {end_port_name} ({end_port_coords})")
                    folium.PolyLine(
                        locations=leg_path,
                        color=route.color,
                        weight=2,
                        opacity=0.5
                    ).add_to(feature_group)
                    current_pos = leg_path[-1]
                    current_ref_lon = current_pos[1]
                    folium.Marker(
                        current_pos,
                        popup=folium.Popup(
                            f"""
                            <div style='padding:8px;min-width:160px;max-width:220px;background:#fff;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.12);border:1px solid #e0e0e0;'>
                                <div style='font-weight:bold;font-size:1.1em;color:#2c3e50;'>Port</div>
                                <div style='margin-top:4px;color:#555;'>{end_port_name}</div>
                            </div>
                            """,
                            max_width=250
                        )
                    ).add_to(feature_group)
                all_bounds.extend(leg_path)
            v_loc = voyage.vessel.current_location
            if v_loc:
                v_lat, v_lon_u = v_loc[0], self.unwrap_longitude(v_loc[1], current_ref_lon)
                folium.Marker(
                    [v_lat, v_lon_u],
                    icon=folium.Icon(color='green', icon='ship', prefix='fa'),
                    popup=folium.Popup(
                        f"""
                        <div style='padding:10px;min-width:170px;max-width:240px;background:#f8f9fa;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.13);border:1px solid #b2bec3;'>
                            <div style='font-weight:bold;font-size:1.1em;color:#006266;'>Vessel</div>
                            <div style='margin-top:4px;color:#222;'>{voyage.vessel.name}</div>
                            <div style='margin-top:6px;font-size:0.95em;color:#555;'>Route: <span style='color:{route.color};font-weight:bold'>{route.name}</span></div>
                        </div>
                        """,
                        max_width=260
                    )
                ).add_to(feature_group)
                all_bounds.append([v_lat, v_lon_u])
            feature_group.add_to(self.map)
        if all_bounds:
            self.map.fit_bounds(all_bounds, padding=(0.1, 0.1))
        # Add custom legend after all routes are processed
        self.add_custom_legend(route_infos)

    def generate(self):
        self.load_data()
        self.render_routes()
        folium.LayerControl(collapsed=False).add_to(self.map)
        self.map.save('index.html')

if __name__ == '__main__':
    dashboard = VesselTrackingDashboard()
    dashboard.generate()
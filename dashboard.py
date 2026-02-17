import folium
from service import VesselTrackingService

class VesselTrackingDashboard:
    def __init__(self):
    # initializing the map     
        self.map = folium.Map(location=(6.02, 81.5), tiles='CartoDB positron', zoom_start=2.4)
        self.routes = []
    
    # loads all routes from the service 
    def load_data(self):
        service = VesselTrackingService()
        self.routes = service.get_routes()
    
    def render_routes(self):
        for route in self.routes:
            feature_group = folium.FeatureGroup(name=route.name, show=True)
            
            # Add route line
            folium.PolyLine(route.waypoints, color=route.color, weight=3, opacity=0.8, dash_array='10, 5').add_to(feature_group)
            
            # Add origin port marker
            folium.Marker(route.origin_port.location, popup=route.origin_port.name).add_to(feature_group)
            
            # Add destination port marker
            if route.destination_port.status == 'strike':
                folium.Marker(
                    route.destination_port.location,
                    popup=f'<b style="color: orange;">⚠️ PORT STRIKE</b><br>{route.destination_port.name}',
                    icon=folium.Icon(color='orange', icon='exclamation-triangle', prefix='fa')
                ).add_to(feature_group)
            else:
                folium.Marker(route.destination_port.location, popup=route.destination_port.name).add_to(feature_group)
            
            # Add vessel marker
            vessel_color = 'red' if route.vessel.status == 'delayed' else 'green' if route.vessel.status == 'on_time' else 'purple'
            vessel_popup = f'{route.vessel.name}<br>{"⚠️ DELAYED" if route.vessel.status == "delayed" else "Current Location"}'
            
            folium.Marker(
                route.vessel.current_location,
                icon=folium.Icon(icon='ship', prefix='fa', color=vessel_color),
                popup=vessel_popup
            ).add_to(feature_group)
            
            feature_group.add_to(self.map)
    
    def add_controls(self):
        folium.LayerControl(position='topright', collapsed=False).add_to(self.map)
    
    def save(self, filename='index.html'):
        self.map.save(filename)
        
        # Add legend
        with open(filename, 'r') as f:
            map_html = f.read()
        
        custom_html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Vessel Tracking Dashboard</title>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map-container {{ position: relative; height: 60vh; }}
        #map-container iframe {{ width: 100%; height: 100%; border: none; }}
        .legend {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background-color: white;
            border: 2px solid grey;
            z-index: 9999;
            padding: 10px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div id="map-container">
        <iframe srcdoc='{map_html.replace("'", "&apos;")}'></iframe>
        <div class="legend">
            <b>Vessel Status</b><br>
            <span style="color:green">●</span> On Time<br>
            <span style="color:red">●</span> Delayed<br>
            <span style="color:orange">⚠</span> Port Strike
        </div>
    </div>
</body>
</html>
'''
        
        with open(filename, 'w') as f:
            f.write(custom_html)
    
    def generate(self):
        # loading data, rendering routes on the map, adding controls and saving the final dashboard display 
        self.load_data()
        self.render_routes()
        self.add_controls()
        self.save()

if __name__ == '__main__':
    dashboard = VesselTrackingDashboard()
    dashboard.generate()

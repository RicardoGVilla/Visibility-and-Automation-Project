import folium
from folium import plugins

m = folium.Map(location=(6.02, 81.5), tiles='CartoDB positron', zoom_start=2.4)

popup_html = '''
<b>Shipment Details</b><br>
<b>Vessel:</b> CMA CGM ARCTIC<br>
<b>Origin:</b> Chittagong<br>
<b>Departure:</b> 28-01-2026 12:30<br>
<b>Colombo ETA:</b> 03-02-2026<br>
<b>Halifax ETA:</b> 10-03-2026<br>
<b>Final Destination:</b> Montreal (CN Brampton 3037)<br>
'''

chittagong = [22.3569, 91.7832]
colombo = [6.9271, 79.8612]

# Maritime route through Suez Canal and Atlantic
suez = [30.0, 32.5]
gibraltar = [36.0, -5.5]
halifax = [44.6488, -63.5752]
montreal = [45.5017, -73.5673]
vessel_location = [5.5, 80.0]

# Create feature groups for filtering
line_asia_na = folium.FeatureGroup(name='Asia-North America Line', show=True)

# Add route and markers to groups
folium.PolyLine([chittagong, colombo, suez, gibraltar, halifax, montreal], color='#2E86AB', weight=3, opacity=0.8, dash_array='10, 5').add_to(line_asia_na)
folium.Marker(chittagong, popup=folium.Popup(popup_html, max_width=300)).add_to(line_asia_na)
folium.Marker(colombo, popup='Colombo').add_to(line_asia_na)
folium.Marker(halifax, popup='Halifax').add_to(line_asia_na)
folium.Marker(montreal, popup='Montreal (Destination)').add_to(line_asia_na)
folium.Marker(vessel_location, icon=folium.Icon(icon='ship', prefix='fa', color='green'), popup='CMA CGM ARCTIC<br>Current Location').add_to(line_asia_na)

# Add groups to map
line_asia_na.add_to(m)

# Europe to Norfolk Line
line_europe_norfolk = folium.FeatureGroup(name='Europe-Norfolk Line', show=True)

rotterdam = [51.9244, 4.4777]
norfolk = [36.8468, -76.2852]
vessel_norfolk = [45.0, -35.0]

popup_norfolk = '''
<b>Shipment Details</b><br>
<b style="color: red;">⚠️ DELAYED</b><br>
<b>Vessel:</b> MSC MEDITERRANEAN<br>
<b>Origin:</b> Rotterdam<br>
<b>Departure:</b> 05-02-2026 14:00<br>
<b>Norfolk ETA:</b> <span style="color: red;">20-02-2026 (Delayed 2 days)</span><br>
<b>Final Destination:</b> Norfolk, VA<br>
'''

folium.PolyLine([rotterdam, norfolk], color='#F18F01', weight=3, opacity=0.8, dash_array='10, 5').add_to(line_europe_norfolk)
folium.Marker(rotterdam, popup=folium.Popup(popup_norfolk, max_width=300)).add_to(line_europe_norfolk)
folium.Marker(norfolk, popup='Norfolk, VA').add_to(line_europe_norfolk)
folium.Marker(vessel_norfolk, icon=folium.Icon(icon='ship', prefix='fa', color='red'), popup='MSC MEDITERRANEAN<br>⚠️ DELAYED<br>Current Location').add_to(line_europe_norfolk)

line_europe_norfolk.add_to(m)

# UK to Boston Line
line_uk_boston = folium.FeatureGroup(name='UK-Boston Line', show=True)

southampton = [50.9097, -1.4044]
boston = [42.3601, -71.0589]
vessel_uk = [45.0, -55.0]

popup_uk = '''
<b>Shipment Details</b><br>
<b>Vessel:</b> HAPAG LLOYD EXPRESS<br>
<b>Origin:</b> Southampton<br>
<b>Departure:</b> 12-02-2026 10:00<br>
<b>Boston ETA:</b> 20-02-2026<br>
<b>Final Destination:</b> Boston, MA<br>
'''

folium.PolyLine([southampton, boston], color='#9B59B6', weight=3, opacity=0.8, dash_array='10, 5').add_to(line_uk_boston)
folium.Marker(southampton, popup=folium.Popup(popup_uk, max_width=300)).add_to(line_uk_boston)
folium.Marker(boston, popup='<b style="color: orange;">⚠️ PORT STRIKE</b><br>Boston, MA', icon=folium.Icon(color='orange', icon='exclamation-triangle', prefix='fa')).add_to(line_uk_boston)
folium.Marker(vessel_uk, icon=folium.Icon(icon='ship', prefix='fa', color='purple'), popup='HAPAG LLOYD EXPRESS<br>Current Location').add_to(line_uk_boston)

line_uk_boston.add_to(m)

# Add layer control
folium.LayerControl(position='topright', collapsed=False).add_to(m)

m.save('index.html')

# Wrap map in custom HTML with legend
with open('index.html', 'r') as f:
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

with open('index.html', 'w') as f:
    f.write(custom_html)
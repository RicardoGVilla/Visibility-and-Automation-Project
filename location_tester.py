from geopy.geocoders import Nominatim

# List of locations from the CSV
locations = ["haiphong", "yantian", "ningbo"]

geolocator = Nominatim(user_agent="geoapi_tester")

for loc in locations:
    location = geolocator.geocode(loc)
    if location:
        print(f"{loc}: {location.latitude}, {location.longitude}")
    else:
        print(f"{loc}: Not found")

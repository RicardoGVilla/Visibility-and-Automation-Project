from global_land_mask import globe

# Montreal
lat_city, lon_city = 45.5031824, -73.5698065


print(f"montreal City: {globe.is_land(lat_city, lon_city)}") # Output: True

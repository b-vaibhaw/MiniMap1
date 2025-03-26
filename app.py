from flask import Flask, render_template, request, send_file
import openrouteservice
import folium
from geopy.geocoders import Nominatim
import os
from io import BytesIO
import config

app = Flask(__name__)

# Initialize the geolocator and OpenRouteService client
geolocator = Nominatim(user_agent="city_locator")
client = openrouteservice.Client(key=config.OPENROUTESERVICE_API_KEY)

# Function to fetch suggestions for a city name
def geocode_city_suggestions(query):
    locations = geolocator.geocode(query, exactly_one=False, timeout=10)
    if locations:
        suggestions = []
        for location in locations:
            suggestions.append(location)
        return suggestions
    return []

# Function to get the route from OpenRouteService API
def get_shortest_path(start_lat, start_lon, end_lat, end_lon):
    start_coords = (start_lon, start_lat)
    end_coords = (end_lon, end_lat)
    routes = client.directions(
        coordinates=[start_coords, end_coords],
        profile='driving-car',
        format='geojson'
    )
    route_coords = routes['features'][0]['geometry']['coordinates']
    route_map = folium.Map(location=[start_lat, start_lon], zoom_start=12)
    folium.PolyLine(locations=[(lat, lon) for lon, lat in route_coords], color='blue', weight=3, opacity=1).add_to(route_map)
    folium.Marker([start_lat, start_lon], popup="Start City", icon=folium.Icon(color='green')).add_to(route_map)
    folium.Marker([end_lat, end_lon], popup="Destination City", icon=folium.Icon(color='red')).add_to(route_map)
    return route_map

# Route for home page
@app.route('/')
def home():
    return render_template('index.html')

# Route to get the map based on user input
@app.route('/get_route', methods=['POST'])
def get_route():
    start_city = request.form.get('start_city')
    end_city = request.form.get('end_city')

    start_locations = geocode_city_suggestions(start_city)
    end_locations = geocode_city_suggestions(end_city)

    if start_locations and end_locations:
        start_lat, start_lon = start_locations[0].latitude, start_locations[0].longitude
        end_lat, end_lon = end_locations[0].latitude, end_locations[0].longitude
        route_map = get_shortest_path(start_lat, start_lon, end_lat, end_lon)

        # Save the map as an HTML file
        map_filename = "route_map.html"
        route_map.save(map_filename)

        return render_template('map.html', map_file=map_filename)
    else:
        return "Could not find cities. Please try again."

# Route to download the map
@app.route('/download_map')
def download_map():
    map_filename = "route_map.html"
    return send_file(map_filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

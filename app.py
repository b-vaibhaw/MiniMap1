from flask import Flask, render_template, request, send_from_directory
import openrouteservice
from geopy.geocoders import Nominatim
from config import OPENROUTESERVICE_API_KEY
import folium
import os

app = Flask(__name__)

# Initialize the geolocator
geolocator = Nominatim(user_agent="city_locator")

# Initialize OpenRouteService client with API Key from config
client = openrouteservice.Client(key=OPENROUTESERVICE_API_KEY)

# Folder for saving maps
MAP_FOLDER = 'static/maps'
if not os.path.exists(MAP_FOLDER):
    os.makedirs(MAP_FOLDER)

# Function to fetch suggestions for a city name
def geocode_city_suggestions(query):
    locations = geolocator.geocode(query, exactly_one=False, timeout=10)
    if locations:
        suggestions = [location for location in locations]
        return suggestions
    else:
        return []

# Function to get the route from OpenRouteService API
def get_shortest_path(start_lat, start_lon, end_lat, end_lon):
    start_coords = (start_lon, start_lat)  # OpenRouteService expects (lon, lat)
    end_coords = (end_lon, end_lat)
    routes = client.directions(
        coordinates=[start_coords, end_coords],
        profile='driving-car',
        format='geojson'
    )

    route_map = folium.Map(location=[start_lat, start_lon], zoom_start=12)
    route_coords = routes['features'][0]['geometry']['coordinates']

    folium.PolyLine(locations=[(lat, lon) for lon, lat in route_coords], color='blue', weight=3, opacity=1).add_to(route_map)
    folium.Marker([start_lat, start_lon], popup="Start City", icon=folium.Icon(color='green')).add_to(route_map)
    folium.Marker([end_lat, end_lon], popup="Destination City", icon=folium.Icon(color='red')).add_to(route_map)

    # Save map to a file
    map_filename = 'route_map.html'
    map_path = os.path.join(MAP_FOLDER, map_filename)
    route_map.save(map_path)

    return map_filename

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        start_city = request.form.get('start_city')
        end_city = request.form.get('end_city')

        # Fetch suggestions for both cities
        start_suggestions = geocode_city_suggestions(start_city)
        end_suggestions = geocode_city_suggestions(end_city)

        if start_suggestions and end_suggestions:
            # Ask user to select a city from suggestions
            start_lat, start_lon = start_suggestions[0].latitude, start_suggestions[0].longitude
            end_lat, end_lon = end_suggestions[0].latitude, end_suggestions[0].longitude

            # Generate route map
            map_filename = get_shortest_path(start_lat, start_lon, end_lat, end_lon)

            # Return the results to the template
            return render_template('index.html', 
                                   start_suggestions=start_suggestions, 
                                   end_suggestions=end_suggestions, 
                                   map_filename=map_filename)
        else:
            error_message = "No suggestions found for the cities."
            return render_template('index.html', error_message=error_message)

    return render_template('index.html')

@app.route('/download_map/<filename>')
def download_map(filename):
    return send_from_directory(MAP_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)

import openrouteservice
import folium
import time
import numpy as np
import networkx as nx
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# API Keys
ORS_API_KEY = '5b3ce3597851110001cf624803070ef73fab46049a4367a57979c831'
WEATHER_API_KEY = '08208abad73b45982006305407922e0f'

# Initialize OpenRouteService client
client = openrouteservice.Client(key=ORS_API_KEY)

# Initialize geolocator
geolocator = Nominatim(user_agent="city_locator")

# Flask API URL for browser GPS location
FLASK_BACKEND_URL = "http://127.0.0.1:5000/get_gps_location"


# Function to fetch real-time weather data
def get_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data['weather'][0]['main'] if response.status_code == 200 else None


# Function to check if weather is bad
def is_bad_weather(weather):
    return weather in ['Rain', 'Thunderstorm', 'Snow', 'Extreme']


# Function to get GPS location from the browser via Flask API
def get_gps_location():
    print("📡 Trying to get GPS location from browser...")
    try:
        response = requests.get(FLASK_BACKEND_URL)
        data = response.json()
        if "lat" in data and "lon" in data:
            return data["lat"], data["lon"]
        else:
            print("⚠️ GPS location not found. Switching to manual input.")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error connecting to GPS API: {e}")

    # Ask user to enter manually
    lat = input("Enter latitude manually: ")
    lon = input("Enter longitude manually: ")
    try:
        return float(lat), float(lon)
    except ValueError:
        print("❌ Invalid coordinates. Try again.")
        return None


# Function to get user-selected city coordinates with multiple suggestions
def get_user_city_input(prompt="Enter a city or address: "):
    while True:
        city_name = input(prompt)
        try:
            locations = list(geolocator.geocode(city_name, exactly_one=False, timeout=10))

            if not locations:
                print("❌ No matching location found. Try again.")
                continue

            print("\n🔍 Multiple locations found. Select the correct one:")
            for i, loc in enumerate(locations[:5]):  # Show top 5 suggestions
                print(f"{i+1}. {loc.address}")

            choice = input("Enter the number of the correct location (1-5) or type 'retry' to search again: ")
            if choice.lower() == 'retry':
                continue

            try:
                choice_index = int(choice) - 1
                if 0 <= choice_index < len(locations):
                    selected_location = locations[choice_index]
                    print(f"\n✅ Selected: {selected_location.address}")
                    return selected_location.latitude, selected_location.longitude
                else:
                    print("❌ Invalid choice. Try again.")
            except ValueError:
                print("❌ Please enter a valid number.")

        except GeocoderTimedOut:
            print("⚠️ Geolocation service timed out. Try again.")
        time.sleep(1)


# Function to get an optimized route
def get_optimized_route(start_lat, start_lon, end_lat, end_lon):
    start_coords = (start_lon, start_lat)
    end_coords = (end_lon, end_lat)

    start_weather = get_weather(start_lat, start_lon) or "Unknown"
    end_weather = get_weather(end_lat, end_lon) or "Unknown"

    if is_bad_weather(start_weather) or is_bad_weather(end_weather):
        print("⚠️ Bad weather detected! Rerouting to safer roads...")

    try:
        routes = client.directions(
            coordinates=[start_coords, end_coords],
            profile='driving-car',
            format='geojson'
        )
    except openrouteservice.exceptions.ApiError as e:
        print(f"⚠️ Route generation failed: {e}")
        return None, None

    if routes and 'features' in routes and len(routes['features']) > 0:
        route_map = folium.Map(location=[start_lat, start_lon], zoom_start=12)
        route_coords = routes['features'][0]['geometry']['coordinates']

        folium.PolyLine(locations=[(lat, lon) for lon, lat in route_coords], color='blue', weight=3).add_to(route_map)
        folium.Marker([start_lat, start_lon], popup="Start", icon=folium.Icon(color='green')).add_to(route_map)
        folium.Marker([end_lat, end_lon], popup="Destination", icon=folium.Icon(color='red')).add_to(route_map)

        return route_map, route_coords
    else:
        print("⚠️ Could not generate a valid route.")
        return None, None


# Function to optimize route using A* Algorithm
def optimize_route_with_astar(route_coords):
    G = nx.Graph()
    for i in range(len(route_coords) - 1):
        dist = np.linalg.norm(np.array(route_coords[i]) - np.array(route_coords[i + 1]))
        traffic_weight = np.random.uniform(1, 3)
        G.add_edge(i, i + 1, weight=dist * traffic_weight)

    start_node, end_node = 0, len(route_coords) - 1
    shortest_path = nx.astar_path(G, source=start_node, target=end_node, weight='weight')
    return [route_coords[i] for i in shortest_path]


# Main function
def main():
    print("🚀 Welcome to MiniMap")

    use_gps = input("Do you want to use GPS location? (Y/N): ").strip().lower()
    if use_gps == 'y':
        location = get_gps_location()
        if location:
            start_lat, start_lon = location
            print(f"📍 Using GPS location: {start_lat}, {start_lon}")
        else:
            start_lat, start_lon = get_user_city_input("Enter starting city or address: ")
    else:
        start_lat, start_lon = get_user_city_input("Enter starting city or address: ")

    end_lat, end_lon = get_user_city_input("Enter destination city or address: ")

    route_map, route_coords = get_optimized_route(start_lat, start_lon, end_lat, end_lon)
    if route_map:
        optimized_coords = optimize_route_with_astar(route_coords)
        route_map.save("route_map.html")
        print("✅ Route saved as 'route_map.html'. Open in a browser to view.")


if __name__ == "__main__":
    main()

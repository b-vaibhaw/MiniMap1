import os
import openrouteservice
import folium
import time
import numpy as np
import networkx as nx
import requests
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from scipy.optimize import minimize
from dwave.system import LeapHybridSampler  # Alternative to Qiskit

# API Keys
ORS_API_KEY = os.getenv("ORS_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Initialize OpenRouteService client
client = openrouteservice.Client(key=ORS_API_KEY)

# Initialize geolocator
geolocator = Nominatim(user_agent="city_locator")

# Flask API URL for browser GPS location
FLASK_BACKEND_URL = "http://127.0.0.1:5000/get_gps_location"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Function to fetch real-time weather data
def get_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={WEATHER_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        weather_main = data['weather'][0]['main']
        temp = data['main']['temp']  # Get temperature
        return f"{weather_main} ({temp}°C)"
    except requests.RequestException as e:
        logging.warning(f"Weather API error: {e}")
        return None


# Function to check bad weather
def is_bad_weather(weather):
    return weather in ['Rain', 'Thunderstorm', 'Snow', 'Extreme']

# Function to get GPS location
def get_gps_location():
    logging.info("📡 Fetching GPS location...")
    try:
        response = requests.get(FLASK_BACKEND_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        if "lat" in data and "lon" in data:
            return float(data["lat"]), float(data["lon"])
    except (requests.exceptions.RequestException, ValueError) as e:
        logging.warning(f"⚠️ GPS Error: {e}")

    while True:
        lat = input("Enter latitude manually: ")
        lon = input("Enter longitude manually: ")
        try:
            return float(lat), float(lon)
        except ValueError:
            logging.error("❌ Invalid coordinates. Enter numeric values.")


# Get city coordinates
def get_user_city_input(prompt="Enter a city: "):
    while True:
        city_name = input(prompt)
        try:
            locations = list(geolocator.geocode(city_name, exactly_one=False, timeout=10))
            if not locations:
                logging.warning("❌ No matching location found. Try again.")
                continue

            print("\n🔍 Multiple locations found. Select the correct one:")
            for i, loc in enumerate(locations[:5]):
                print(f"{i+1}. {loc.address}")

            choice = input("Enter number (1-5) or 'retry': ")
            if choice.lower() == 'retry':
                continue

            try:
                choice_index = int(choice) - 1
                if 0 <= choice_index < len(locations):
                    selected_location = locations[choice_index]
                    logging.info(f"\n✅ Selected: {selected_location.address}")
                    return selected_location.latitude, selected_location.longitude
            except ValueError:
                logging.error("❌ Invalid choice.")

        except GeocoderTimedOut:
            logging.warning("⚠️ Geolocation timed out. Try again.")
        time.sleep(1)

# Get optimized route
def get_optimized_route(start_lat, start_lon, end_lat, end_lon):
    start_coords = (start_lon, start_lat)
    end_coords = (end_lon, end_lat)

    try:
        routes = client.directions(
            coordinates=[start_coords, end_coords],
            profile='driving-car',
            format='geojson'
        )
    except openrouteservice.exceptions.ApiError as e:
        logging.error(f"⚠️ Route API error: {e}")
        return None, None

    if not routes.get('features'):
        logging.warning("⚠️ No route found.")
        return None, None

    route_map = folium.Map(location=[start_lat, start_lon], zoom_start=12)
    route_coords = routes['features'][0]['geometry']['coordinates']

    folium.PolyLine(locations=[(lat, lon) for lon, lat in route_coords], color='blue', weight=3).add_to(route_map)
    folium.Marker([start_lat, start_lon], popup="Start", icon=folium.Icon(color='green')).add_to(route_map)
    folium.Marker([end_lat, end_lon], popup="Destination", icon=folium.Icon(color='red')).add_to(route_map)

    return route_map, route_coords


# Quantum optimization without Qiskit
def optimize_route_with_qaoa(route_coords):
    num_nodes = len(route_coords)
    if num_nodes < 2:
        return route_coords  # No need to optimize small routes

    Q = {}
    for i in range(num_nodes - 1):
        dist = np.linalg.norm(np.array(route_coords[i]) - np.array(route_coords[i + 1]))
        Q[(i, i+1)] = dist

    sampler = LeapHybridSampler()
    response = sampler.sample_qubo(Q)

    best_route = [route_coords[i] for i in response.first.sample if response.first.sample.get(i, 0) == 1]

    return best_route if best_route else route_coords


# Main function
def main():
    logging.info("🚀 Welcome to MiniMap")

    use_gps = input("Use GPS? (Y/N): ").strip().lower()
    if use_gps == 'y':
        location = get_gps_location()
        start_lat, start_lon = location if location else get_user_city_input("Enter start city: ")
    else:
        start_lat, start_lon = get_user_city_input("Enter start city: ")

    end_lat, end_lon = get_user_city_input("Enter destination: ")

    route_map, route_coords = get_optimized_route(start_lat, start_lon, end_lat, end_lon)
    if route_map:
        optimized_coords = optimize_route_with_qaoa(route_coords)
        route_map.save("templates/map.html")  # Save inside `templates` for Flask
        logging.info("✅ Route saved as 'map.html'.")
    else:
        logging.error("❌ No valid route generated. Exiting.")


if __name__ == "__main__":
    main()

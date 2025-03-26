import openrouteservice
import folium
from geopy.geocoders import Nominatim
import time

# Initialize the geolocator
geolocator = Nominatim(user_agent="city_locator")

# Initialize OpenRouteService client with your API key
client = openrouteservice.Client(key='5b3ce3597851110001cf624803070ef73fab46049a4367a57979c831')

# Function to fetch suggestions for a city name
def geocode_city_suggestions(query):
    # Get multiple geocoding results
    locations = geolocator.geocode(query, exactly_one=False, timeout=10)
    if locations:
        suggestions = []
        for location in locations:
            suggestions.append(location)
        return suggestions
    else:
        print(f"No suggestions found for query: {query}")
        return []

# Function to get user input with suggestions
def get_user_city_input(prompt="Enter a city: "):
    while True:
        city_name = input(prompt)  # Get city name input
        suggestions = geocode_city_suggestions(city_name)  # Get city suggestions
        if suggestions:
            print("\nSelect the city from the suggestions by typing its number:")
            for i, location in enumerate(suggestions):
                print(f"{i+1}: {location.address}")
            
            # Get user choice
            try:
                choice = int(input("\nEnter the number corresponding to your choice (1, 2, 3...): "))
                if 1 <= choice <= len(suggestions):
                    selected_city = suggestions[choice - 1]
                    print(f"\nYou selected: {selected_city.address}")
                    return selected_city.latitude, selected_city.longitude
                else:
                    print("Invalid choice, please try again.")
            except ValueError:
                print("Invalid input, please try again.")
        else:
            print("No suggestions available. Try again.")
        
        time.sleep(1)  # Small delay before retry

# Function to get the route from OpenRouteService API
def get_shortest_path(start_lat, start_lon, end_lat, end_lon):
    # Define the start and end coordinates
    start_coords = (start_lon, start_lat)  # OpenRouteService expects (lon, lat)
    end_coords = (end_lon, end_lat)

    # Request the route from OpenRouteService
    routes = client.directions(
        coordinates=[start_coords, end_coords],
        profile='driving-car',  # 'driving-car' for car routes, you can change to 'cycling-regular', 'foot-walking', etc.
        format='geojson'
    )

    # Create a map centered on the start location
    route_map = folium.Map(location=[start_lat, start_lon], zoom_start=12)

    # Extract the route geometry (coordinates of the path)
    route_coords = routes['features'][0]['geometry']['coordinates']
    
    # Plot the route on the map
    folium.PolyLine(locations=[(lat, lon) for lon, lat in route_coords], color='blue', weight=3, opacity=1).add_to(route_map)
    
    # Mark the starting and destination locations
    folium.Marker([start_lat, start_lon], popup="Start City", icon=folium.Icon(color='green')).add_to(route_map)
    folium.Marker([end_lat, end_lon], popup="Destination City", icon=folium.Icon(color='red')).add_to(route_map)

    return route_map

# Main function to handle user input and display the map
def main():
    print("Welcome to the City Locator.")
    
    # Get the starting city coordinates
    start_city_lat, start_city_lon = get_user_city_input("Enter the starting city: ")
    
    # Get the destination city coordinates
    end_city_lat, end_city_lon = get_user_city_input("Enter the destination city: ")

    print(f"Start City Coordinates: {start_city_lat}, {start_city_lon}")
    print(f"Destination City Coordinates: {end_city_lat}, {end_city_lon}")
    
    # Get the shortest path and display the map
    route_map = get_shortest_path(start_city_lat, start_city_lon, end_city_lat, end_city_lon)
    
    # Save the map to an HTML file
    route_map.save("route_map.html")
    print("Map has been saved as 'route_map.html'. Open this file in your browser to view the path.")

if __name__ == "__main__":
    main()

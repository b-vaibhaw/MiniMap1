# MiniMap
# City Locator and Route Mapping

This project allows you to input two cities, get their geographical coordinates, and display the shortest route between them using OpenRouteService API. It leverages the `geopy` library for city geocoding and `folium` for visualizing the route on a map.

## Features

- **City Geocoding:** Use the `geopy` library to suggest possible cities based on user input.
- **Route Calculation:** Calculates the shortest route between two cities using the OpenRouteService API.
- **Route Map Visualization:** Displays the route on an interactive map using the `folium` library.
- **User-friendly Interface:** Prompts users for input and provides suggestions based on city names.
  
## Libraries Used

- **OpenRouteService:** For route calculations using the OpenRouteService API.
- **Geopy:** For geocoding city names into geographical coordinates.
- **Folium:** For visualizing the calculated route on a map.

## Setup

1. Install the required Python libraries by running:
   ```bash
   pip install openrouteservice folium geopy

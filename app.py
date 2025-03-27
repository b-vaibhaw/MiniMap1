from flask import Flask, render_template, request, jsonify, send_file
from model import get_optimized_route, optimize_route_with_astar
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables

ORS_API_KEY = os.getenv("ORS_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/route', methods=['POST'])
def fetch_route():
    data = request.json
    start_lat, start_lon = float(data['start_lat']), float(data['start_lon'])
    end_lat, end_lon = float(data['end_lat']), float(data['end_lon'])
    model = data['model']

    route_map, route_coords = get_optimized_route(start_lat, start_lon, end_lat, end_lon)
    
    if not route_map:
        return jsonify({'error': 'Failed to generate route'}), 500

    # Apply model-based optimization
    if model == 'astar':
        optimized_coords = optimize_route_with_astar(route_coords)
    elif model == 'qaoa':
        optimized_coords = route_coords  # To be replaced with actual QAOA optimization
    elif model == 'traffic-aware':
        optimized_coords = route_coords  # Future enhancement

    # Save optimized route map in static folder
    map_path = "static/map.html"
    route_map.save(map_path)

    return jsonify({'message': 'Route generated successfully', 'map_url': '/map'})

@app.route('/map')
def show_map():
    return send_file("static/map.html")

if __name__ == '__main__':
    app.run(debug=True)

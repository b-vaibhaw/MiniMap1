from flask import Flask, render_template, request, jsonify
from model import get_optimized_route, optimize_route_with_astar

app = Flask(__name__)

# Store last route to serve the map dynamically
latest_route = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/route', methods=['POST'])
def fetch_route():
    global latest_route
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
        optimized_coords = route_coords  # Placeholder for quantum model
    elif model == 'traffic-aware':
        optimized_coords = route_coords  # Future enhancement

    # Save optimized route map
    route_map.save("templates/map.html")
    latest_route = "map.html"

    return jsonify({'message': 'Route generated successfully', 'map_url': '/map'})

@app.route('/map')
def show_map():
    global latest_route
    if latest_route:
        return render_template(latest_route)
    return "No route available", 404

if __name__ == '__main__':
    app.run(debug=True)

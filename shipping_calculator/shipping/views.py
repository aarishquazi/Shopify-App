from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Define warehouse locations
warehouses = {
    "Delhi": (28.7041, 77.1025),
    "Mumbai": (19.0760, 72.8777),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Bengaluru": (12.9716, 77.5946)
}

# Get coordinates from address
def get_coordinates(address):
    geolocator = Nominatim(user_agent="shipping_calculator")
    location = geolocator.geocode(address)
    if location:
        return (location.latitude, location.longitude)
    else:
        return None

# Calculate distance
def calculate_distance(location1, location2):
    return geodesic(location1, location2).km

# Calculate shipping costs and time
def calculate_costs_and_time(distance, road_cost_per_km=5, airplane_cost_per_km=10, road_speed=60, airplane_speed=600):
    road_cost = distance * road_cost_per_km
    airplane_cost = distance * airplane_cost_per_km
    road_time = distance / road_speed
    airplane_time = distance / airplane_speed
    return road_cost, airplane_cost, road_time, airplane_time

# Get all shipping options
def get_all_shipping_options(user_location):
    shipping_options = []
    for warehouse_name, warehouse_location in warehouses.items():
        distance = calculate_distance(warehouse_location, user_location)
        road_cost, airplane_cost, road_time, airplane_time = calculate_costs_and_time(distance)
        shipping_options.append({
            "warehouse": warehouse_name,
            "distance_km": distance,
            "road": {"cost": road_cost, "time": road_time},
            "airplane": {"cost": airplane_cost, "time": airplane_time}
        })
    return shipping_options
# Find cheapest shipping option
def find_cheapest_option(shipping_options):
    cheapest_option = min(
        shipping_options,
        key=lambda x: min(x["road"]["cost"], x["airplane"]["cost"])
    )
    method = "road" if cheapest_option["road"]["cost"] < cheapest_option["airplane"]["cost"] else "airplane"
    return {
        "warehouse": cheapest_option["warehouse"],
        "method": method,
        "cost": cheapest_option[method]["cost"],
        "time": cheapest_option[method]["time"]
    }

# Find quickest shipping option
def find_quickest_option(shipping_options):
    quickest_option = min(
        shipping_options,
        key=lambda x: min(x["road"]["time"], x["airplane"]["time"])
    )
    method = "road" if quickest_option["road"]["time"] < quickest_option["airplane"]["time"] else "airplane"
    return {
        "warehouse": quickest_option["warehouse"],
        "method": method,
        "cost": quickest_option[method]["cost"],
        "time": quickest_option[method]["time"]
    }

# Normalize values (if necessary)
def normalize(value, max_value):
    return value / max_value if max_value > 0 else 0

# Calculate combined score for Multi-Criteria Optimization
def calculate_mco_score(option, max_cost_road, max_cost_airplane, max_time_road, max_time_airplane, max_distance,weight_cost=0.4, weight_time=0.3, weight_distance=0.3):
    road_cost = option["road"]["cost"]
    airplane_cost = option["airplane"]["cost"]
    
    road_time = option["road"]["time"]
    airplane_time = option["airplane"]["time"]
    
    normalized_road_cost = normalize(road_cost, max_cost_road)
    normalized_airplane_cost = normalize(airplane_cost, max_cost_airplane)
    
    normalized_road_time = normalize(road_time, max_time_road)
    normalized_airplane_time = normalize(airplane_time, max_time_airplane)
    normalized_distance = normalize(option["distance_km"], max_distance)
    
    # Combine scores for road and airplane methods
    road_score = (weight_cost * normalized_road_cost + 
                  weight_time * normalized_road_time + 
                  weight_distance * normalized_distance)
    
    airplane_score = (weight_cost * normalized_airplane_cost + 
                      weight_time * normalized_airplane_time + 
                      weight_distance * normalized_distance)
    
    # Return the method with the lower score
    return min(road_score, airplane_score)

# Find balanced shipping option using MCO
def find_balanced_option(shipping_options):
    # Get the maximum values for cost, time, and distance
    max_cost_road = max(option["road"]["cost"] for option in shipping_options)
    max_cost_airplane = max(option["airplane"]["cost"] for option in shipping_options)
    
    max_time_road = max(option["road"]["time"] for option in shipping_options)
    max_time_airplane = max(option["airplane"]["time"] for option in shipping_options)
    
    max_distance = max(option["distance_km"] for option in shipping_options)
    
    # Calculate MCO scores for each option
    scored_options = []
    for option in shipping_options:
        score = calculate_mco_score(option,  max_cost_road, max_cost_airplane, max_time_road, max_time_airplane, max_distance)
        scored_options.append((option, score))
    
    # Sort options by score (lower score is better)
    best_option = min(scored_options, key=lambda x: x[1])[0]
    
    # Determine the method (road or airplane) for the best option
    method = "road" if best_option["road"]["cost"] < best_option["airplane"]["cost"] else "airplane"
    
    return {
        "warehouse": best_option["warehouse"],
        "method": method,
        "cost": best_option[method]["cost"],
        "time": best_option[method]["time"]
    }

# API endpoint for shipping calculation
@csrf_exempt
def calculate_shipping(request):
    if request.method == "POST":
        try:
            address = request.GET.get("address")
            if not address:
                return JsonResponse({"error": "Address is required"}, status=400)
            
            user_location = get_coordinates(address)
            if not user_location:
                return JsonResponse({"error": "Could not geocode the address"}, status=400)
            
            shipping_options = get_all_shipping_options(user_location)
            cheapest = find_cheapest_option(shipping_options)
            quickest = find_quickest_option(shipping_options)
            balanced = find_balanced_option(shipping_options)
            
            return JsonResponse({
                "shipping_options": shipping_options,
                "cheapest": cheapest,
                "quickest": quickest,
                "balanced": balanced
            })
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

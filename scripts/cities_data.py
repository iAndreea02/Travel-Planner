ROMANIA_CITIES_COORDS = {
    "București": {"lat": 44.4268, "lon": 26.1025, "name": "București"},
    "Cluj-Napoca": {"lat": 46.7712, "lon": 23.6236, "name": "Cluj-Napoca"},
    "Timișoara": {"lat": 45.7489, "lon": 21.2087, "name": "Timișoara"},
    "Iași": {"lat": 47.1585, "lon": 27.6014, "name": "Iași"},
    "Constanța": {"lat": 44.1598, "lon": 28.6348, "name": "Constanța"},
    "Brașov": {"lat": 45.6427, "lon": 25.5887, "name": "Brașov"},
    "Oradea": {"lat": 47.0465, "lon": 21.9189, "name": "Oradea"},
    "Sibiu": {"lat": 45.7983, "lon": 24.1469, "name": "Sibiu"},
    "Târgu Mureș": {"lat": 46.5385, "lon": 24.5675, "name": "Târgu Mureș"},
    "Craiova": {"lat": 44.3190, "lon": 23.7967, "name": "Craiova"},
    "Galați": {"lat": 45.4353, "lon": 28.0480, "name": "Galați"},
    "Suceava": {"lat": 47.6635, "lon": 26.2732, "name": "Suceava"}
}

def filter_cities(text):
    """Filter cities that contain the text anywhere in the name"""
    text = text.lower().strip()
    normalized_text = text.replace('ț', 't').replace('ț', 't').replace('ă', 'a')
    
    matched_cities = []
    for city in ROMANIA_CITIES_COORDS.keys():
        city_norm = city.lower().replace('ț', 't').replace('ț', 't').replace('ă', 'a')
        if normalized_text in city_norm:
            matched_cities.append(city)
    
    return matched_cities

def get_city_coords(city_name):
    """Get coordinates for a city"""
    city_data = ROMANIA_CITIES_COORDS.get(city_name)
    if city_data:
        return city_data["lat"], city_data["lon"]
    return None

def normalize_city_name(city_name):
    """Get normalized name for a city"""
    city_data = ROMANIA_CITIES_COORDS.get(city_name)
    if city_data:
        return city_data["name"]
    return city_name

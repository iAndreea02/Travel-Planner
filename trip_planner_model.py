import pandas as pd
from datetime import datetime, timedelta
import spacy
import re
import os
import unicodedata
import difflib
import requests
from PIL import Image
from io import BytesIO
from ml_engine import TripRecommender
from cities_data import ROMANIA_CITIES_COORDS  # Add this import
import sys

class TripPlanner:
    def __init__(self):
        # Configure console encoding for Windows
        if sys.platform.startswith('win'):
            sys.stdout.reconfigure(encoding='utf-8')
            
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.csv_path = os.path.join(self.data_dir, 'locatii_turistice_final.csv')
        
        # Ensure data exists
        if not os.path.exists(self.csv_path):
            print("Colectez date pentru prima dată...")
            from data_collector import DataCollector
            collector = DataCollector()
            collector.collect_and_save_data()
        
        self.df = pd.read_csv(self.csv_path)
        self.nlp = spacy.load("ro_core_news_sm")
        self.recommender = TripRecommender()
        self.tourist_locations = pd.read_csv(os.path.join(self.data_dir, 'locatii_turistice.csv'))
        self.image_cache = {}
        
        self.category_emojis = {
            'muzeu': '🏛️',
            'biserica': '⛪',
            'monument': '🗽',
            'cetate': '🏰',
            'parc': '🌳',
            'shopping': '🛍️',
            'natura': '🌲',
            'plimbare': '🚶',
            'restaurant': '🍽️',
            'teatru': '🎭',
            'entertainment': '🎪',
            'general': '📍'
        }
        
        self.category_mappings = {
            "religion": {"emoji": "⛪", "icon": "church"},
            "historic architecture": {"emoji": "🏛️", "icon": "historic_building"},
            "cinemas": {"emoji": "🎬", "icon": "cinema"},
            "historic": {"emoji": "🏺", "icon": "historic"},
            "cultural": {"emoji": "🎭", "icon": "cultural"},
            "other": {"emoji": "📍", "icon": "poi"},
            "museums": {"emoji": "🏺", "icon": "museum"},
            "architecture": {"emoji": "🏛️", "icon": "building"},
            "fountains": {"emoji": "⛲", "icon": "fountain"},
            "palaces": {"emoji": "🏰", "icon": "palace"},
            "theatres and entertainments": {"emoji": "🎭", "icon": "theatre"},
            "towers": {"emoji": "🗼", "icon": "tower"},
            "cemeteries": {"emoji": "⚰️", "icon": "cemetery"},
            "biographical museums": {"emoji": "👤", "icon": "museum"},
            "fortifications": {"emoji": "🏰", "icon": "castle"},
            "urban environment": {"emoji": "🌆", "icon": "city"},
            "gardens and parks": {"emoji": "🌳", "icon": "park"},
            "view points": {"emoji": "🗻", "icon": "viewpoint"},
            "science museums": {"emoji": "🔬", "icon": "science"},
            "settlements": {"emoji": "🏘️", "icon": "settlement"},
            "natural": {"emoji": "🌲", "icon": "nature"},
            "beaches": {"emoji": "🏖️", "icon": "beach"},
            "geological formations": {"emoji": "🌋", "icon": "geology"},
            "battlefields": {"emoji": "⚔️", "icon": "battlefield"},
            "bridges": {"emoji": "🌉", "icon": "bridge"}
        }
        
        # Default fallback
        self.default_category = {"emoji": "📍", "icon": "default"}
        
        # Add caching
        self._cache = {}
        self._cache_timeout = timedelta(hours=1)
        
        # Initialize with better category weights
        self._category_weights = {
            'museums': 1.2,
            'historic': 1.15,
            'cultural': 1.1,
            'architecture': 1.05,
            'nature': 1.0
        }

    def _extract_destinations(self, text):
        """Extract multiple destinations with durations and preferences"""
        destinations = []
        text = text.lower().strip()
        
        # Words that could appear before city names
        prep_words = ['la', 'in', 'spre', 'catre', 'pentru']
        
        # Clean up the text
        for word in prep_words:
            text = text.replace(f" {word} ", " ")
        
        # Try to find city and duration
        for city in ROMANIA_CITIES_COORDS.keys():
            city_lower = city.lower()
            # Remove diacritics for comparison
            city_simple = self._normalize_text(city)
            
            if (city_lower in text or 
                city_simple in self._normalize_text(text)):
                
                # Extract duration
                duration = 2  # default
                if duration_match := re.search(
                    r'(\d+)\s*(?:zile|zi|zil|days?)', text
                ):
                    duration = int(duration_match.group(1))
                
                destinations.append({
                    'city': city,
                    'duration': duration,
                    'preferences': ['general']
                })
                break
        
        return destinations

    def _get_location_image(self, lat, lon):
        """Get location image using Wikimedia API"""
        cache_key = f"{lat},{lon}"
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
            
        try:
            # Query Wikimedia API for nearby images
            url = f"https://api.wikimedia.org/core/v1/wikipedia/en/geosearch/page?latitude={lat}&longitude={lon}&radius=1000&limit=1"
            headers = {
                "User-Agent": "TravelPlannerApp/1.0"
            }
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if "pages" in data and len(data["pages"]) > 0:
                page = data["pages"][0]
                if "thumbnail" in page:
                    image_url = page["thumbnail"]["url"]
                    self.image_cache[cache_key] = image_url
                    return image_url
            
            # Fallback to OpenStreetMap static image
            fallback_url = f"https://static-maps.openstreetmap.org/1.0/center/{lon},{lat},14/400x300.png"
            self.image_cache[cache_key] = fallback_url
            return fallback_url
        except Exception as e:
            print(f"Error fetching image: {e}")
            return None

    def _get_category_info(self, category):
        """Get emoji and icon for a category"""
        # Normalize category name
        category = category.lower().strip()
        
        # Try direct match
        if category in self.category_mappings:
            return self.category_mappings[category]
            
        # Try matching keywords
        categories = {
            "religion": ["religios", "spiritual", "biserică", "mănăstire", "credință"],
            "historic architecture": ["clădiri vechi", "monumente istorice", "istorie", "patrimoniu"],
            "cinemas": ["cinema", "film", "sală de cinema", "evenimente cinematografice"],
            "historic": ["istorie", "cultură", "evenimente istorice", "istorie"],
            "cultural": ["cultură", "arte", "expoziție", "festival", "evenimente culturale", "muzică", "dans"],
            "other": ["diverse", "locație", "interesant", "explorare", "necategorizat", "activități diverse"],
            "museums": ["muzeu", "expoziție", "artă", "istorie", "cultură"],
            "architecture": ["arhitectură", "design", "clădiri", "structuri", "construcții"],
            "fountains": ["fântână", "apă", "fontană", "loc de relaxare", "jocuri de apă"],
            "palaces": ["palat", "monarhie", "istorie", "eleganță", "lux"],
            "theatres and entertainments": ["teatru", "spectacol", "muzică", "dans", "entertainment", "divertisment", "cultură"],
            "towers": ["turn", "vârf", "panoramă", "priveliște"],
            "cemeteries": ["cemetery", "mormânt", "istorie", "cultură", "spiritualitate"],
            "biographical museums": ["muzeu biografic", "viața unui om"],
            "fortifications": ["fortificație", "castel", "cetate", "istorie"],
            "urban environment": ["urban", "oraș", "viață urbană"],
            "gardens and parks": ["grădina", "parc", "natură", "relaxare", "plimbare"],
            "view points": ["priveliște", "panoramă", "peisaj", "natură"],
            "science museums": ["muzeu stiințific", "inovație", "tehnologie", "descoperire", "experimente", "invenții"],
            "settlements": ["așezare", "comunitate", "village", "oraș", "istorie", "cultura locală"],
            "natural": ["natură", "conservare", "peisaj natural", "faţă", "floră"],
            "beaches": ["plajă", "soare", "vacanță", "relaxare", "mare", "ocean", "nisip", "natură"],
            "geological formations": ["forme geologice", "munte", "caverne", "peșteri", "natură"],
            "battlefields": ["câmp de bătălie", "istorie militară", "război", "istorie"],
            "bridges": ["pod", "construcție", "istorie"]
        }
        
        for cat, info in self.category_mappings.items():
            keywords = categories.get(cat, [])
            if any(kw in category for kw in keywords):
                return info
        
        return self.default_category

    def _get_suggested_locations(self, city, preferences, time_of_day):
        """Get location suggestions with category-based icons and prices"""
        city_locations = self.df[self.df['oras'] == city]
        
        if city_locations.empty:
            return {
                "nume locatie": "Explorare liberă",
                "categorie": "general",
                "emoji": "📍",
                "icon": "default",
                "pret_categorie": "Mediu",
                "pret_estimat": "30-70 RON"
            }
        
        # Time-appropriate categories
        time_categories = {
            'morning': ['muzeu', 'biserica', 'monument', 'cetate'],
            'afternoon': ['parc', 'shopping', 'natura', 'plimbare'],
            'evening': ['restaurant', 'teatru', 'entertainment']
        }
        
        # Filter locations
        categories = time_categories[time_of_day]
        if preferences and preferences != ['general']:
            categories.extend([p.lower() for p in preferences])
        
        matching_locations = city_locations[
            city_locations['categorie'].str.lower().isin(categories)
        ]
        
        if matching_locations.empty:
            matching_locations = city_locations
        
        # Select location and add details
        location = matching_locations.sample(n=1).iloc[0]
        category = location['categorie'].lower()
        cat_info = self._get_category_info(category)
        
        # Get price info directly from the data
        price_category = location.get('pret estimativ', 'Mediu')
        price_map = {
            'Gratuit': '0 RON',
            'Mic': '10-30 RON',
            'Mediu': '30-70 RON', 
            'Mare': '70+ RON'
        }
        
        return {
            "nume locatie": location['nume locatie'],
            "categorie": location['categorie'],
            "emoji": cat_info['emoji'],
            "icon": cat_info['icon'],
            "tip_calatorie": location.get('tip calatorie', 'general'),
            "pret_categorie": price_category,
            "pret_estimat": price_map.get(price_category, 'Preț nedefinit')
        }

    def process_user_input(self, text):
        """Process user input and generate detailed itinerary"""
        destinations = self._extract_destinations(text)
        
        if not destinations:
            return {"error": "Nu am putut identifica nicio destinație"}
        
        return self.process_destinations(destinations)

    def process_destinations(self, destinations):
        """Process destinations and generate optimized single-day itineraries"""
        if not destinations:
            return {"error": "Nu am primit nicio destinație"}
        
        daily_plans = {}
        current_day = 1
        
        for dest in destinations:
            city = dest['city']
            all_locations = self.get_locations_by_categories(city, ['all'])
            
            # Group locations by time slot preference
            morning_locations = [loc for loc in all_locations if self._is_morning_activity(loc['categorie'])]
            afternoon_locations = [loc for loc in all_locations if self._is_afternoon_activity(loc['categorie'])]
            evening_locations = [loc for loc in all_locations if self._is_evening_activity(loc['categorie'])]
            
            # Get optimized schedule
            from trip_scheduler import TripScheduler
            scheduler = TripScheduler()
            day_plans = scheduler.schedule_activities(
                city=city,
                morning_locations=morning_locations,
                afternoon_locations=afternoon_locations,
                evening_locations=evening_locations,
                requested_days=dest['duration']
            )
            
            # Add routing information
            for day_plan in day_plans:
                if 'route_coordinates' in day_plan:
                    day_plan['route_info'] = {
                        'coordinates': day_plan['route_coordinates'],
                        'color': '#FF0000',  # Red color for route
                        'width': 3,
                        'style': 'dashed'
                    }
                daily_plans[current_day] = day_plan
                current_day += 1
        
        return {
            "destinations": destinations,
            "daily_plan": daily_plans,
            "duration": current_day - 1,
            "has_routes": True  # Flag to indicate route information is available
        }

    def _is_morning_activity(self, category):
        """Check if category is suitable for morning"""
        morning_categories = ['muzeu', 'biserică', 'monument', 'cetate', 'historic']
        return any(cat in category.lower() for cat in morning_categories)
    
    def _is_afternoon_activity(self, category):
        """Check if category is suitable for afternoon"""
        afternoon_categories = ['parc', 'grădină', 'shopping', 'fountains']
        return any(cat in category.lower() for cat in afternoon_categories)
    
    def _is_evening_activity(self, category):
        """Check if category is suitable for evening"""
        evening_categories = ['restaurant', 'teatru', 'entertainment']
        return any(cat in category.lower() for cat in evening_categories)

    def _optimize_route(self, locations):
        """Optimize route between locations using nearest neighbor algorithm"""
        if not locations:
            return []
            
        unvisited = locations.copy()
        route = []
        current = unvisited.pop(0)  # Start with first location
        route.append(current)
        
        while unvisited:
            # Find nearest unvisited location
            nearest = min(unvisited, 
                        key=lambda x: self._calculate_distance(
                            current['lat'], current['lon'],
                            x['lat'], x['lon']
                        ))
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
            
        return route
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        return distance

    def _location_to_activity(self, location):
        """Convert location dict to activity format"""
        if not location:
            return None
            
        # Set price based on category
        category = location['categorie'].lower()
        if "museum" in category:
            price_category = 'Mediu'
            price_estimate = '20-50 RON'
        elif "palace" in category or "castle" in category:
            price_category = 'Mare'
            price_estimate = '40-80 RON'
        elif "park" in category or "monument" in category:
            price_category = 'Gratuit'
            price_estimate = '0 RON'
        else:
            price_category = 'Mediu'
            price_estimate = '30-70 RON'
        
        return {
            'nume_locatie': location['nume'],
            'categorie': location['categorie'],
            'latitudine': location['lat'],
            'longitudine': location['lon'],
            'pret_categorie': price_category,
            'pret_estimat': price_estimate,
            'route_order': location.get('route_order', 0)
        }

    def _split_input(self, text):
        """Split user text by commas and periods."""
        # Simple split by comma or period
        import re
        return [p.strip() for p in re.split(r'[.,]', text) if p.strip()]
    
    def _parse_phrase(self, raw_text, doc):
        """Parse a single phrase for key elements."""
        parsed_info = {
            'durata': self._extract_duration(raw_text),
            'destinatie': self._extract_destination(doc),
            'tip': self._extract_trip_type(doc),
            'buget': self._extract_budget(doc)
        }
        return parsed_info
    
    def _extract_duration(self, text):
        """Extrage durata din text"""
        duration_patterns = [
            r'(\d+)[- ]?(?:zile|zi)',
            r'(\d+)[- ]?(?:days|day)'
        ]
        
        for pattern in duration_patterns:
            if match := re.search(pattern, text):
                return int(match.group(1))
        return 2  # default duration
    
    def _normalize_text(self, text):
        """Normalizare text pentru comparare"""
        text = text.lower()
        # Remove diacritics and special characters
        replacements = {
            'ș': 's', 'ț': 't', 'ă': 'a', 'â': 'a', 'î': 'i',
            'ş': 's', 'ţ': 't', '-': '', ' ': '', ',': '', '.': '',
            'galați': 'galati', 'galaţi': 'galati'  # Add specific handling for Galati
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text.strip()

    def _extract_destination(self, doc):
        """Extrage destinația din text folosind matching flexibil"""
        text = doc.text.lower()
        cities = {city.lower(): city for city in self.df['oras'].unique()}
        
        # City patterns with better matches
        city_patterns = {
            'cluj': 'Cluj-Napoca',
            'napoca': 'Cluj-Napoca',
            'timis': 'Timișoara',
            'bras': 'Brașov',
            'bucur': 'București',
            'const': 'Constanța',
            'galati': 'Galați',
            'gala': 'Galați',
            'targ': 'Târgu Mureș',
            'mures': 'Târgu Mureș',
            'suceav': 'Suceava',
            'iasi': 'Iași',
            'ias': 'Iași',
            'orad': 'Oradea',
            'sibiu': 'Sibiu',
            'craiov': 'Craiova'
        }
        
        # Try exact match first
        for word in text.split():
            normalized = self._normalize_text(word)
            if normalized in cities:
                return cities[normalized]
        
        # Then try partial matches
        words = text.split()
        for word in words:
            normalized = self._normalize_text(word)
            if len(normalized) < 3:  # Skip very short words
                continue
                
            # Check if word contains any city pattern
            for pattern, full_name in city_patterns.items():
                if pattern in normalized:
                    matching_cities = [
                        city for city in cities.values()
                        if pattern in self._normalize_text(city.lower())
                    ]
                    if matching_cities:
                        return matching_cities[0]
            
            # Try fuzzy matching if no pattern match
            closest = self._get_closest_city(normalized, list(cities.values()))
            if closest:
                return closest
        
        return None

    def _get_closest_city(self, word, cities):
        """Găsește cel mai apropiat oraș folosind distanța Levenshtein"""
        min_distance = float('inf')
        closest_city = None
        
        for city in cities:
            norm_city = self._normalize_text(city)
            distance = self._levenshtein_distance(word, norm_city)
            if distance < min_distance and distance <= len(word) // 2:
                min_distance = distance
                closest_city = city
                
        return closest_city
    
    def _levenshtein_distance(self, s1, s2):
        """Calculează distanța Levenshtein între două șiruri"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

    def _extract_trip_type(self, doc):
        """Identifică tipul de călătorie dorit"""
        keywords = {
            'munte': 'mountain',
            'mare': 'beach',
            'plaja': 'beach',
            'relax': 'relaxation',
            'cultura': 'culture',
            'istorie': 'history'
        }
        
        found_types = []
        for token in doc:
            if token.text in keywords:
                found_types.append(keywords[token.text])
        
        return found_types or ['general']
    
    def _extract_budget(self, doc):
        """Extrage și simplifică bugetul în categorii"""
        text = doc.text.lower()
        
        if any(word in text for word in ['ieftin', 'economic', 'low']):
            return 'mic'
        elif any(word in text for word in ['scump', 'lux', 'premium']):
            return 'mare'
        return 'mediu'  # default

    def get_recommendations_for_text(self, text_input, city):
        """Get recommendations based on text input and city"""
        try:
            # Use safe ASCII characters for debug output
            print("\nProcessing recommendations:")
            print(f"City: {city.encode('ascii', 'replace').decode()}")
            print(f"Input: {text_input.encode('ascii', 'replace').decode()}")
            print("-" * 50)
            
            recommendations = self.recommender.get_recommendations(text_input, city)
            
            if not recommendations:
                print("No recommendations found!")
                return []
            
            # Format recommendations for display
            formatted_recommendations = []
            print("\nFormatting recommendations:")
            for loc in recommendations:
                rec = {
                    'nume locatie': loc['denumire'],
                    'categorie': loc['categorie'],
                    'latitudine': loc.get('latitudine', 0),
                    'longitudine': loc.get('longitudine', 0),
                    'pret_categorie': self._get_price_category(loc['categorie']),
                    'pret_estimat': self._get_price_estimate(loc['categorie']),
                    'tip_calatorie': loc.get('tip_calatorie', 'general'),
                    'emoji': self._get_category_info(loc['categorie'])['emoji']
                }
                formatted_recommendations.append(rec)
                # Safe printing of location names
                print(f"Found: {rec['nume locatie'].encode('ascii', 'replace').decode()} "
                      f"({rec['categorie'].encode('ascii', 'replace').decode()})")
            
            return formatted_recommendations
            
        except Exception as e:
            print(f"Error in get_recommendations_for_text: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
            
    def _get_price_estimate(self, category):
        """Get price estimate based on category"""
        category = category.lower()
        if "museum" in category:
            return "20-50 RON"
        elif "palace" in category or "castle" in category:
            return "40-80 RON"
        elif "park" in category or "monument" in category:
            return "Gratuit"
        return "30-70 RON"

    def _get_price_category(self, category):
        """Get price category based on category"""
        category = category.lower()
        if "museum" in category:
            return "Mediu"
        elif "palace" in category or "castle" in category:
            return "Mare"
        elif "park" in category or "monument" in category:
            return "Gratuit"
        return "Mediu"

    def get_locations_by_categories(self, city, categories):
        """Get locations in city matching given categories"""
        city_locations = self.df[self.df['oras'] == city]
        matching_locations = []
        
        for _, location in city_locations.iterrows():
            category = location['categorie'].lower()
            for target_cat in categories:
                if target_cat.lower() in category:
                    matching_locations.append({
                        'nume': location['denumire'],
                        'categorie': location['categorie'],
                        'rating': location.get('rating_general', 0),
                        'reviews': location.get('nr_recenzii', 0),
                        'lat': location.get('latitudine', 0),
                        'lon': location.get('longitudine', 0)
                    })
                    break
        
        return matching_locations

    def _get_cached_data(self, key):
        """Get cached data if valid"""
        if key in self._cache:
            timestamp, data = self._cache[key]
            if datetime.now() - timestamp < self._cache_timeout:
                return data
        return None

    def _cache_data(self, key, data):
        """Cache data with timestamp"""
        self._cache[key] = (datetime.now(), data)

    def calculate_location_score(self, location, user_preferences):
        """Enhanced scoring algorithm"""
        try:
            base_score = 0
            weights = {
                'category_match': 0.4,
                'rating': 0.3,
                'popularity': 0.2,
                'accessibility': 0.1
            }
            
            # Category match
            category = location['categorie'].lower()
            category_score = self._category_weights.get(category, 1.0)
            
            # Rating and popularity
            rating_score = float(location['rating_general']) / 5.0
            popularity_score = min(float(location['nr_recenzii']) / 1000, 1.0)
            
            # Accessibility score based on price and duration
            accessibility_score = self._calculate_accessibility(location)
            
            # Calculate weighted score
            final_score = sum([
                category_score * weights['category_match'],
                rating_score * weights['rating'],
                popularity_score * weights['popularity'],
                accessibility_score * weights['accessibility']
            ])
            
            return min(max(final_score, 0.0), 1.0)
            
        except Exception as e:
            print(f"Scoring error: {e}")
            return 0.0

    def _calculate_accessibility(self, location):
        """Calculate accessibility score"""
        price_scores = {
            'Gratuit': 1.0,
            'Mic': 0.8,
            'Mediu': 0.6,
            'Mare': 0.4
        }
        
        duration_penalty = min(location['durata_minima'] / 10.0, 1.0)
        price_score = price_scores.get(location['pret_categorie'], 0.5)
        
        return (price_score + (1.0 - duration_penalty)) / 2.0

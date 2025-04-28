import os
import pandas as pd
import requests
import time
import random
import sys

class DataCollector:
    def __init__(self):
        self.api_key = "5ae2e3f221c38a28845f05b6d39ea85b65163d209754a67b5f62156e"
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.ensure_data_directory()
        
        # Ensure proper encoding
        import codecs
        self.encoding = 'utf-8-sig'  # Use UTF-8 with BOM for Windows compatibility
        if sys.platform.startswith('win'):
            sys.stdout.reconfigure(encoding='utf-8')

    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def collect_and_save_data(self):
        print("Collecting data...")  # Safe ASCII message
        
        orase = ["București", "Cluj-Napoca", "Timișoara", "Iași", "Constanța",
                 "Brașov", "Oradea", "Sibiu", "Târgu Mureș", "Craiova",
                 "Galați", "Suceava"]
        
        toate_locatiile = []
        
        for oras in orase:
            print(f"📍 Colectez date pentru {oras}...")
            
            # Get coordinates
            geo = requests.get(
                f"https://api.opentripmap.com/0.1/en/places/geoname?name={oras}&apikey={self.api_key}"
            ).json()
            
            lat, lon = geo.get("lat"), geo.get("lon")
            if not lat or not lon:
                print(f"⚠️ Nu am găsit coordonate pentru {oras}")
                continue

            # Get locations
            radius_url = f"https://api.opentripmap.com/0.1/en/places/radius?radius=10000&lon={lon}&lat={lat}&limit=100&apikey={self.api_key}"
            features = requests.get(radius_url).json().get("features", [])

            for f in features:
                location_data = self.process_location(f, oras)
                if location_data:
                    toate_locatiile.append(location_data)
                time.sleep(0.3)  # Avoid API rate limiting

        # Save with explicit encoding
        df = pd.DataFrame(toate_locatiile)
        csv_path = os.path.join(self.data_dir, 'locatii_turistice_final.csv')
        df.to_csv(csv_path, index=False, encoding=self.encoding)
        print(f"Data saved to {csv_path}")
        return csv_path

    def process_location(self, feature, oras):
        """Process individual location data"""
        xid = feature["properties"]["xid"]
        detail_url = f"https://api.opentripmap.com/0.1/en/places/xid/{xid}?apikey={self.api_key}"
        detail = requests.get(detail_url).json()

        if not detail.get("name"):
            return None

        # Process categories and keywords
        categorie = self.get_category(detail)
        cuvinte_cheie = self.get_keywords(categorie)
        tip_calatorie = self.get_travel_type(categorie)

        return {
            "denumire": detail.get("name", ""),
            "oras": oras,
            "rating general": round(random.uniform(3.5, 5.0), 1),
            "nr_recenzii": random.randint(50, 3000),
            "categorie": categorie,
            "popularitate": random.randint(1, 3),
            "sezon recomandat": self.get_season(categorie),
            "longitudine": detail.get("point", {}).get("lon", ""),
            "latitudine": detail.get("point", {}).get("lat", ""),
            "pret estimativ": self.get_price_category(categorie),
            "tip calatorie": tip_calatorie,
            "cuvinte cheie": cuvinte_cheie
        }

    def get_category(self, detail):
        """Extract and process category"""
        categorii = detail.get("kinds", "").split(",")[0]
        return categorii.replace("_", " ").capitalize() if categorii else "Necunoscut"

    def get_season(self, category):
        """Determine recommended season"""
        category = category.lower()
        if "beach" in category or "coast" in category:
            return "Cald"
        elif "ski" in category or "mountain" in category:
            return "Rece"
        return "Oricând"

    def get_price_category(self, category):
        """Determine price category based on type"""
        category = category.lower()
        if "museum" in category or "theatre" in category:
            return "Mediu"
        elif "park" in category or "monument" in category:
            return "Gratuit"
        elif "palace" in category or "castle" in category:
            return "Mare"
        return "Mic"

    def get_travel_type(self, category):
        """Determine travel type based on category and location type"""
        category = category.lower()
        
        # Default distribution of trip types based on category
        if "museum" in category or "historic" in category or "architecture" in category:
            return "City Break"
        elif "church" in category or "monastery" in category or "park" in category:
            return "Relaxare"  
        elif "castle" in category or "fortification" in category or "ruins" in category:
            return "Circuit"
        
        # Random selection for other categories with weighted distribution:
        # - City Break: 40%
        # - Relaxare: 35%
        # - Circuit: 25%
        import random
        trip_types = ["City Break", "Relaxare", "Circuit"]
        weights = [0.4, 0.35, 0.25]
        return random.choices(trip_types, weights=weights)[0]

    def get_keywords(self, category):
        """Generate relevant keywords"""
        category = category.lower()
        if "museum" in category:
            return ["muzeu", "cultură", "istorie", "artă"]
        elif "nature" in category:
            return ["natură", "peisaje", "drumeție", "relaxare"]
        return ["turism", "călătorie", "explorare"]

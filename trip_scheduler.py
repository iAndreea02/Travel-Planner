from typing import List, Dict, Any
import numpy as np
from math import radians, sin, cos, sqrt, atan2

class TripScheduler:
    def __init__(self):
        self.time_slots = ['morning', 'afternoon', 'evening']

    def schedule_activities(self, city: str, 
                          morning_locations: List[Dict], 
                          afternoon_locations: List[Dict],
                          evening_locations: List[Dict],
                          requested_days: int) -> List[Dict]:
        """Schedule activities for a single day with optimized route"""
        scheduled_days = []
        
        # Combine all locations
        all_available_locations = {
            'morning': morning_locations,
            'afternoon': afternoon_locations,
            'evening': evening_locations
        }
        
        # For each day, create an optimized schedule
        for day in range(requested_days):
            day_plan = {
                "city": city,
                "morning": None,
                "afternoon": None,
                "evening": None,
                "route": [],  # Store complete route for the day
                "route_coordinates": []  # Store coordinates for map drawing
            }
            
            # Select one location for each time slot
            current_location = None
            day_locations = []
            
            for time_slot in self.time_slots:
                pool = all_available_locations[time_slot]
                if not pool:
                    continue
                
                # Select best next location
                selected = self._select_best_location(pool, current_location, time_slot)
                if selected:
                    day_locations.append((time_slot, selected))
                    current_location = selected
                    pool.remove(selected)  # Remove from available pool
            
            # Optimize route between selected locations
            if day_locations:
                # Sort locations by time slot but consider distances
                optimized_route = self._optimize_day_route([loc for _, loc in day_locations])
                route_coords = [(loc['lat'], loc['lon']) for loc in optimized_route]
                
                # Assign locations to time slots while preserving optimal route
                for time_slot, location in zip(self.time_slots, optimized_route):
                    day_plan[time_slot] = self._location_to_activity(location)
                
                # Store route information
                day_plan["route"] = optimized_route
                day_plan["route_coordinates"] = route_coords
            
            scheduled_days.append(day_plan)
            
            # If we have more days, move remaining locations back to pools
            remaining = []
            for slot, locations in all_available_locations.items():
                remaining.extend(locations)
            
            if remaining and day < requested_days - 1:
                # Redistribute remaining locations for next days
                for slot in self.time_slots:
                    all_available_locations[slot] = [
                        loc for loc in remaining 
                        if self._is_suitable_for_timeslot(loc, slot)
                    ]
        
        return scheduled_days

    def _select_best_location(self, pool: List[Dict], 
                            last_location: Dict, 
                            time_slot: str) -> Dict:
        """Select best location based on distance and time slot"""
        if not pool:
            return None
            
        if not last_location:
            return pool[0]  # Return first location if no previous location
            
        # Calculate scores for each location
        scores = []
        for loc in pool:
            distance_score = 1.0 - (
                self._calculate_distance(
                    last_location['lat'], last_location['lon'],
                    loc['lat'], loc['lon']
                ) / 10.0  # Normalize by 10km
            )
            time_score = self._get_time_slot_score(loc, time_slot)
            
            total_score = (distance_score * 0.7) + (time_score * 0.3)
            scores.append((loc, total_score))
        
        # Return location with highest score
        return max(scores, key=lambda x: x[1])[0]

    def _calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c

    def _get_time_slot_score(self, location: Dict, time_slot: str) -> float:
        """Score location suitability for time slot"""
        category = location['categorie'].lower()
        
        time_preferences = {
            'morning': ['muzeu', 'biserică', 'monument', 'cetate', 'historic'],
            'afternoon': ['parc', 'grădină', 'shopping', 'fountains'],
            'evening': ['restaurant', 'teatru', 'entertainment']
        }
        
        # Check if category matches time slot preferences
        slot_keywords = time_preferences[time_slot]
        if any(keyword in category for keyword in slot_keywords):
            return 1.0
        return 0.5

    def _optimize_day_route(self, locations: List[Dict]) -> List[Dict]:
        """Optimize route for a single day considering time slots"""
        if not locations:
            return []
        
        # Start with the first location
        route = [locations[0]]
        remaining = locations[1:]
        
        while remaining:
            current = route[-1]
            # Find nearest location that fits time constraints
            best_next = min(
                remaining,
                key=lambda x: self._calculate_travel_score(current, x, len(route))
            )
            route.append(best_next)
            remaining.remove(best_next)
        
        return route

    def _calculate_travel_score(self, loc1: Dict, loc2: Dict, position: int) -> float:
        """Calculate travel score considering both distance and time slot suitability"""
        distance = self._calculate_distance(
            loc1['lat'], loc1['lon'],
            loc2['lat'], loc2['lon']
        )
        
        # Time slot penalty (0 to 1, where 0 is perfect time slot match)
        time_penalties = {
            0: {'morning': 0, 'afternoon': 0.5, 'evening': 1},
            1: {'morning': 0.5, 'afternoon': 0, 'evening': 0.5},
            2: {'morning': 1, 'afternoon': 0.5, 'evening': 0}
        }
        
        category = loc2['categorie'].lower()
        time_score = 0
        
        if position < len(self.time_slots):
            target_slot = self.time_slots[position]
            time_score = time_penalties[position].get(target_slot, 0.5)
        
        # Combine distance and time scores (weighted)
        return distance * 0.7 + time_score * 0.3

    def _is_suitable_for_timeslot(self, location: Dict, time_slot: str) -> bool:
        """Check if location is suitable for given time slot"""
        category = location['categorie'].lower()
        
        slot_categories = {
            'morning': ['muzeu', 'biserică', 'monument', 'cetate', 'historic'],
            'afternoon': ['parc', 'grădină', 'shopping', 'fountains'],
            'evening': ['restaurant', 'teatru', 'entertainment']
        }
        
        return any(cat in category for cat in slot_categories.get(time_slot, []))

    def _location_to_activity(self, location: Dict) -> Dict:
        """Convert location dict to activity format with additional routing info"""
        category = location['categorie'].lower()
        
        price_mapping = {
            'museum': ('Mediu', '20-50 RON'),
            'palace': ('Mare', '40-80 RON'),
            'park': ('Gratuit', '0 RON'),
            'monument': ('Gratuit', '0 RON')
        }
        
        # Get price category and estimate
        for key, (price_cat, price_est) in price_mapping.items():
            if key in category:
                price_category = price_cat
                price_estimate = price_est
                break
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
            'coordinates': (location['lat'], location['lon']),
            'optimal_order': location.get('route_order', 0),
            'distance_to_next': location.get('distance_to_next', 0)
        }

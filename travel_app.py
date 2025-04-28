import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
import json
from PIL import Image, ImageTk
import requests
from io import BytesIO
import tkintermapview
import webbrowser
from urllib.parse import quote
import polyline

class TravelPlannerApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Travel Planner")
        self.geometry("1200x800")
        
        # Data structure for ML integration
        self.user_preferences = {
            'liked_locations': [],
            'preferred_types': [],
            'price_range': (0, 1000),
            'ratings': []
        }
        
        self.setup_ui()
        self.load_sample_data()
    
    def setup_ui(self):
        # Create main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=YES)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=BOTH, expand=YES)
        
        # Discover tab
        self.discover_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.discover_frame, text="✨ Discover")
        self.setup_discover_view()
        
        # Map tab
        self.map_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.map_frame, text="🗺️ Map View")
        self.setup_map_view()
    
    def setup_discover_view(self):
        # Left sidebar for filters
        filters = ttk.LabelFrame(self.discover_frame, text="Filters", padding=10)
        filters.pack(side=LEFT, fill=Y, padx=5, pady=5)
        
        # Rating filter
        ttk.Label(filters, text="Minimum Rating").pack(pady=5)
        self.rating_scale = ttk.Scale(filters, from_=1, to=5, value=4)
        self.rating_scale.pack(fill=X, pady=5)
        
        # Type filter
        ttk.Label(filters, text="Travel Type").pack(pady=5)
        types = ["City Break", "Circuit", "Shopping", "Adventure"]
        self.type_vars = {}
        for t in types:
            var = ttk.BooleanVar(value=True)
            self.type_vars[t] = var
            ttk.Checkbutton(filters, text=t, variable=var).pack()
        
        # Main content area
        content = ScrolledFrame(self.discover_frame)
        content.pack(side=LEFT, fill=BOTH, expand=YES, padx=5, pady=5)
        self.content_frame = content
    
    def setup_map_view(self):
        # Create map frame
        map_container = ttk.Frame(self.map_frame)
        map_container.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        # Search frame
        search_frame = ttk.Frame(map_container)
        search_frame.pack(fill=X, pady=5)

        ttk.Label(search_frame, text="Search:").pack(side=LEFT, padx=5)
        self.location_entry = ttk.Entry(search_frame, width=40)
        self.location_entry.pack(side=LEFT, padx=5)

        ttk.Button(search_frame, text="Search", 
                  command=self.search_location).pack(side=LEFT, padx=5)
        ttk.Button(search_frame, text="📍 Current Location",
                  command=self.get_current_location).pack(side=LEFT, padx=5)

        # Route frame
        route_frame = ttk.Frame(map_container)
        route_frame.pack(fill=X, pady=5)

        ttk.Label(route_frame, text="Start:").pack(side=LEFT, padx=5)
        self.start_entry = ttk.Entry(route_frame, width=30)
        self.start_entry.pack(side=LEFT, padx=5)

        ttk.Label(route_frame, text="End:").pack(side=LEFT, padx=5)
        self.end_entry = ttk.Entry(route_frame, width=30)
        self.end_entry.pack(side=LEFT, padx=5)

        ttk.Button(route_frame, text="Calculate Route",
                  command=self.calculate_route).pack(side=LEFT, padx=5)

        # Map controls
        controls_frame = ttk.Frame(map_container)
        controls_frame.pack(fill=X, pady=5)

        ttk.Label(controls_frame, text="Map Style:").pack(side=LEFT, padx=5)
        for style in ["Normal", "Satellite", "Terrain"]:
            ttk.Button(controls_frame, text=style,
                      command=lambda s=style: self.change_map(s.lower())
                      ).pack(side=LEFT, padx=2)

        # Map widget
        self.map_widget = tkintermapview.TkinterMapView(map_container)
        self.map_widget.pack(fill=BOTH, expand=YES)

        # Initialize map
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        self.get_current_location()

    def validate_coordinates(self, coord_str):
        try:
            if ',' in coord_str:
                lat, lon = map(float, coord_str.split(','))
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
        except:
            return None
        return None

    def get_location_info(self):
        try:
            response = requests.get('http://ip-api.com/json/')
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'lat': float(data['lat']),
                        'lon': float(data['lon']),
                        'city': data['city']
                    }
        except:
            return None
        return None

    def get_current_location(self):
        location = self.get_location_info()
        if location:
            lat, lon = location['lat'], location['lon']
            # Update the location entry with coordinates
            self.location_entry.delete(0, tk.END)
            self.location_entry.insert(0, f"{lat}, {lon}")
            self.map_widget.set_position(lat, lon)
            self.map_widget.set_zoom(14)
            self.map_widget.set_marker(lat, lon, text=f"You are here ({location['city']})")
            return True
        return False

    def search_location(self):
        try:
            location = self.location_entry.get().strip()
            coords = self.validate_coordinates(location)
            if coords:
                lat, lon = coords
                self.map_widget.set_position(lat, lon)
                self.map_widget.set_zoom(13)
                self.map_widget.set_marker(lat, lon, text=f"Location: {lat}, {lon}")
                return
            
            coords = self.map_widget.set_address(location)
            if coords:
                self.map_widget.set_position(coords[0], coords[1])
                self.map_widget.set_zoom(13)
                self.map_widget.set_marker(coords[0], coords[1], text=location)
        except:
            messagebox.showerror("Error", "Location not found")

    def calculate_route(self):
        try:
            self.map_widget.delete_all_path()
            self.map_widget.delete_all_marker()
            
            start_loc = self.start_entry.get().strip()
            end_loc = self.end_entry.get().strip()
            
            start_coords = self.validate_coordinates(start_loc) or self.map_widget.set_address(start_loc)
            end_coords = self.validate_coordinates(end_loc) or self.map_widget.set_address(end_loc)
            
            if start_coords and end_coords:
                self.map_widget.set_marker(start_coords[0], start_coords[1], text=f"Start: {start_loc}")
                self.map_widget.set_marker(end_coords[0], end_coords[1], text=f"End: {end_loc}")
                self.map_widget.set_path([start_coords, end_coords])
                self.map_widget.fit_bounds([start_coords, end_coords])
        except:
            messagebox.showerror("Error", "Could not calculate route")

    def change_map(self, map_type):
        if map_type == "normal":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        elif map_type == "satellite":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        elif map_type == "terrain":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
    
    def create_travel_card(self, data):
        card = ttk.Frame(self.content_frame)
        card.pack(fill=X, padx=5, pady=5)
        
        # Title and rating
        header = ttk.Frame(card)
        header.pack(fill=X, pady=5)
        
        ttk.Label(
            header,
            text=data["title"],
            font=("Helvetica", 14, "bold")
        ).pack(side=LEFT)
        
        rating = "⭐" * int(float(data["rating"]))
        ttk.Label(header, text=rating).pack(side=RIGHT)
        
        # Details
        ttk.Label(card, text=f"📍 {data['location']}").pack(anchor=W)
        ttk.Label(card, text=f"🎯 {data['type']}").pack(anchor=W)
        ttk.Label(card, text=f"💰 {data['price']}€").pack(anchor=W)
        ttk.Label(card, text=f"⏱ {data['duration']} days").pack(anchor=W)
        
        # Buttons
        btn_frame = ttk.Frame(card)
        btn_frame.pack(fill=X, pady=5)
        
        ttk.Button(
            btn_frame,
            text="Save",
            command=lambda: self.save_preference(data)
        ).pack(side=LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="View on Map",
            command=lambda: self.show_on_map(data)
        ).pack(side=LEFT, padx=2)
        
        ttk.Separator(self.content_frame).pack(fill=X, pady=5)
    
    def load_sample_data(self):
        sample_data = [
            {
                "title": "Historic Bucharest Tour",
                "location": "Bucharest",
                "type": "City Break",
                "rating": "4.8",
                "price": 299,
                "duration": 3
            },
            {
                "title": "Black Sea Adventure",
                "location": "Constanta",
                "type": "Circuit",
                "rating": "4.5",
                "price": 499,
                "duration": 5
            },
            {
                "title": "Shopping in Cluj",
                "location": "Cluj-Napoca",
                "type": "Shopping",
                "rating": "4.6",
                "price": 399,
                "duration": 2
            }
        ]
        
        for item in sample_data:
            self.create_travel_card(item)
    
    def save_preference(self, data):
        """Save user preference for ML training"""
        self.user_preferences['liked_locations'].append(data['location'])
        self.user_preferences['ratings'].append(float(data['rating']))
        self.user_preferences['preferred_types'].append(data['type'])
    
    def show_on_map(self, data):
        """Show location on map"""
        self.notebook.select(1)  # Switch to map tab
        coords = self.map_widget.set_address(f"{data['location']}, Romania")
        if coords:
            self.map_widget.set_position(coords[0], coords[1])
            self.map_widget.set_zoom(13)
            self.map_widget.set_marker(coords[0], coords[1], text=data['title'])

if __name__ == "__main__":
    app = TravelPlannerApp()
    app.mainloop()

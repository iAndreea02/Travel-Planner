import tkinter as tk
from tkinter import ttk, messagebox
import tkintermapview
import requests
import webbrowser
from cities_data import ROMANIA_CITIES_COORDS, filter_cities
import polyline

class SearchableCombobox(ttk.Combobox):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<<ComboboxSelected>>', self._on_select)
        self._all_values = kwargs.get('values', [])

    def _on_keyrelease(self, event):
        # Don't update for navigation keys
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Tab'):
            return

        value = self.get().strip()
        if value:
            # Find matches containing the typed text
            matches = [x for x in self._all_values 
                     if value.lower() in x.lower()]
            if matches:
                self['values'] = matches
                self.event_generate('<Down>')  # Show dropdown
        else:
            self['values'] = self._all_values

    def _on_select(self, event):
        # Reset values list when an item is selected
        self['values'] = self._all_values

class MapView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        
        # Left panel for controls
        left_panel = ttk.Frame(self)
        left_panel.pack(side="left", fill="y", padx=10, pady=10)
        
        # Search section with Romanian text
        search_section = ttk.LabelFrame(left_panel, text="Caută pe hartă", padding=10)
        search_section.pack(fill="x", pady=(0, 10))
        
        self.location_entry = SearchableCombobox(
            search_section, 
            width=30,
            values=list(ROMANIA_CITIES_COORDS.keys())
        )
        self.location_entry.pack(side="left", padx=5)
        
        ttk.Button(search_section, text="Caută", width=8,
                  command=self.search_location).pack(side="left")
        ttk.Button(search_section, text="Locația mea", width=8,
                  command=self.get_current_location).pack(side="left", padx=(5,0))

        # Route section with Romanian text
        route_section = ttk.LabelFrame(left_panel, text="Planificare traseu", padding=10)
        route_section.pack(fill="x", pady=(0, 10))
        
        ttk.Label(route_section, text="Punct de plecare:").pack(anchor="w")
        self.start_entry = SearchableCombobox(
            route_section, 
            width=35,
            values=list(ROMANIA_CITIES_COORDS.keys()
        ))
        self.start_entry.pack(fill="x", pady=(0, 10))
        
        ttk.Label(route_section, text="Destinație:").pack(anchor="w") 
        self.end_entry = SearchableCombobox(
            route_section,
            width=35, 
            values=list(ROMANIA_CITIES_COORDS.keys())
        )
        self.end_entry.pack(fill="x", pady=(0, 10))
        
        button_frame = ttk.Frame(route_section)
        button_frame.pack(fill="x")
        ttk.Button(button_frame, text="Calculează traseul",
                  command=self.calculate_route).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Adaugă oprire",
                  command=self.add_waypoint).pack(side="left")
        
        # Waypoints container
        self.waypoints_frame = ttk.Frame(route_section)
        self.waypoints_frame.pack(fill="x", pady=(10,0))
        self.waypoints = []

        # Map controls with Romanian text
        controls_section = ttk.LabelFrame(left_panel, text="Control hartă", padding=10)
        controls_section.pack(fill="x")
        
        ttk.Label(controls_section, text="Tip vizualizare:").pack(anchor="w")
        styles_frame = ttk.Frame(controls_section)
        styles_frame.pack(fill="x", pady=5)
        for style in ["Normală", "Satelit", "Teren"]:
            ttk.Button(styles_frame, text=style,
                      command=lambda s=style.lower(): self.change_map(s),
                      width=10).pack(side="left", padx=2)

        ttk.Button(controls_section, text="Afișare puncte de interes",
                  command=self.toggle_attractions).pack(fill="x", pady=(10,0))

        # Legend section with colored circles
        legend = ttk.LabelFrame(left_panel, text="Legendă hartă", padding=10)
        legend.pack(fill="x", pady=(10,0))
        
        # Define a single color mapping that will be used for both legend and markers
        self.category_colors = {
            'Religion': '#FF0000',      # Red
            'Cultural': '#4285F4',      # Blue
            'Historic': '#FBBC05',      # Yellow
            'Museums': '#34A853',       # Green
            'Architecture': '#EA4335',  # Red
            'Theatres': '#AA00FF',      # Purple
            'Cinemas': '#FF6D01',       # Orange
            'Other': '#757575',         # Gray
            'Route_Start': 'green',     # Route colors
            'Route_Stop': 'orange',
            'Route_End': 'red'
        }
        
        # Update legend entries to use Romanian text
        legends = [
            (self.category_colors['Religion'], "Lăcașuri Religioase"),
            (self.category_colors['Cultural'], "Locuri Culturale"),
            (self.category_colors['Historic'], "Situri Istorice"),
            (self.category_colors['Museums'], "Muzee"),
            (self.category_colors['Architecture'], "Arhitectură"),
            (self.category_colors['Theatres'], "Teatre"),
            (self.category_colors['Cinemas'], "Cinematografe"),
            (self.category_colors['Other'], "Alte Atracții"),
            (self.category_colors['Route_Start'], "Punct Pornire"),
            (self.category_colors['Route_Stop'], "Punct Oprire"),
            (self.category_colors['Route_End'], "Destinație")
        ]
        
        # Using existing category_colors for consistent colors
        for color, desc in legends:
            legend_frame = ttk.Frame(legend)
            legend_frame.pack(fill="x", pady=2)
            
            # Create circle using Canvas
            circle_canvas = tk.Canvas(
                legend_frame, 
                width=15, 
                height=15,
                bg=self.winfo_toplevel()['background'],
                highlightthickness=0
            )
            circle_canvas.pack(side="left", padx=5)
            
            # Draw filled circle with border
            circle_canvas.create_oval(
                2, 2, 13, 13,  # Smaller circle within canvas
                fill=color,
                outline='gray75',
                width=1
            )
            
            ttk.Label(
                legend_frame, 
                text=desc,
                font=('Helvetica', 10)
            ).pack(side="left", padx=5)

        # Main map area
        map_area = ttk.Frame(self)
        map_area.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        self.map_widget = tkintermapview.TkinterMapView(map_area)
        self.map_widget.pack(fill="both", expand=True)

        # Route info at bottom
        self.route_info_frame = ttk.LabelFrame(map_area, text="Informații traseu", padding=10)
        self.route_info_frame.pack(fill="x", pady=(10,0))
        self.route_info_frame.pack_forget()
        
        self.steps_list = tk.Listbox(self.route_info_frame, height=4)
        self.steps_list.pack(fill="x")

        # Initialize map
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        
        # Initialize other variables
        self.attractions_visible = False
        self.attraction_markers = []
        
        # Initialize to default location
        if not self.get_current_location():
            messagebox.showerror("Eroare", "Nu s-a putut determina locația curentă")
            self.map_widget.set_position(45.4353, 28.0480)
            self.map_widget.set_zoom(13)

    def add_waypoint(self):
        """Add a waypoint to the route"""
        waypoint_row = ttk.Frame(self.waypoints_frame)
        waypoint_row.pack(fill="x", pady=2)
        
        entry = SearchableCombobox(
            waypoint_row,
            width=30,
            values=list(ROMANIA_CITIES_COORDS.keys())
        )
        entry.pack(side="left", padx=(20,5))  # Add left padding for indentation
        
        remove_btn = ttk.Button(
            waypoint_row,
            text="×",
            width=3,
            command=lambda: self.remove_waypoint(waypoint_row, entry, remove_btn)
        )
        remove_btn.pack(side="left")
        
        self.waypoints.append((entry, remove_btn))

    def remove_waypoint(self, row_frame, entry, button):
        row_frame.destroy()  # Remove the entire row frame
        self.waypoints = [(e, b) for e, b in self.waypoints if e != entry]

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
            city = location['city']
            
            self.map_widget.set_position(lat, lon)
            self.map_widget.set_zoom(14)
            self.map_widget.set_marker(lat, lon, text=f"You are here ({city})")
            
            self.location_entry.delete(0, tk.END)
            self.location_entry.insert(0, city)
            return True
        return False
        
    def set_start_current(self):
        location = self.get_location_info()
        if location:
            coord_str = f"{location['lat']},{location['lon']}"
            self.start_entry.delete(0, tk.END)
            self.start_entry.insert(0, coord_str)
    
    def search_location(self):
        try:
            location = self.location_entry.get().strip()
            if location in ROMANIA_CITIES_COORDS:
                city_data = ROMANIA_CITIES_COORDS[location]
                lat, lon = city_data['lat'], city_data['lon']
                self.map_widget.set_position(lat, lon)
                self.map_widget.set_zoom(13)
                self.map_widget.set_marker(lat, lon, text=city_data['name'])
                return True
            
            # Fallback to normal search if not in our database
            coords = self.validate_coordinates(location) or self.map_widget.set_address(f"{location}, Romania")
            if coords:
                self.map_widget.set_position(coords[0], coords[1])
                self.map_widget.set_zoom(13)
                self.map_widget.set_marker(coords[0], coords[1], text=location)
                return True
            
            messagebox.showerror("Eroare", "Locația nu a putut fi găsită")
            return False
        except Exception as e:
            print(f"Eroare la căutare: {str(e)}")
            messagebox.showerror("Eroare", "Nu s-a putut procesa cererea")
            return False

    def get_route_points(self, locations):
        """Get route through multiple points"""
        try:
            # Format coordinates string for OSRM
            coords = []
            
            # Get coordinates for each location
            for loc in locations:
                if loc in ROMANIA_CITIES_COORDS:
                    city = ROMANIA_CITIES_COORDS[loc]
                    coords.append(f"{city['lon']},{city['lat']}")  # OSRM expects lon,lat
                else:
                    # Try to geocode the location
                    result = self.map_widget.set_address(f"{loc}, Romania")
                    if result:
                        lat, lon = result
                        coords.append(f"{lon},{lat}")  # OSRM expects lon,lat
            
            if len(coords) < 2:
                return None
                
            # Build OSRM API URL
            coords_str = ";".join(coords)
            url = f"http://router.project-osrm.org/route/v1/driving/{coords_str}?steps=true&geometries=polyline&overview=full"
            
            # Make request without debug prints
            response = requests.get(url)
            
            if not response.ok:
                print(f"Route API error: {response.status_code}")
                return None
                
            data = response.json()
            
            if data.get("code") != "Ok":
                return None

            # Process route data
            route = data["routes"][0]
            
            # Decode full route geometry
            full_route = polyline.decode(route["geometry"])
            
            # Get legs info with safe access to instructions
            legs = []
            for leg in route["legs"]:
                steps = []
                for step in leg["steps"]:
                    maneuver = step.get("maneuver", {})
                    instruction = maneuver.get("text", "Continue")  # Default instruction if missing
                    
                    steps.append({
                        "instruction": instruction,
                        "distance": step.get("distance", 0),
                        "duration": step.get("duration", 0),
                        "geometry": polyline.decode(step.get("geometry", ""))
                    })
                legs.append({
                    "steps": steps,
                    "distance": leg.get("distance", 0),
                    "duration": leg.get("duration", 0)
                })
            
            return {
                "points": full_route,
                "legs": legs,
                "total_distance": route.get("distance", 0),
                "total_duration": route.get("duration", 0)
            }
                
        except Exception as e:
            print(f"Route calculation error: {e.__class__.__name__}")
            return None

    def calculate_route(self):
        """Calculate and display route with waypoints"""
        try:
            self.map_widget.delete_all_path()
            self.map_widget.delete_all_marker()
            
            # Collect all locations in order
            locations = [self.start_entry.get().strip()]
            locations.extend(entry.get().strip() for entry, _ in self.waypoints)
            locations.append(self.end_entry.get().strip())
            
            # Filter out empty locations
            locations = [loc for loc in locations if loc]
            
            if len(locations) < 2:
                return
            
            route_data = self.get_route_points(locations)
            
            if route_data:
                # Add markers for all points
                colors = ["green"] + ["orange"] * (len(locations)-2) + ["red"]
                
                for loc, color in zip(locations, colors):
                    if loc in ROMANIA_CITIES_COORDS:
                        city = ROMANIA_CITIES_COORDS[loc]
                        lat, lon = city['lat'], city['lon']
                        name = city['name']
                    else:
                        coords = self.map_widget.set_address(f"{loc}, Romania")
                        if coords:
                            lat, lon = coords
                            name = loc
                    
                    self.map_widget.set_marker(
                        lat, lon,
                        text=name,
                        marker_color_circle=color,
                        marker_color_outside=f"dark{color}"
                    )
                
                # Draw route
                self.map_widget.set_path(route_data["points"])
                
                # Show route info
                self.route_info_frame.pack(fill="x", pady=5)
                self.steps_list.delete(0, tk.END)
                
                self.display_route_info(route_data)
                
                # Fit map to show entire route
                self.map_widget.fit_bounds(route_data["points"], padding=50)
                
        except Exception as e:
            print(f"Route calculation error: {str(e)}")

    def display_route_info(self, route_data):
        total_distance = route_data["total_distance"] / 1000  # to km
        total_duration = route_data["total_duration"] / 60    # to minutes
        
        self.steps_list.insert(tk.END, f"Distanță totală: {total_distance:.1f} km")
        self.steps_list.insert(tk.END, f"Durată estimată: {int(total_duration)} minute")

    def change_map(self, map_type):
        if map_type == "normală":  # Changed from "normal" to match Romanian button text
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}", max_zoom=22)
        elif map_type == "satelit":  # Changed from "satellite" to match Romanian button text
            self.map_widget.set_tile_server("http://mt0.google.com/vt/lyrs=s,h&hl=en&x={x}&y={y}&z={z}", max_zoom=22)
        elif map_type == "teren":  # Changed from "terrain" to match Romanian button text
            self.map_widget.set_tile_server("http://mt0.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}", max_zoom=22)

    def show_location(self, location_data):
        """Show a specific location on the map"""
        try:
            city = location_data["location"]
            if city in ROMANIA_CITIES_COORDS:
                city_data = ROMANIA_CITIES_COORDS[city]
                base_lat, base_lon = city_data['lat'], city_data['lon']
                
                # Create marker with full details
                marker_text = (
                    f"📍 {location_data['title']}\n"
                    f"Rating: {'⭐' * int(float(location_data['rating']))}\n"
                    f"Categorie: {location_data['type']}\n"
                    f"Preț: {location_data['price_category']}\n"
                    f"Durata: {location_data['min_duration']} ore"
                )
                
                self.map_widget.set_position(base_lat, base_lon)
                self.map_widget.set_zoom(15)
                
                self.map_widget.set_marker(
                    base_lat, base_lon,
                    text=marker_text,
                    marker_color_circle="red",
                    marker_color_outside="darkred",
                    font=("Arial", 12)
                )
                return True
                    
        except Exception as e:
            print(f"Error showing location: {e}")
        return False

    def toggle_attractions(self):
        """Toggle tourist attractions visibility"""
        if not self.attractions_visible:
            # Clear existing markers
            for marker in self.attraction_markers:
                marker.delete()
            self.attraction_markers.clear()
            
            try:
                import pandas as pd
                df = pd.read_csv("D:\Proiect_Concurs\data\locatii_turistice_final.csv")
                
                # Use the same color mapping defined in __init__
                for _, row in df.iterrows():
                    try:
                        lat = float(row['latitudine'])
                        lon = float(row['longitudine'])
                        
                        # Get color based on category using the shared color mapping
                        color = self.category_colors.get(row['categorie'], self.category_colors['Other'])
                        
                        marker = self.map_widget.set_marker(
                            lat, lon,
                            text="",  # Empty text
                            marker_color_circle=color,
                            marker_color_outside=color
                        )
                        self.attraction_markers.append(marker)
                    except (ValueError, TypeError):
                        continue  # Skip if coordinates are invalid
                
            except Exception as e:
                print(f"Error loading attractions: {e}")
                
            self.attractions_visible = True
        else:
            for marker in self.attraction_markers:
                marker.delete()
            self.attraction_markers.clear()
            self.attractions_visible = False

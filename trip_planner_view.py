import tkinter as tk
from tkinter import messagebox, ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime
from cities_data import ROMANIA_CITIES_COORDS
from PIL import Image, ImageTk
import requests
from io import BytesIO
from tkinter import scrolledtext
import os
import pandas as pd

class TripPlannerView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=BOTH, expand=YES)
        
        # Improved UI configuration
        self.style = ttk.Style()
        self._configure_styles()
        self._setup_ui_constants()
        
        # State management
        self.trip_data = {}
        self.current_step = 0
        self.steps = [('plan', self.create_trip_plan)]
        
        # Load data from collector
        self.df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'data', 'locatii_turistice_final.csv'))
        self.cities = sorted(self.df['oras'].unique())
        
        self.create_welcome_screen()

    def _configure_styles(self):
        """Configure enhanced modern styles"""
        colors = {
            'primary': '#2962ff',
            'secondary': '#455a64',
            'success': '#2e7d32',
            'background': '#f5f5f5',
            'card': '#ffffff',
            'text': '#263238',
            'accent': '#1976d2'
        }
        
        # Enhanced card style
        self.style.configure(
            'Card.TFrame', 
            background=colors['card'],
            relief='solid',
            borderwidth=1
        )
        
        self.style.configure(
            'CardHeader.TFrame',
            background=colors['card']
        )
        
        self.style.configure(
            'CardTitle.TLabel',
            font=('Helvetica', 12, 'bold'),
            foreground=colors['text'],
            background=colors['card']
        )
        
        self.style.configure(
            'CardTime.TLabel',
            font=('Helvetica', 11),
            foreground=colors['secondary'],
            background=colors['card']
        )
        
        self.style.configure(
            'CardPrice.TLabel',
            font=('Helvetica', 11),
            foreground=colors['secondary'],
            background=colors['card']
        )
        
        self.style.configure(
            'CardRating.TLabel',
            font=('Helvetica', 11),
            foreground='#ffd700',
            background=colors['card']
        )
        
        # Modern button styles
        self.style.configure(
            'Action.TButton',
            font=('Helvetica', 11),
            padding=(20, 10),
            background=colors['primary']
        )
        
        # Enhanced label styles
        self.style.configure(
            'Title.TLabel',
            font=('Helvetica', 16, 'bold'),
            foreground=colors['text']
        )

    def _setup_ui_constants(self):
        """Setup UI constants with minimal icons"""
        self.UI_ICONS = {
            'rating': '★',  # Single star for ratings
            'empty_rating': '☆'  # Empty star for ratings
        }
        
        self.THEME_COLORS = {
            'primary': '#2962ff',
            'secondary': '#455a64', 
            'background': '#f8fafc',
            'card': '#ffffff',
            'text': '#1e293b',
            'border': '#e2e8f0',
            'rating': '#ffd700'  # Gold color for rating stars
        }
        
        self.CARD_PADDING = 15
        self.SPACING = 10

    def create_welcome_screen(self):
        """Enhanced welcome screen"""
        self.clear_frame()
        container = self._create_styled_container("Planifică-ți Călătoria bazată pe personalitatea ta")
        
        # Create input section frame
        input_frame = self._create_input_section(container)
        self._add_city_selector(input_frame)
        self._add_text_input(input_frame)
        self._add_action_buttons(input_frame)

    def _create_styled_container(self, title):
        """Create styled container with shadow effect"""
        container = ttk.Frame(self, style='Card.TFrame')
        container.pack(fill=BOTH, expand=YES, padx=30, pady=20)
        
        if title:
            ttk.Label(
                container,
                text=title,
                style='Title.TLabel'
            ).pack(pady=(20, 30))
        
        return container

    def _create_input_section(self, parent):
        """Create input section frame"""
        frame = ttk.Frame(parent, style='Card.TFrame')
        frame.pack(fill=X, padx=30, pady=20)
        return frame

    def _add_city_selector(self, parent):
        """Add city selection dropdown"""
        city_frame = ttk.Frame(parent)
        city_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(
            city_frame,
            text="Alege orașul:",
            font=("Helvetica", 11)
        ).pack(side=LEFT)
        
        self.selected_city = ttk.StringVar()
        city_combo = ttk.Combobox(
            city_frame,
            textvariable=self.selected_city,
            values=self.cities,
            state='readonly',
            width=30
        )
        city_combo.pack(side=LEFT, padx=(10, 0))

    def _add_text_input(self, parent):
        """Add text input area"""
        ttk.Label(
            parent,
            text="Spune ceva despre tine:",
            font=("Helvetica", 11)
        ).pack(anchor=W, pady=(10, 5))
        
        self.user_input = scrolledtext.ScrolledText(
            parent,
            height=4,
            width=50,
            font=("Helvetica", 10)
        )
        self.user_input.pack(fill=X, pady=(0, 10))
        
        # Add placeholder text
        placeholder = "Exemple:\n• Vreau să vizitez muzee și clădiri istorice\n• Caut locuri pentru relaxare în natură"
        self.user_input.insert('1.0', placeholder)
        self.user_input.bind('<FocusIn>', self._clear_placeholder)
        self.user_input.bind('<FocusOut>', self._restore_placeholder)
        self.user_input.placeholder = placeholder

    def _add_action_buttons(self, parent):
        """Add action buttons"""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(
            btn_frame,
            text="Generează Plan",
            style="primary.TButton",
            command=self.process_user_request
        ).pack(side=RIGHT)
        
        ttk.Button(
            btn_frame,
            text="Resetează",
            style="secondary.TButton",
            command=self.reset_form
        ).pack(side=RIGHT, padx=(0, 10))

    def _clear_placeholder(self, event):
        """Clear placeholder text on focus"""
        if self.user_input.get('1.0', 'end-1c') == self.user_input.placeholder:
            self.user_input.delete('1.0', 'end')
            self.user_input.configure(foreground='black')

    def _restore_placeholder(self, event):
        """Restore placeholder if empty"""
        if not self.user_input.get('1.0', 'end-1c').strip():
            self.user_input.delete('1.0', 'end')
            self.user_input.insert('1.0', self.user_input.placeholder)
            self.user_input.configure(foreground='gray')

    def reset_form(self):
        """Reset form to initial state"""
        self.selected_city.set('')
        self.user_input.delete('1.0', 'end')
        self.user_input.insert('1.0', self.user_input.placeholder)
        self.user_input.configure(foreground='gray')

    def process_user_request(self):
        """Procesează cererea utilizatorului și afișează top 5 locații"""
        try:
            text = self.user_input.get('1.0', 'end-1c')
            city = self.selected_city.get()
            
            if not city:
                messagebox.showwarning("Atenție", "Te rog selectează un oraș")
                return
            
            from trip_planner_model import TripPlanner
            planner = TripPlanner()
            
            # Get matching categories and their probabilities
            similarities, probabilities = planner.recommender.process_text_input(text)
            
            # Get city locations and calculate scores
            city_locations = self.df[self.df['oras'] == city]
            scored_locations = []
            
            for _, location in city_locations.iterrows():
                category = location['categorie'].lower()
                score = probabilities.get(category, 0) * float(location['rating_general'])
                
                if score > 0:
                    scored_locations.append({
                        'nume': location['denumire'],
                        'categorie': location['categorie'],
                        'rating': location['rating_general'],
                        'lat': location['latitudine'],
                        'lon': location['longitudine'],
                        'score': score
                    })
            
            # Sort by score and get top 5
            top_locations = sorted(
                scored_locations,
                key=lambda x: x['score'],
                reverse=True
            )[:5]
            
            if not top_locations:
                messagebox.showwarning(
                    "Nicio locație",
                    f"Nu am găsit locații potrivite în {city}"
                )
                return
            
            # Update trip data structure
            self.trip_data = {
                'city': city,
                'locations': top_locations
            }
            
            # Calculate distances between locations
            distances = []
            for i in range(len(top_locations)-1):
                loc1 = top_locations[i]
                loc2 = top_locations[i+1]
                distance = planner._calculate_distance(
                    float(loc1['lat']), float(loc1['lon']),
                    float(loc2['lat']), float(loc2['lon'])
                )
                distances.append((loc1['nume'], loc2['nume'], distance))
            
            self.trip_data['distances'] = distances
            
            # Show results
            self.show_results()
            
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {str(e)}")

    def show_results(self):
        """Afișează rezultatele pe hartă și lista de locații"""
        self.clear_frame()
        
        # Create main container
        container = self.create_container(f"Top 5 Locații în {self.trip_data['city']}")
        
        # Create split view
        split_container = ttk.Frame(container)
        split_container.pack(fill=BOTH, expand=YES)
        
        # Left side - Location list and distances
        list_frame = ttk.Frame(split_container)
        list_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0,10))
        
        # Add locations list
        for i, loc in enumerate(self.trip_data['locations'], 1):
            self._create_location_card(list_frame, loc, i)
        
        # Add distances
        if self.trip_data['distances']:
            ttk.Separator(list_frame).pack(fill=X, pady=10)
            ttk.Label(
                list_frame,
                text="Distanțe între locații:",
                style='Title.TLabel'
            ).pack(pady=10)
            
            for from_loc, to_loc, dist in self.trip_data['distances']:
                ttk.Label(
                    list_frame,
                    text=f"{from_loc} → {to_loc}: {dist:.2f} km"
                ).pack(pady=2)
        
        # Right side - Map
        map_frame = ttk.Frame(split_container)
        map_frame.pack(side=LEFT, fill=BOTH, expand=YES)
        
        # Add map widget
        from tkintermapview import TkinterMapView
        map_widget = TkinterMapView(map_frame, width=400, height=400)
        map_widget.pack(fill=BOTH, expand=YES)
        
        # Add markers and route
        route_points = []
        for loc in self.trip_data['locations']:
            lat, lon = float(loc['lat']), float(loc['lon'])
            map_widget.set_marker(lat, lon, text=loc['nume'])
            route_points.append((lat, lon))
        
        # Draw route between points
        if len(route_points) > 1:
            map_widget.set_path(route_points)
        
        # Center map on locations
        center_lat = sum(float(loc['lat']) for loc in self.trip_data['locations']) / len(self.trip_data['locations'])
        center_lon = sum(float(loc['lon']) for loc in self.trip_data['locations']) / len(self.trip_data['locations'])
        map_widget.set_position(center_lat, center_lon)
        map_widget.set_zoom(13)

    def _create_location_card(self, parent, location, index):
        """Create card for a location"""
        card = ttk.Frame(parent, style='Card.TFrame')
        card.pack(fill=X, pady=5)
        
        # Location name with index
        ttk.Label(
            card,
            text=f"{index}. {location['nume']}",
            style='CardTitle.TLabel'
        ).pack(anchor=W)
        
        # Rating and category
        info_frame = ttk.Frame(card)
        info_frame.pack(fill=X, pady=5)
        
        ttk.Label(
            info_frame,
            text=f"⭐ {location['rating']:.1f}",
            style='CardRating.TLabel'
        ).pack(side=LEFT)
        
        ttk.Label(
            info_frame,
            text=location['categorie'],
            style='CardInfo.TLabel'
        ).pack(side=RIGHT)
        
        ttk.Separator(parent).pack(fill=X, pady=5)

    def create_container(self, title):
        """Helper function to create a standard container"""
        container = ttk.Frame(self)
        container.pack(fill=BOTH, expand=YES, padx=50, pady=30)
        
        if title:
            ttk.Label(
                container,
                text=title,
                font=("Helvetica", 18, "bold")
            ).pack(pady=20)
        
        return container
    
    def show_step(self, step_index):
        """Show a specific step"""
        self.current_step = step_index
        self.clear_frame()
        _, step_func = self.steps[step_index]
        step_func()
    
    def create_trip_plan(self):
        container = self.create_container("Planul Tău de Călătorie")
        
        # Create split view container
        split_container = ttk.Frame(container)
        split_container.pack(fill=BOTH, expand=YES)
        
        # Left side - Itinerary
        itinerary_frame = ttk.Frame(split_container)
        itinerary_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0,10))
        
        # Add title with destination summary
        destinations_text = " → ".join(
            f"{d['city']} ({d['duration']} zile)" 
            for d in self.trip_data['destinations']
        )
        
        ttk.Label(
            itinerary_frame,
            text=destinations_text,
            style='Header.TLabel'
        ).pack(pady=(0, 20))
        
        # Right side - Map
        map_frame = ttk.Frame(split_container)
        map_frame.pack(side=LEFT, fill=BOTH, expand=YES)
        
        # Add map widget
        from tkintermapview import TkinterMapView
        self.map_widget = TkinterMapView(map_frame)
        self.map_widget.pack(fill=BOTH, expand=YES)
        
        # Plot route on map
        route_points = []
        markers = []
        for dest in self.trip_data['destinations']:
            if dest['city'] in ROMANIA_CITIES_COORDS:
                city_data = ROMANIA_CITIES_COORDS[dest['city']]
                lat, lon = city_data['lat'], city_data['lon']
                route_points.append((lat, lon))
                
                # Add marker for each city
                marker = self.map_widget.set_marker(
                    lat, lon,
                    text=f"{dest['city']} ({dest['duration']} zile)"
                )
                markers.append(marker)
        
        # Draw route line between cities
        if len(route_points) > 1:
            path = self.map_widget.set_path(route_points)
            
            # Calculate bounds to fit all markers
            min_lat = min(p[0] for p in route_points)
            max_lat = max(p[0] for p in route_points)
            min_lon = min(p[1] for p in route_points)
            max_lon = max(p[1] for p in route_points)
            
            # Add padding to bounds
            padding = 0.1  # Adjust this value as needed
            min_lat -= padding
            max_lat += padding
            min_lon -= padding
            max_lon += padding
            
            # Set map view to show all markers
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2
            self.map_widget.set_position(center_lat, center_lon)
            
            # Calculate appropriate zoom level
            lat_diff = max_lat - min_lat
            lon_diff = max_lon - min_lon
            zoom = min(
                int(-1.4 * max(lat_diff, lon_diff) + 13),  # Adjust formula as needed
                17  # Maximum zoom level
            )
            self.map_widget.set_zoom(zoom)

        # Create scrollable itinerary view
        scroll_frame = ttk.Frame(itinerary_frame)
        scroll_frame.pack(fill=BOTH, expand=YES)
        
        canvas = tk.Canvas(scroll_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Style for day cards
        style = ttk.Style()
        style.configure(
            'DayCard.TFrame',
            background='white',
            relief='solid',
            borderwidth=1,
            padding=15
        )
        
        # Daily schedule with improved cards
        times = {
            "morning": "🌅 Dimineața",
            "afternoon": "☀️ După-amiaza",
            "evening": "🌙 Seara"
        }
        
        for day, activities in self.trip_data['daily_plan'].items():
            day_frame = ttk.LabelFrame(
                scrollable_frame,
                text=f"Ziua {day} - {activities['city']}",
                padding=10,
                style='DayCard.TFrame'
            )
            day_frame.pack(fill=X, padx=10, pady=5)
            
            # Add activities
            for time, label in times.items():
                activity = activities[time]
                self._create_activity_card(day_frame, activity, label)
                
                # Show location on map when clicked
                if activity['nume locatie'] != "Explorare liberă":
                    lat = float(activity.get('latitudine', 0))
                    lon = float(activity.get('longitudine', 0))
                    if lat and lon:
                        self.map_widget.set_marker(
                            lat, lon,
                            text=f"{activity['nume locatie']} ({label})",
                            marker_color_circle="orange"
                        )
        
        # Pack scrollable components
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Bottom buttons
        self._add_bottom_buttons(container)

    def _create_activity_card(self, parent, activity, time_label):
        """Create enhanced activity card"""
        card = ttk.Frame(parent, style='Card.TFrame')
        card.pack(fill=X, pady=5)
        
        # Add hover effect
        self._add_hover_effect(card)
        
        # Create content with improved layout
        self._create_card_content(card, activity, time_label)
        
        return card

    def _add_hover_effect(self, widget):
        """Add hover effect to widget"""
        def on_enter(e):
            widget.configure(relief='raised')
        def on_leave(e):
            widget.configure(relief='solid')
            
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    def _create_card_content(self, card, activity, time_label):
        """Create modern card content"""
        # Header with time and location
        header = ttk.Frame(card, style='CardHeader.TFrame')
        header.pack(fill=X, pady=(0, self.SPACING))
        
        location_text = activity['nume locatie']
        ttk.Label(
            header,
            text=time_label,
            style='CardTime.TLabel'
        ).pack(side=LEFT)
        
        ttk.Label(
            header,
            text=location_text,
            style='CardTitle.TLabel'
        ).pack(side=RIGHT)
        
        # Content area with price and rating
        content = ttk.Frame(card, style='CardContent.TFrame')
        content.pack(fill=X)
        
        # Price info
        price_text = f"{activity['pret_estimat']}"
        ttk.Label(
            content,
            text=price_text,
            style='CardPrice.TLabel'
        ).pack(side=LEFT)
        
        # Rating display
        rating = float(activity['rating'])
        full_stars = "★" * int(rating)
        empty_stars = "☆" * (5 - int(rating))
        rating_text = f"{full_stars}{empty_stars} {rating:.1f}"
        
        ttk.Label(
            content,
            text=rating_text,
            style='CardRating.TLabel'
        ).pack(side=RIGHT)

    def _add_bottom_buttons(self, container):
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=X, pady=20)
        
        ttk.Button(
            btn_frame,
            text="← Început nou",
            command=self.reset_app,
            style="secondary.TButton"
        ).pack(side=LEFT)
        
        ttk.Button(
            btn_frame,
            text="Salvează planul",
            style="success.TButton"
        ).pack(side=RIGHT)
    
    def clear_frame(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.update_idletasks()

    def reset_app(self):
        self.trip_data = {}
        self.current_step = 0
        self.create_welcome_screen()

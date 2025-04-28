import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
import pandas as pd
from ml_engine import TripRecommender

# Add these constants at the top after imports
ICONS = {
    'LOCATION': '\u2302',  # House symbol
    'PRICE': '\u20AC',     # Euro symbol  
    'SEASON': '\u2600',    # Sun symbol
    'TYPE': '\u2691',      # Flag symbol
    'TIME': '\u231B',      # Hourglass symbol
    'MAP': '\u25A0',       # Map symbol
    'SEARCH': '\u2315',    # Search symbol
    'MARKER': '\u2316'     # Position marker
}

class DiscoverView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=BOTH, expand=YES)
        
        # Initialize the recommender
        self.recommender = TripRecommender()
        
        # Data structure for ML integration
        self.user_preferences = {
            'liked_locations': [],
            'preferred_types': [],
            'price_range': (0, 1000),
            'ratings': []
        }
        
        # Callback for map integration
        self.on_map_request = None
        
        # Style configuration
        self.style = ttk.Style()
        self.setup_styles()
        
        # Load CSV data for city dropdown
        self.load_csv_data()
        
        # Create UI elements
        self.setup_ui()
        
        # Load initial data
        self.load_initial_data()
    
    def load_csv_data(self):
        self.df_full = pd.read_csv("d:/Proiect_Concurs/data/locatii_turistice_final.csv")
        self.unique_cities = sorted(self.df_full['oras'].unique())
    
    def setup_styles(self):
        """Configure custom styles"""
        # Enhanced color palette
        self.colors = {
            'primary': '#3b82f6',      # Bright blue
            'secondary': '#64748b',     # Slate gray
            'success': '#22c55e',       # Green
            'background': '#f8fafc',    # Light gray
            'card': '#ffffff',          # White
            'text': '#1e293b',         # Dark slate
            'border': '#e2e8f0',       # Light border
            'hover': '#f1f5f9',        # Hover background
            'star': '#fbbf24',         # Star rating color
            'tag': '#e2e8f0'           # Tag background
        }

        # Card styling with shadow
        self.style.configure('Card.TFrame', 
            background=self.colors['card'])
        
        # Hover style for cards
        self.style.configure('CardHover.TFrame',
            background=self.colors['hover'])

        # Filter section with better spacing
        self.style.configure('Filter.TLabelframe',
            background=self.colors['background'],
            padding=25)
        
        self.style.configure('Filter.TLabelframe.Label',
            font=('Segoe UI Semibold', 18),
            foreground=self.colors['primary'])

        # Enhanced buttons
        self.style.configure('Primary.TButton',
            font=('Segoe UI Semibold', 11),
            padding=(20, 10))

        self.style.configure('Secondary.TButton',
            font=('Segoe UI', 11),
            padding=(20, 10))

    def setup_ui(self):
        # Use styled frame instead of direct configuration
        self.configure(style='Main.TFrame')
        
        # Left sidebar for filters
        filters = ttk.LabelFrame(
            self, 
            text="Filtre", 
            padding=20,
            style='Filter.TLabelframe'
        )
        filters.pack(side=LEFT, fill=Y, padx=20, pady=20)

        # Create a container frame for the filters content
        filter_content = ttk.Frame(filters, style='Filter.TLabelframe')
        filter_content.pack(fill=BOTH, expand=YES)
        
        # Reset button at the top - centered
        reset_frame = ttk.Frame(filter_content)
        reset_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Button(
            reset_frame,
            text="Resetează filtrele",
            style='Reset.TButton',
            command=self.reset_filters
        ).pack(side=TOP, anchor=CENTER)  # Changed from side=RIGHT to side=TOP with anchor=CENTER
        
        # City filter
        ttk.Label(
            filter_content, 
            text="Oraș",
            font=('Segoe UI', 12),
            foreground=self.colors['secondary']
        ).pack(pady=(10,5))

        self.city_var = ttk.StringVar()
        self.city_combo = ttk.Combobox(
            filter_content,
            textvariable=self.city_var,
            values=self.unique_cities,
            state='readonly'
        )
        self.city_combo.pack(fill=X, pady=(0,15))
        self.city_combo.bind('<<ComboboxSelected>>', self.on_filter_change)

        # Category filter
        ttk.Label(
            filter_content, 
            text="Categorie",
            font=('Segoe UI', 12),
            foreground=self.colors['secondary']
        ).pack(pady=(10,5))

        self.category_var = ttk.StringVar()
        categories = sorted(self.df_full['categorie'].unique())
        self.category_combo = ttk.Combobox(
            filter_content,
            textvariable=self.category_var,
            values=categories,
            state='readonly'
        )
        self.category_combo.pack(fill=X, pady=(0,15))
        self.category_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Trip Type filter
        ttk.Label(
            filter_content, 
            text="Tip Călătorie",
            font=('Segoe UI', 12),
            foreground=self.colors['secondary']
        ).pack(pady=(10,5))

        self.trip_type_var = ttk.StringVar()
        trip_types = ["City Break", "Relaxare", "Circuit"]
        self.trip_type_combo = ttk.Combobox(
            filter_content,
            textvariable=self.trip_type_var,
            values=trip_types,
            state='readonly'
        )
        self.trip_type_combo.pack(fill=X, pady=(0,15))
        self.trip_type_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Rating filter
        ttk.Label(
            filter_content, 
            text="Rating Minim",
            font=('Segoe UI', 12),
            foreground=self.colors['secondary']
        ).pack(pady=(10,5))
        
        self.rating_var = ttk.StringVar(value='1')
        rating_values = [str(x) for x in range(1, 6)]
        self.rating_combo = ttk.Combobox(
            filter_content,
            textvariable=self.rating_var,
            values=rating_values,
            state='readonly'
        )
        self.rating_combo.pack(fill=X, pady=(0,15))
        self.rating_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Apply filters button
        ttk.Button(
            filter_content,
            text="Aplică Filtrele",
            style='Primary.TButton',
            width=20,
            command=self.apply_filters
        ).pack(pady=(20,5))
        
        # Main content area with shadow
        content = ScrolledFrame(
            self,
            bootstyle='light-rounded'
        )
        content.pack(side=LEFT, fill=BOTH, expand=YES, padx=20, pady=20)
        self.content_frame = content
    
    def reset_filters(self):
        """Reset all filters to default values"""
        self.city_var.set('')
        self.category_var.set('')
        self.trip_type_var.set('')
        self.rating_var.set('1')
        self.apply_filters()
    
    def create_travel_card(self, data):
        # Create card with enhanced shadow effect
        card = ttk.Frame(self.content_frame, style='Card.TFrame')
        card.pack(fill=X, padx=20, pady=12)
        
        # Apply shadow effect using canvas
        shadow = tk.Canvas(card, height=4, bg=self.colors['background'], 
                         highlightthickness=0)
        shadow.pack(fill=X, side=BOTTOM)
        
        # Content container
        content = ttk.Frame(card, style='CardContent.TFrame')
        content.pack(fill=X, padx=20, pady=15)
        
        # Header with title and rating
        header = ttk.Frame(content)
        header.pack(fill=X, pady=(0, 15))
        
        # Title with category tag
        title_frame = ttk.Frame(header)
        title_frame.pack(side=LEFT)
        
        ttk.Label(
            title_frame,
            text=data["title"],
            font=('Segoe UI Semibold', 20),
            foreground=self.colors['text']
        ).pack(side=LEFT)
        
        # Category tag
        tag_frame = ttk.Frame(title_frame, style='Tag.TFrame')
        tag_frame.pack(side=LEFT, padx=(10, 0))
        
        ttk.Label(
            tag_frame,
            text=data['type'],
            font=('Segoe UI', 10),
            foreground=self.colors['secondary'],
            padding=(8, 2)
        ).pack()
        
        # Enhanced rating display
        rating_frame = ttk.Frame(header)
        rating_frame.pack(side=RIGHT)
        
        # Star rating visualization
        rating_val = float(data['rating'])
        stars = "★" * int(rating_val) + "☆" * (5 - int(rating_val))
        
        ttk.Label(
            rating_frame,
            text=stars,
            font=('Segoe UI', 16),
            foreground=self.colors['star']
        ).pack(side=LEFT, padx=(0, 8))
        
        ttk.Label(
            rating_frame,
            text=f"{data['rating']} ({data['reviews']} recenzii)",
            font=('Segoe UI', 12),
            foreground=self.colors['secondary']
        ).pack(side=LEFT)

        # Info grid with icons and better layout
        info_frame = ttk.Frame(content)
        info_frame.pack(fill=X, pady=(5, 15))
        
        info = [
            (ICONS['LOCATION'], "Locație", data['location']),
            (ICONS['PRICE'], "Preț", data['price_category']),
            (ICONS['SEASON'], "Sezon", data['season']),
            (ICONS['TYPE'], "Tip", data['trip_type']),
            (ICONS['TIME'], "Durată", f"{data['min_duration']} ore")
        ]
        
        for row, (icon, label, text) in enumerate(info):
            # Icon
            ttk.Label(
                info_frame,
                text=icon,
                font=('Segoe UI', 14)
            ).grid(row=row, column=0, padx=(0,10), pady=4)
            
            # Label
            ttk.Label(
                info_frame,
                text=label + ":",
                font=('Segoe UI Semibold', 13),
                foreground=self.colors['text']
            ).grid(row=row, column=1, padx=(0,10), pady=4)
            
            # Value
            ttk.Label(
                info_frame,
                text=text,
                font=('Segoe UI', 13),
                foreground=self.colors['secondary']
            ).grid(row=row, column=2, sticky=W, pady=4)

        # Action button - only map
        btn_frame = ttk.Frame(content)
        btn_frame.pack(fill=X, pady=(15,0))
        
        ttk.Button(
            btn_frame,
            text=f" Vezi pe Hartă",
            style='Primary.TButton',
            command=lambda: self.show_on_map(data),
            width=20
        ).pack(side=LEFT)
    
    def save_preference(self, data):
        """Save user preference and update recommender"""
        self.user_preferences['liked_locations'].append(data['location'])
        self.user_preferences['ratings'].append(float(data['rating']))
        self.user_preferences['preferred_types'].append(data['type'])
        
        # Send feedback to recommender
        feedback = {
            'location': data['location'],
            'rating': float(data['rating']),
            'category': data['type'],
            'liked': True
        }
        self.recommender.learn_from_feedback([feedback])
    
    def show_on_map(self, data):
        """Show location in popup map window"""
        # Create minimal popup window
        popup = ttk.Toplevel(self)
        popup.title(f"{data['title']}")
        popup.geometry("800x600")
        
        # Create map widget directly
        from tkintermapview import TkinterMapView
        map_widget = TkinterMapView(popup, corner_radius=0)
        map_widget.pack(fill="both", expand=True)
        
        # Set map location using coordinates
        lat = float(data["latitude"])
        lon = float(data["longitude"])
        
        # Center map on location
        map_widget.set_position(lat, lon)
        map_widget.set_zoom(15)
        
        # Add single marker
        map_widget.set_marker(
            lat, lon,
            text=data["title"],
            marker_color_circle="red",
            marker_color_outside="darkred"
        )
    
    def clear_cards(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def on_filter_change(self, event=None):
        """Called whenever a filter changes"""
        self.apply_filters()
    
    def load_initial_data(self):
        """Load initial data without filters"""
        self.clear_cards()
        print("Available columns:", self.df_full.columns.tolist())  # Debug print
        recommendations = self.df_full.head(20).to_dict('records')
        self.display_recommendations(recommendations)
    
    def apply_filters(self):
        self.clear_cards()
        df = self.df_full.copy()
        
        city = self.city_var.get().strip()
        category = self.category_var.get().strip()
        trip_type = self.trip_type_var.get().strip()
        rating_min = float(self.rating_var.get() or 1)
        
        if city:
            df = df[df['oras'] == city]
        if category:
            df = df[df['categorie'] == category]
        if trip_type:
            df = df[df['tip_calatorie'] == trip_type]
        df = df[df['rating_general'] >= rating_min]
        
        self.display_recommendations(df.head(20).to_dict('records'))
    
    def display_recommendations(self, recommendations):
        """Display recommendations as cards"""
        for rec in recommendations:
            data = {
                "title": rec["denumire"],
                "location": rec["oras"],
                "type": rec["categorie"],
                "rating": str(rec["rating_general"]),
                "price_category": rec["pret_categorie"],
                "season": rec["sezon"],
                "trip_type": rec["tip_calatorie"],
                "min_duration": str(rec["durata_minima"]),
                "reviews": str(rec["nr_recenzii"]),
                "latitude": float(rec["latitudine"]),
                "longitude": float(rec["longitudine"])
            }
            self.create_travel_card(data)

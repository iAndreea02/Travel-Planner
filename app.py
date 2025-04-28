import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from style.styles import configure_styles, configure_category_styles

from map_module import MapView
from discover_module import DiscoverView
from photo_gallery_view import PhotoGalleryView
from trip_planner_view import TripPlannerView

class TravelPlannerApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="cosmo")
        self.title("iTravel")
        self.geometry("1800x800")
        
        # Configure styles - only sidebar should be purple
        style = ttk.Style()
        style.configure('Sidebar.TFrame', background='#E6E6FA')  # Light purple only for sidebar
        style.configure('Content.TFrame', background='white')    # White for content
        
        # Category-based color scheme
        self.category_colors = {
            'museums': {'bg': '#FFF3E0', 'fg': '#E65100', 'accent': '#FB8C00'},
            'religion': {'bg': '#E8EAF6', 'fg': '#1A237E', 'accent': '#3F51B5'},
            'historic': {'bg': '#EFEBE9', 'fg': '#3E2723', 'accent': '#795548'},
            'architecture': {'bg': '#E0F2F1', 'fg': '#004D40', 'accent': '#009688'},
            'cultural': {'bg': '#F3E5F5', 'fg': '#4A148C', 'accent': '#9C27B0'},
            'natural': {'bg': '#F1F8E9', 'fg': '#33691E', 'accent': '#8BC34A'},
            'entertainment': {'bg': '#FFF3E0', 'fg': '#E65100', 'accent': '#FF9800'},
            'fortifications': {'bg': '#ECEFF1', 'fg': '#263238', 'accent': '#607D8B'},
            'default': {'bg': '#F5F5F5', 'fg': '#212121', 'accent': '#9E9E9E'}
        }

        # Apply styles
        configure_styles(style)
        configure_category_styles(style, self.category_colors)
        
        # Create main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=YES)
        
        # Create side menu and content area
        self.menu_frame = ttk.Frame(self.main_frame, style='Sidebar.TFrame', width=250)
        self.menu_frame.pack(side=LEFT, fill=Y)
        self.menu_frame.pack_propagate(False)
        
        self.content_frame = ttk.Frame(self.main_frame, style='Content.TFrame')
        self.content_frame.pack(side=LEFT, fill=BOTH, expand=YES)
        
        # Create menu items
        self.create_menu_items()
        
        # Initialize all views
        self.views = {
            'discover': DiscoverView(self.content_frame),
            'map': MapView(self.content_frame),
            'gallery': PhotoGalleryView(self.content_frame),
            'planner': TripPlannerView(self.content_frame)
        }
        
        # Hide all views initially
        for view in self.views.values():
            view.pack_forget()
            
        # Show default view
        self.show_view('discover')
        
    def create_menu_items(self):
        # App title
        title_frame = ttk.Frame(self.menu_frame, style='Sidebar.TFrame')
        title_frame.pack(fill=X, pady=(20, 30))
        title_label = ttk.Label(title_frame, text="iTravel", style='SidebarTitle.TLabel')
        title_label.pack()
        
        # Menu buttons with Romanian titles
        menu_items = [
            ("\u2728 Descoperă", 'discover'),      # Sparkles
            ("\u2691 Hartă", 'map'),               # Map symbol
            ("\u2315 Galerie Foto", 'gallery'),    # Camera
            ("\u2708 Planificare", 'planner')      # Airplane
        ]
        
        for text, view_name in menu_items:
            btn = ttk.Button(
                self.menu_frame, 
                text=text,
                style='Sidebar.TButton',
                command=lambda v=view_name: self.show_view(v)
            )
            btn.pack(fill=X, padx=10, pady=5)
    
    def show_view(self, view_name):
        # Hide all views
        for view in self.views.values():
            view.pack_forget()
        
        # Show selected view
        self.views[view_name].pack(fill=BOTH, expand=YES)
    
    def show_on_map(self, data):
        """Show a location on the map from discover view"""
        self.show_view('map')
        self.views['map'].show_location(data["location"])

if __name__ == "__main__":
    app = TravelPlannerApp()
    app.mainloop()

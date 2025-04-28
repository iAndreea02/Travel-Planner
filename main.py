import tkinter as tk
import ttkbootstrap as ttk
import os
import sys
import locale  # Add this import
from trip_planner_view import TripPlannerView
from discover_module import DiscoverView

class MainApp(ttk.Window):
    def __init__(self):
        # Fix console encoding for Windows
        if sys.platform.startswith('win'):
            sys.stdout.reconfigure(encoding='utf-8')
            
        super().__init__(themename="litera")
        self.title("Travel Planner")
        self.geometry("900x700")
        
        # Show loading screen with safe characters
        self.show_loading_screen()
        self.after(100, self.init_data)

    def show_loading_screen(self):
        """Show loading screen while data is being initialized"""
        self.loading_frame = ttk.Frame(self)
        self.loading_frame.pack(expand=True)
        
        ttk.Label(
            self.loading_frame,
            text="Loading data...",  # Changed to ASCII
            font=("Helvetica", 14)
        ).pack(pady=20)
        
        self.progress = ttk.Progressbar(
            self.loading_frame,
            mode='indeterminate',
            length=300
        )
        self.progress.pack(pady=10)
        self.progress.start()
    
    def init_data(self):
        """Initialize data and create main interface"""
        try:
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            csv_path = os.path.join(data_dir, 'locatii_romania_AI_ready.csv')
            
            if not os.path.exists(csv_path):
                from data_collector import DataCollector
                collector = DataCollector()
                collector.collect_and_save_data()
            
            # Remove loading screen
            self.loading_frame.destroy()
            
            # Create main interface
            notebook = ttk.Notebook(self)
            notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            planner_tab = ttk.Frame(notebook)
            discover_tab = ttk.Frame(notebook)
            
            notebook.add(planner_tab, text="✨ Planificare")
            notebook.add(discover_tab, text="🔍 Descoperire")
            
            self.planner = TripPlannerView(planner_tab)
            self.discover = DiscoverView(discover_tab)
            
        except Exception as e:
            self.show_error(str(e))
    
    def show_error(self, message):
        """Show error message"""
        self.loading_frame.destroy()
        
        error_frame = ttk.Frame(self)
        error_frame.pack(expand=True)
        
        ttk.Label(
            error_frame,
            text="Error:",  # Changed to ASCII
            font=("Helvetica", 14, "bold")
        ).pack(pady=10)
        
        ttk.Label(
            error_frame,
            text=message,
            wraplength=400
        ).pack(pady=10)
        
        ttk.Button(
            error_frame,
            text="Try Again",  # Changed to ASCII
            command=self.restart_app
        ).pack(pady=20)
    
    def restart_app(self):
        """Restart application"""
        self.destroy()
        app = MainApp()
        app.mainloop()

if __name__ == "__main__":
    # Configure proper encoding
    if sys.platform.startswith('win'):
        sys.stdout.reconfigure(encoding='utf-8')
        try:
            locale.setlocale(locale.LC_ALL, 'Romanian')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'ro_RO.UTF-8')
            except:
                locale.setlocale(locale.LC_ALL, '')
    
    app = MainApp()
    app.mainloop()
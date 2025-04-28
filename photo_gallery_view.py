import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.dialogs import Querybox
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox
import pandas as pd
import json
import os
import shutil
from datetime import datetime
from tkintermapview import TkinterMapView  # Add this import
import numpy as np  # Add this import

class PhotoGalleryView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=BOTH, expand=YES)
        
        # Add this line at the beginning of __init__
        self._photo_references = {}  # Store all PhotoImage references
        
        # Create photos directory if it doesn't exist
        self.photos_dir = os.path.join(os.path.dirname(__file__), 'photos')
        os.makedirs(self.photos_dir, exist_ok=True)
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure('Gallery.TFrame', background='white')
        self.style.configure('Card.TFrame', background='white')
        self.style.configure('PhotoInfo.TLabel', background='white', font=('Helvetica', 10))
        self.style.configure('Location.TLabel', background='white', font=('Helvetica', 12, 'bold'))
        
        self.configure(style='Gallery.TFrame')
        
        # Storage for photos data
        self.photos = []
        self.photo_references = []  # Add a list to store PhotoImage references
        self.load_photos()
        
        # Load tourist data from CSV
        self.load_tourist_data()
        
        # Dictionary for photo-location associations
        self.photo_associations = {}
        
        self.create_ui()
    
    def load_tourist_data(self):
        """Load tourist location data from CSV"""
        try:
            self.df = pd.read_csv("d:/Proiect_Concurs/data/locatii_turistice_final.csv")
            # Create a list of suggestions in format: "Location Name (City)"
            self.location_suggestions = [
                f"{row['denumire']} ({row['oras']})" 
                for _, row in self.df.iterrows()
            ]
        except Exception as e:
            print(f"Error loading tourist data: {e}")
            self.df = None
            self.location_suggestions = []

    def create_ui(self):
        # Top toolbar with Instagram-like styling
        toolbar = ttk.Frame(self, style='Gallery.TFrame')
        toolbar.pack(fill=X, pady=(10,0), padx=10)
        
        # Title
        ttk.Label(
            toolbar,
            text="Poze din Romania",
            style='Location.TLabel',
            font=('Helvetica', 16, 'bold')
        ).pack(side=LEFT, padx=10)
        
        # Single add photo button
        add_btn = ttk.Button(
            toolbar,
            text="➕ Hai sa adaugam!:)",
            style="primary.TButton",
            command=self.add_photo
        )
        add_btn.pack(side=RIGHT, padx=5)
        
        # Main content area
        self.content = ScrolledFrame(self, style='Gallery.TFrame')
        self.content.pack(fill=BOTH, expand=YES, padx=20, pady=20)
        
        self.refresh_gallery()

    def add_photo(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        
        if file_path:
            # Copy image to photos directory
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"photo_{timestamp}{os.path.splitext(file_path)[1]}"
                new_path = os.path.join(self.photos_dir, file_name)
                
                shutil.copy2(file_path, new_path)
                
                dialog = LocationInputDialog(self)
                if dialog.result:
                    photo_data = {
                        'path': new_path,
                        'location': dialog.result['location'],
                        'latitude': dialog.result['latitude'],
                        'longitude': dialog.result['longitude'],
                        'description': dialog.result['description'],
                        'date_added': timestamp,
                        'predicted_rating': dialog.result['predicted_rating'],
                        'features': dialog.result['features']
                    }
                    self.photos.append(photo_data)
                    self.save_photos()
                    self.refresh_gallery()
                    messagebox.showinfo("Success", "Photo added successfully!")
                else:
                    os.remove(new_path)  # Clean up if user cancelled
                    
            except Exception as e:
                messagebox.showerror("Error", f"Could not add photo: {str(e)}")

    def add_photos(self):
        """Allows adding photos with location association"""
        files = filedialog.askopenfilenames(
            title="Selectează Poze",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp")]
        )
        
        if not files:
            return
            
        for file in files:
            # Create custom dialog with combobox
            dialog = ttk.Toplevel(self)
            dialog.title("Asociază cu Locație")
            dialog.grab_set()
            
            frame = ttk.Frame(dialog, padding=20)
            frame.pack(fill=BOTH, expand=YES)
            
            # Location selection
            ttk.Label(frame, text="Alege locația turistică:").pack(pady=(0,5))
            location_var = tk.StringVar()
            combo = ttk.Combobox(
                frame, 
                textvariable=location_var,
                values=self.location_suggestions,
                width=50,
                state='readonly'
            )
            combo.pack(pady=(0,15))
            
            # Feature collection
            features_frame = ttk.LabelFrame(frame, text="Detalii Poză", padding=10)
            features_frame.pack(fill=X, pady=10)
            
            # Duration
            dur_frame = ttk.Frame(features_frame)
            dur_frame.pack(fill=X, pady=5)
            ttk.Label(dur_frame, text="Durată minimă (zile):").pack(side=LEFT)
            duration_var = tk.StringVar(value="1")
            ttk.Spinbox(dur_frame, from_=1, to=14, textvariable=duration_var).pack(side=LEFT, padx=5)
            
            # Season checkboxes
            season_frame = ttk.Frame(features_frame)
            season_frame.pack(fill=X, pady=5)
            season_vars = {
                'Cald': tk.BooleanVar(),
                'Oricând': tk.BooleanVar(),
                'Rece': tk.BooleanVar()
            }
            ttk.Label(season_frame, text="Sezon:").pack(side=LEFT)
            for season, var in season_vars.items():
                ttk.Checkbutton(season_frame, text=season, variable=var).pack(side=LEFT, padx=5)
            
            # Trip type checkboxes
            type_frame = ttk.Frame(features_frame)
            type_frame.pack(fill=X, pady=5)
            type_vars = {
                'Circuit': tk.BooleanVar(),
                'City Break': tk.BooleanVar(),
                'Relaxare': tk.BooleanVar()
            }
            ttk.Label(type_frame, text="Tip:").pack(side=LEFT)
            for trip_type, var in type_vars.items():
                ttk.Checkbutton(type_frame, text=trip_type, variable=var).pack(side=LEFT, padx=5)
            
            # Price category checkboxes
            price_frame = ttk.Frame(features_frame)
            price_frame.pack(fill=X, pady=5)
            price_vars = {
                'Gratuit': tk.BooleanVar(),
                'Mediu': tk.BooleanVar(),
                'Mic': tk.BooleanVar()
            }
            ttk.Label(price_frame, text="Preț:").pack(side=LEFT)
            for price, var in price_vars.items():
                ttk.Checkbutton(price_frame, text=price, variable=var).pack(side=LEFT, padx=5)
            
            # Description
            ttk.Label(frame, text="Descriere:").pack(pady=(10,5))
            description = ttk.Text(frame, height=3, width=50)
            description.pack(pady=(0,15))
            
            def on_ok():
                # Collect feature values
                features = {
                    'durata_minima': int(duration_var.get()),
                    'Cald': int(season_vars['Cald'].get()),
                    'Oricând': int(season_vars['Oricând'].get()),
                    'Rece': int(season_vars['Rece'].get()),
                    'Circuit': int(type_vars['Circuit'].get()),
                    'City Break': int(type_vars['City Break'].get()),
                    'Relaxare': int(type_vars['Relaxare'].get()),
                    'Gratuit': int(price_vars['Gratuit'].get()),
                    'Mediu': int(price_vars['Mediu'].get()),
                    'Mic': int(price_vars['Mic'].get())
                }
                
                # Get rating prediction
                from ml_engine import TripRecommender
                recommender = TripRecommender()
                prediction = recommender.predict_photo_rating(features)
                
                # Show prediction
                result = messagebox.askyesno(
                    "Predicție Rating",
                    f"Rating prezis: {prediction['predicted_rating']:.2f} ⭐\n" +
                    f"Acuratețe model: {prediction['metrics']['accuracy']:.2%}\n\n" +
                    "Doriți să salvați poza cu aceste detalii?"
                )
                
                if result:
                    dialog.features = features
                    dialog.location = combo.get()
                    dialog.description = description.get('1.0', 'end-1c')
                    dialog.predicted_rating = prediction['predicted_rating']
                    dialog.destroy()
                
            def on_cancel():
                dialog.location = None
                dialog.features = None
                dialog.description = None
                dialog.destroy()
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill=X)
            ttk.Button(btn_frame, text="Salvează", command=on_ok).pack(side=RIGHT, padx=5)
            ttk.Button(btn_frame, text="Anulează", command=on_cancel).pack(side=RIGHT)
            
            dialog.wait_window()
            
            # Process results
            if hasattr(dialog, 'location') and dialog.location:
                try:
                    # Save image with collected data
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_name = f"photo_{timestamp}{os.path.splitext(file)[1]}"
                    new_path = os.path.join(self.photos_dir, file_name)
                    
                    shutil.copy2(file, new_path)
                    
                    # Get coordinates from selected location
                    location_name = dialog.location.split(" (")[0]
                    location_data = self.df[self.df['denumire'] == location_name].iloc[0]
                    
                    # Create photo data with predictions
                    photo_data = {
                        'path': new_path,
                        'location': dialog.location,
                        'latitude': float(location_data['latitudine']),
                        'longitude': float(location_data['longitudine']),
                        'description': dialog.description,
                        'date_added': timestamp,
                        'predicted_rating': dialog.predicted_rating,
                        'features': dialog.features
                    }
                    
                    self.photos.append(photo_data)
                    self.save_photos()
                    
                except Exception as e:
                    messagebox.showerror("Eroare", f"Nu s-a putut salva poza: {str(e)}")
                    if os.path.exists(new_path):
                        os.remove(new_path)
        
        # Refresh gallery after adding all photos
        self.refresh_gallery()
        messagebox.showinfo("Succes", "Pozele au fost adăugate cu succes!")

    def add_photo_to_gallery(self, photo_path, location):
        """Adds a photo to the gallery with its association"""
        try:
            # Process image
            image = Image.open(photo_path)
            image.thumbnail((200, 200))  # Resize for thumbnail
            photo = ImageTk.PhotoImage(image)
            
            # Create frame for thumbnail and information
            frame = ttk.Frame(self.content, style='Card.TFrame')
            frame.pack(side=LEFT, padx=10, pady=10)
            
            # Thumbnail
            label = ttk.Label(frame, image=photo)
            label.image = photo  # Keep reference
            label.pack(padx=5, pady=5)
            
            # Location information
            ttk.Label(
                frame,
                text=location,
                wraplength=190,
                justify=CENTER
            ).pack(padx=5, pady=5)
            
            # Save association
            self.photo_associations[photo_path] = location
            
        except Exception as e:
            print(f"Error adding photo: {e}")

    def create_photo_card(self, photo_data):
        try:
            # Create main frames
            card = ttk.Frame(self.content, style='Card.TFrame')
            left_pane = ttk.Frame(card)
            right_pane = ttk.Frame(card)
            
            # Configure layouts
            card.pack(fill=X, pady=(0, 20))
            left_pane.pack(side=LEFT, fill=BOTH, expand=YES, padx=10)
            right_pane.pack(side=RIGHT, fill=BOTH, expand=YES, padx=10)
            
            # Load and display image
            img_key = self._add_photo_image(photo_data['path'], left_pane)
            
            # Add location and rating
            self._add_location_rating(photo_data, left_pane)
            
            # Add map
            self._add_location_map(photo_data, right_pane)
            
            # Add features if available
            if photo_data.get('features'):
                self._add_features(photo_data['features'], right_pane)
                
        except Exception as e:
            print(f"Error creating photo card: {e}")
            messagebox.showerror("Error", f"Could not load image: {photo_data['path']}")

    def _add_photo_image(self, path, parent, width=400):
        """Helper to add photo with caching"""
        img = Image.open(path)
        aspect_ratio = img.width / img.height
        new_height = int(width / aspect_ratio)
        img = img.resize((width, new_height), Image.Resampling.LANCZOS)
        
        photo_key = f"{path}_{width}"
        photo = ImageTk.PhotoImage(img)
        self._photo_references[photo_key] = photo
        
        label = ttk.Label(parent, image=photo, background='white')
        label.photo_key = photo_key
        label.pack()
        return photo_key

    def _add_location_rating(self, data, parent):
        """Helper to add location and rating info"""
        info = ttk.Frame(parent, padding=10)
        info.pack(fill=X)
        
        header = ttk.Frame(info)
        header.pack(fill=X)
        
        ttk.Label(header, text=f"📍 {data['location']}", 
                 style='Location.TLabel').pack(side=LEFT)
        
        if 'predicted_rating' in data:
            # Ensure rating is between 1-5
            rating = float(np.clip(data['predicted_rating'], 1.0, 5.0))
            full_stars = int(rating)
            decimal_part = rating - full_stars
            
            # Calculate partial star
            if decimal_part > 0:
                stars = "★" * full_stars + "⯨" + "☆" * (4 - full_stars)
            else:
                stars = "★" * full_stars + "☆" * (5 - full_stars)
            
            rating_frame = ttk.Frame(header)
            rating_frame.pack(side=RIGHT)
            
            ttk.Label(rating_frame, text=stars, font=("Helvetica", 14),
                     foreground="#FFD700").pack(side=LEFT, padx=(0, 5))
            
            ttk.Label(rating_frame, text=f"{rating:.1f}", 
                     font=("Helvetica", 12, "bold"),
                     foreground="#2c3e50").pack(side=LEFT)

    def _add_location_map(self, data, parent):
        """Helper to add map widget"""
        map_frame = ttk.LabelFrame(parent, text="Locație", padding=10)
        map_frame.pack(fill=BOTH, expand=YES)
        
        map_widget = TkinterMapView(map_frame, width=400, height=300)
        map_widget.pack(fill=BOTH, expand=YES)
        
        if 'latitude' in data and 'longitude' in data:
            lat = float(data['latitude'])
            lon = float(data['longitude'])
            map_widget.set_position(lat, lon)
            map_widget.set_zoom(15)
            map_widget.set_marker(
                lat, lon,
                text=data['location'],
                marker_color_circle="red",
                marker_color_outside="darkred"
            )

    def _add_features(self, features, parent):
        """Helper to add features display"""
        features_frame = ttk.LabelFrame(parent, text="Caracteristici", padding=10)
        features_frame.pack(fill=X, pady=10)
        
        for key, value in features.items():
            if value:
                ttk.Label(
                    features_frame,
                    text=f"• {key}",
                    style='PhotoInfo.TLabel'
                ).pack(anchor=W)

    def refresh_gallery(self):
        # Clear current gallery
        for widget in self.content.winfo_children():
            widget.destroy()
        
        # Clear old photo references
        self._photo_references.clear()
        
        # Sort photos by date added (newest first)
        sorted_photos = sorted(
            self.photos,
            key=lambda x: x.get('date_added', ''),
            reverse=True
        )
        
        if not sorted_photos:
            # Show empty state
            ttk.Label(
                self.content,
                text="No photos yet. Click the '+' button to add some!",
                style='PhotoInfo.TLabel',
                font=('Helvetica', 12)
            ).pack(pady=50)
        else:
            # Add all photos
            for photo_data in sorted_photos:
                self.create_photo_card(photo_data)
    
    def load_photos(self):
        try:
            json_path = os.path.join(self.photos_dir, 'photos.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.photos = json.load(f)
        except Exception as e:
            print(f"Error loading photos: {e}")
            self.photos = []
    
    def save_photos(self):
        try:
            json_path = os.path.join(self.photos_dir, 'photos.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.photos, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving photos: {e}")
            messagebox.showerror("Error", "Could not save photo data")

    def __del__(self):
        """Cleanup when gallery is destroyed"""
        self._photo_references.clear()

class LocationInputDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Adaugă Locație Poză")
        self.result = None
        
        # Get locations data
        try:
            self.df = pd.read_csv("d:/Proiect_Concurs/data/locatii_turistice_final.csv")
            self.locations = [
                f"{row['denumire']} ({row['oras']})"
                for _, row in self.df.iterrows()
            ]
        except Exception as e:
            print(f"Error loading locations: {e}")
            self.locations = []
        
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # Location selector with "Add New" option
        location_frame = ttk.Frame(main_frame)
        location_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(location_frame, text="Alege locația:").pack(side=LEFT)
        self.location_var = ttk.StringVar()
        
        # Add "New Location" at the start of suggestions
        self.locations = ["➕ Adaugă locație nouă..."] + self.locations
        
        self.location_combo = ttk.Combobox(
            location_frame,
            textvariable=self.location_var,
            values=self.locations,
            width=45,
            state='readonly'
        )
        self.location_combo.pack(side=LEFT, padx=5)
        self.location_combo.bind('<<ComboboxSelected>>', self.on_location_select)
        
        # New Location Entry Frame (initially hidden)
        self.new_location_frame = ttk.LabelFrame(main_frame, text="Detalii Locație Nouă", padding=10)
        
        # Location name entry
        ttk.Label(self.new_location_frame, text="Nume locație:").pack(anchor=W)
        self.name_entry = ttk.Entry(self.new_location_frame, width=50)
        self.name_entry.pack(fill=X, pady=(0, 5))
        
        # City entry
        ttk.Label(self.new_location_frame, text="Oraș:").pack(anchor=W)
        self.city_entry = ttk.Entry(self.new_location_frame, width=50)
        self.city_entry.pack(fill=X, pady=(0, 5))
        
        # Coordinates
        coords_frame = ttk.Frame(self.new_location_frame)
        coords_frame.pack(fill=X, pady=5)
        
        ttk.Label(coords_frame, text="Latitudine:").pack(side=LEFT)
        self.lat_var = tk.StringVar()
        ttk.Entry(coords_frame, textvariable=self.lat_var, width=15).pack(side=LEFT, padx=5)
        
        ttk.Label(coords_frame, text="Longitudine:").pack(side=LEFT, padx=(10,0))
        self.lon_var = tk.StringVar()
        ttk.Entry(coords_frame, textvariable=self.lon_var, width=15).pack(side=LEFT, padx=5)
        
        # Feature collection - fixed column names
        features_frame = ttk.LabelFrame(main_frame, text="Detalii Poză", padding=10)
        features_frame.pack(fill=X, pady=10)
        
        # Duration
        dur_frame = ttk.Frame(features_frame)
        dur_frame.pack(fill=X, pady=5)
        ttk.Label(dur_frame, text="Durată minimă (zile):").pack(side=LEFT)
        self.duration_var = tk.StringVar(value="1")
        ttk.Spinbox(dur_frame, from_=1, to=14, textvariable=self.duration_var).pack(side=LEFT, padx=5)
        
        # Fixed feature columns for ML model
        self.feature_vars = {
            'durata_minima': self.duration_var,
            'Cald': tk.BooleanVar(),
            'Oricand': tk.BooleanVar(),
            'Rece': tk.BooleanVar(),
            'Circuit': tk.BooleanVar(),
            'CityBreak': tk.BooleanVar(),
            'Relaxare': tk.BooleanVar(),
            'Gratuit': tk.BooleanVar(),
            'Mediu': tk.BooleanVar(),
            'Mic': tk.BooleanVar()
        }
        
        # Create feature checkboxes with proper labels
        self.create_feature_checkboxes(features_frame)
        
        ttk.Label(main_frame, text="Descriere:").pack(anchor=W)
        self.description = ttk.Text(main_frame, height=3, width=50)
        self.description.pack(fill=X, pady=(0, 15))
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(
            btn_frame,
            text="Anulează",
            command=self.destroy,
            style="secondary.TButton"
        ).pack(side=RIGHT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Salvează",
            command=self.save,
            style="primary.TButton"
        ).pack(side=RIGHT)
        
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)
    
    def on_location_select(self, event=None):
        """Handle location selection"""
        if self.location_var.get() == "➕ Adaugă locație nouă...":
            self.new_location_frame.pack(fill=X, pady=10)
        else:
            self.new_location_frame.pack_forget()

    def create_feature_checkboxes(self, parent):
        """Create organized feature checkboxes"""
        # Season group
        season_frame = ttk.LabelFrame(parent, text="Sezon", padding=5)
        season_frame.pack(fill=X, pady=5)
        for feature in ['Cald', 'Oricand', 'Rece']:
            ttk.Checkbutton(
                season_frame, 
                text=feature.replace('_', ' '), 
                variable=self.feature_vars[feature]
            ).pack(side=LEFT, padx=5)

        # Trip type group
        type_frame = ttk.LabelFrame(parent, text="Tip Călătorie", padding=5)
        type_frame.pack(fill=X, pady=5)
        for feature in ['Circuit', 'CityBreak', 'Relaxare']:
            ttk.Checkbutton(
                type_frame, 
                text=feature.replace('_', ' '), 
                variable=self.feature_vars[feature]
            ).pack(side=LEFT, padx=5)

        # Price group
        price_frame = ttk.LabelFrame(parent, text="Preț", padding=5)
        price_frame.pack(fill=X, pady=5)
        for feature in ['Gratuit', 'Mediu', 'Mic']:
            ttk.Checkbutton(
                price_frame, 
                text=feature, 
                variable=self.feature_vars[feature]
            ).pack(side=LEFT, padx=5)

    def save(self):
        """Save location data with support for new locations"""
        try:
            if self.location_var.get() == "➕ Adaugă locație nouă...":
                # Validate new location data
                if not self.name_entry.get() or not self.city_entry.get():
                    messagebox.showerror("Eroare", "Completează numele locației și orașul")
                    return
                
                location = f"{self.name_entry.get()} ({self.city_entry.get()})"
                latitude = float(self.lat_var.get())
                longitude = float(self.lon_var.get())
            else:
                # Get existing location data
                location = self.location_var.get()
                location_name = location.split(" (")[0]
                location_data = self.df[self.df['denumire'] == location_name].iloc[0]
                latitude = float(location_data['latitudine'])
                longitude = float(location_data['longitudine'])
            
            # Collect feature values with exact column names
            features = {
                'durata_minima': int(self.duration_var.get()),
                'Cald': int(self.feature_vars['Cald'].get()),
                'Oricand': int(self.feature_vars['Oricand'].get()),
                'Rece': int(self.feature_vars['Rece'].get()),
                'Circuit': int(self.feature_vars['Circuit'].get()),
                'CityBreak': int(self.feature_vars['CityBreak'].get()),
                'Relaxare': int(self.feature_vars['Relaxare'].get()),
                'Gratuit': int(self.feature_vars['Gratuit'].get()),
                'Mediu': int(self.feature_vars['Mediu'].get()),
                'Mic': int(self.feature_vars['Mic'].get())
            }
            
            # Get rating prediction
            from ml_engine import TripRecommender
            recommender = TripRecommender()
            prediction = recommender.predict_photo_rating(features)
            
            # Store result
            self.result = {
                'location': location,
                'latitude': latitude,
                'longitude': longitude,
                'description': self.description.get('1.0', 'end-1c'),
                'predicted_rating': prediction['predicted_rating'],
                'features': features
            }
            
            # Show prediction with safe access to metrics
            accuracy = prediction.get('metrics', {}).get('accuracy', 0.0)
            messagebox.showinfo(
                "Predicție Rating",
                f"Rating prezis: {prediction['predicted_rating']:.2f} ⭐\n" +
                f"Acuratețe prezicere: {accuracy:.1%}"
            )
            
            self.destroy()
            
        except Exception as e:
            messagebox.showerror(
                "Eroare",
                f"Nu s-au putut procesa datele: {str(e)}"
            )

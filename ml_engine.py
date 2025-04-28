import pandas as pd
import numpy as np
import warnings
import os
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, precision_score
from sklearn.ensemble import GradientBoostingRegressor

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import MinMaxScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    warnings.warn("scikit-learn not found. Using basic recommendation system.")
    SKLEARN_AVAILABLE = False

class TripRecommender:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.csv_path = os.path.join(self.data_dir, 'locatii_turistice_final.csv')
        self.df = pd.read_csv(self.csv_path)
        
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(stop_words='english')
            self.scaler = MinMaxScaler()
            self.setup_features()
        else:
            self.setup_basic_features()
        
        # Initialize NLP tools
        nltk.download('stopwords')
        nltk.download('wordnet')
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('romanian'))
        
        # Update category mappings with complete list
        self.category_keywords = {
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
        
        # Simplified category features
        self.category_features = {
            'museums': {'weight': 1.2, 'preferred_time': 'morning'},
            'historic': {'weight': 1.1, 'preferred_time': 'morning'},
            'cultural': {'weight': 1.0, 'preferred_time': 'afternoon'},
            'nature': {'weight': 0.9, 'preferred_time': 'afternoon'}
        }

        self.gb_model = None
        self.lr_model = None
        self.setup_gradient_boosting()
        self.setup_linear_regression()

    def setup_features(self):
        """Pregătește caracteristicile pentru ML"""
        self.df['text_features'] = self.df.apply(
            lambda x: ' '.join([
                str(x['denumire']),
                str(x['categorie']),
                str(x['tip_calatorie']),
                str(x['cuvinte_cheie'])
            ]), 
            axis=1
        )
        
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['text_features'])
        
        numeric_features = ['rating_general', 'nr_recenzii']
        self.df[numeric_features] = self.scaler.fit_transform(self.df[numeric_features])
    
    def setup_basic_features(self):
        """Setup basic features without sklearn"""
        self.df['text_features'] = self.df.apply(
            lambda x: ' '.join([
                str(x['denumire']),
                str(x['categorie']),
                str(x['tip_calatorie']),
                str(x['cuvinte_cheie'])
            ]), 
            axis=1
        )

    def setup_gradient_boosting(self):
        """Initialize and train the Gradient Boosting model"""
        try:
            # Select features for training
            feature_cols = ["durata_minima", "Cald", "Oricând", "Rece", "Circuit",
                          "City Break", "Relaxare", "Gratuit", "Mediu", "Mic"]
            
            X = self.df[feature_cols]
            y = self.df["rating_general"]

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Initialize and train model
            self.gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            self.gb_model.fit(X_train, y_train)

            # Calculate metrics
            y_pred = self.gb_model.predict(X_test)
            self.gb_metrics = {
                'mse': mean_squared_error(y_test, y_pred),
                'r2': r2_score(y_test, y_pred),
                'mae': np.mean(np.abs(y_test - y_pred))
            }

        except Exception as e:
            print(f"Error setting up Gradient Boosting: {e}")
            self.gb_model = None

    def setup_linear_regression(self):
        """Initialize and train the Linear Regression model"""
        try:
            # Select features for training
            feature_cols = ["durata_minima", "Cald", "Oricând", "Rece", "Circuit",
                          "City Break", "Relaxare", "Gratuit", "Mediu", "Mic"]
            
            X = self.df[feature_cols]
            y = self.df["rating_general"]

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Initialize and train model
            self.lr_model = LinearRegression()
            self.lr_model.fit(X_train, y_train)

            # Make predictions
            y_pred = self.lr_model.predict(X_test)

            # Calculate metrics
            self.lr_metrics = {
                'mse': mean_squared_error(y_test, y_pred),
                'r2': r2_score(y_test, y_pred)
            }

            # Calculate classification metrics
            y_test_class = (y_test >= 4.0).astype(int)
            y_pred_class = (y_pred >= 4.0).astype(int)
            
            self.lr_metrics.update({
                'accuracy': accuracy_score(y_test_class, y_pred_class),
                'precision': precision_score(y_test_class, y_pred_class, zero_division=0)
            })

        except Exception as e:
            print(f"Error setting up Linear Regression: {e}")
            self.lr_model = None

    def process_text_input(self, text_input):
        """Process user input text and return similarity and probability dictionaries"""
        text_preprocessed = self.preprocess_text(text_input)
        
        similarities = {}
        probabilities = {}
        
        for category, keywords in self.category_keywords.items():
            category_text = " ".join(keywords)
            category_preprocessed = self.preprocess_text(category_text)
            
            vectorizer = CountVectorizer().fit_transform([text_preprocessed, category_preprocessed])
            similarity = cosine_similarity(vectorizer[0:1], vectorizer[1:])[0][0]
            
            probability = (similarity + 1) / 2 if similarity > 0.1 else 0
            
            similarities[category] = similarity
            probabilities[category] = np.float64(round(probability, 2))
        
        return similarities, probabilities

    def get_recommendations(self, text_input, selected_city, top_n=2):
        """Optimized recommendation engine"""
        try:
            # Get text matches
            matches = self.process_text_input(text_input)
            
            # Filter by city and score
            city_locations = self.df[self.df['oras'] == selected_city]
            scored_locations = []
            
            for _, loc in city_locations.iterrows():
                score = self.calculate_location_score(loc, matches)
                if score > 0.1:  # Only keep relevant matches
                    scored_locations.append((loc, score))
            
            # Sort and return top N
            return [loc for loc, _ in sorted(
                scored_locations,
                key=lambda x: x[1],
                reverse=True
            )[:top_n]]
            
        except Exception as e:
            print(f"Recommendation error: {e}")
            return []

    def calculate_location_score(self, location, matches):
        """Optimized scoring function"""
        try:
            category = location['categorie'].lower()
            base_score = matches.get(category, 0)
            
            # Apply category weights
            if cat_info := self.category_features.get(category):
                base_score *= cat_info['weight']
            
            # Adjust by rating
            rating_factor = min(location.get('rating_general', 3.0) / 5.0, 1.0)
            
            return base_score * (0.7 + (0.3 * rating_factor))
            
        except Exception as e:
            print(f"Scoring error: {e}")
            return 0.0

    def preprocess_text(self, text):
        """Preprocess text for similarity comparison"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        words = text.split()
        words = [w for w in words if w not in self.stop_words]
        words = [self.lemmatizer.lemmatize(w) for w in words]
        return " ".join(words)

    def generate_itinerary(self, location, duration, preferences):
        """Generează un itinerariu personalizat"""
        city_locations = self.df[self.df['oras'] == location]
        
        morning_activities = city_locations[
            city_locations['categorie'].isin(['Museum', 'Architecture', 'Historic'])
        ]
        afternoon_activities = city_locations[
            city_locations['categorie'].isin(['Park', 'Nature', 'Shopping'])
        ]
        evening_activities = city_locations[
            city_locations['categorie'].isin(['Entertainment', 'Restaurant', 'Cultural'])
        ]
        
        itinerary = {}
        for day in range(1, duration + 1):
            itinerary[day] = {
                'morning': morning_activities.sample(1).iloc[0].to_dict() if not morning_activities.empty else None,
                'afternoon': afternoon_activities.sample(1).iloc[0].to_dict() if not afternoon_activities.empty else None,
                'evening': evening_activities.sample(1).iloc[0].to_dict() if not evening_activities.empty else None
            }
        
        return itinerary
    
    def learn_from_feedback(self, user_feedback):
        """Învață din feedback-ul utilizatorului"""
        feedback_df = pd.DataFrame(user_feedback)
        if not hasattr(self, 'feedback_history'):
            self.feedback_history = []
        self.feedback_history.append(feedback_df)
        
        if len(self.feedback_history) > 10:
            self._update_model()
    
    def _update_model(self):
        """Actualizează modelul cu datele de feedback"""
        all_feedback = pd.concat(self.feedback_history)
        feedback_path = os.path.join(self.data_dir, 'user_feedback.csv')
        all_feedback.to_csv(feedback_path, index=False)

    def predict_photo_rating(self, features):
        """Optimized rating prediction"""
        try:
            # Calculate individual scores
            scores = {
                'activity': features['durata_minima'] / 14.0,  # normalize to 0-1
                'seasonal': (features.get('Cald', 0) + features.get('Oricand', 0) + features.get('Rece', 0)) / 3.0,
                'type': (features.get('Circuit', 0) + features.get('CityBreak', 0) + features.get('Relaxare', 0)) / 3.0,
                'cost': (features.get('Gratuit', 0) + features.get('Mic', 0) * 0.8 + features.get('Mediu', 0) * 0.6) / 2.0
            }
            
            # Calculate weighted score (0-1 range)
            weights = {'activity': 0.3, 'seasonal': 0.2, 'type': 0.3, 'cost': 0.2}
            weighted_score = sum(score * weights[key] for key, score in scores.items())
            
            # Scale to 1-5 range properly
            final_rating = 1.0 + (weighted_score * 4.0)  # This ensures range between 1-5
            
            # Ensure rating stays within bounds
            final_rating = float(np.clip(final_rating, 1.0, 5.0))
            
            # Calculate accuracy metric
            accuracy = min(weighted_score + 0.5, 1.0)  # Scale between 0.5-1.0
            
            return {
                'predicted_rating': final_rating,
                'confidence': min(weighted_score + 0.5, 1.0),
                'features_used': list(scores.keys()),
                'metrics': {
                    'accuracy': accuracy,
                    'confidence': min(weighted_score + 0.5, 1.0)
                }
            }
            
        except Exception as e:
            print(f"Rating prediction error: {e}")
            return {
                'predicted_rating': 3.0,
                'confidence': 0.5,
                'error': str(e),
                'metrics': {
                    'accuracy': 0.5,
                    'confidence': 0.5
                }
            }

    def predict_rating_gb(self, features):
        """Predict rating using Gradient Boosting model"""
        try:
            if self.gb_model is None:
                return None

            # Ensure features are in correct format
            feature_cols = ["durata_minima", "Cald", "Oricând", "Rece", "Circuit",
                          "City Break", "Relaxare", "Gratuit", "Mediu", "Mic"]
            feature_vector = np.array([[features.get(col, 0) for col in feature_cols]])
            
            # Make prediction
            predicted_rating = self.gb_model.predict(feature_vector)[0]
            
            return {
                'predicted_rating': max(1.0, min(5.0, predicted_rating)),
                'metrics': self.gb_metrics,
                'model': 'gradient_boosting'
            }

        except Exception as e:
            print(f"Error predicting with Gradient Boosting: {e}")
            return None

    def predict_rating_lr(self, features):
        """Predict rating using Linear Regression model"""
        try:
            if self.lr_model is None:
                return None

            # Ensure features are in correct format
            feature_cols = ["durata_minima", "Cald", "Oricând", "Rece", "Circuit",
                          "City Break", "Relaxare", "Gratuit", "Mediu", "Mic"]
            feature_vector = np.array([[features.get(col, 0) for col in feature_cols]])
            
            # Make prediction
            predicted_rating = self.lr_model.predict(feature_vector)[0]
            
            return {
                'predicted_rating': max(1.0, min(5.0, predicted_rating)),
                'metrics': self.lr_metrics,
                'model': 'linear_regression'
            }

        except Exception as e:
            print(f"Error predicting with Linear Regression: {e}")
            return None

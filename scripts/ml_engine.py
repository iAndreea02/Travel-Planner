import pandas as pd
import numpy as np
import warnings
import os

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.preprocessing import MinMaxScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    warnings.warn("scikit-learn not found. Using basic recommendation system.")
    SKLEARN_AVAILABLE = False

class TripRecommender:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.csv_path = os.path.join(self.data_dir, 'locatii_romania_AI_ready.csv')
        
        if not os.path.exists(self.csv_path):
            print("🔄 Se colectează date noi...")
            from data_collector import DataCollector
            collector = DataCollector()
            collector.collect_and_save_data()
        
        self.df = pd.read_csv(self.csv_path)
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(stop_words='english')
            self.scaler = MinMaxScaler()
            self.setup_features()
        else:
            # Fallback to basic recommendation system
            self.setup_basic_features()
    
    def setup_features(self):
        """Pregătește caracteristicile pentru ML"""
        # Combină textul pentru analiza de similaritate
        self.df['text_features'] = self.df.apply(
            lambda x: ' '.join([
                str(x['nume locatie']), 
                str(x['categorie']), 
                str(x['tip calatorie']),
                ' '.join(eval(x['cuvinte cheie']))
            ]), 
            axis=1
        )
        
        # Creează matricea TF-IDF
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['text_features'])
        
        # Normalizează scorurile numerice
        numeric_features = ['rating general', 'popularitate']
        self.df[numeric_features] = self.scaler.fit_transform(self.df[numeric_features])
    
    def setup_basic_features(self):
        """Setup basic features without sklearn"""
        self.df['text_features'] = self.df.apply(
            lambda x: ' '.join([
                str(x['nume locatie']), 
                str(x['categorie']), 
                str(x['tip calatorie']),
                ' '.join(eval(x['cuvinte cheie']))
            ]), 
            axis=1
        )
    
    def get_recommendations(self, user_input, filters=None, top_n=5):
        """Generează recomandări bazate pe input-ul utilizatorului"""
        if SKLEARN_AVAILABLE:
            # Vectorizează input-ul utilizatorului
            user_vector = self.vectorizer.transform([user_input])
            
            # Calculează similaritatea cu toate locațiile
            similarities = cosine_similarity(user_vector, self.tfidf_matrix).flatten()
            
            # Aplică filtrele
            if filters:
                mask = np.ones(len(self.df), dtype=bool)
                if 'oras' in filters:
                    mask &= self.df['oras'] == filters['oras']
                if 'tip_calatorie' in filters:
                    mask &= self.df['tip calatorie'] == filters['tip_calatorie']
                if 'sezon' in filters:
                    mask &= self.df['sezon recomandat'] == filters['sezon']
                similarities = similarities * mask
            
            # Obține cele mai bune potriviri
            top_indices = similarities.argsort()[-top_n:][::-1]
            
            return self.df.iloc[top_indices].to_dict('records')
        else:
            # Simple keyword matching
            keywords = user_input.lower().split()
            scores = []
            
            for _, row in self.df.iterrows():
                text = row['text_features'].lower()
                score = sum(1 for keyword in keywords if keyword in text)
                scores.append(score)
            
            # Get top matches
            top_indices = np.argsort(scores)[-top_n:][::-1]
            return self.df.iloc[top_indices].to_dict('records')
    
    def generate_itinerary(self, location, duration, preferences):
        """Generează un itinerariu personalizat"""
        city_locations = self.df[self.df['oras'] == location]
        
        # Grupează locațiile după categorie
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
        # Salvează preferințele pentru antrenare viitoare
        feedback_df = pd.DataFrame(user_feedback)
        if not hasattr(self, 'feedback_history'):
            self.feedback_history = []
        self.feedback_history.append(feedback_df)
        
        # Ajustează scorurile bazate pe feedback
        if len(self.feedback_history) > 10:
            self._update_model()
    
    def _update_model(self):
        """Actualizează modelul cu datele de feedback"""
        all_feedback = pd.concat(self.feedback_history)
        feedback_path = os.path.join(self.data_dir, 'user_feedback.csv')
        all_feedback.to_csv(feedback_path, index=False)

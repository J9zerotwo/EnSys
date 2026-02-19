import os
import pickle
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer

class TextPreprocessor:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        self.analyzer = SentimentIntensityAnalyzer()
        self.menu_keywords = {'menu', 'dessert', 'drinks', 'main course', 'pasta', 'salad', 'sides', 'baked lasagna', 'seafood sotanghon'}
        
        # Initialize TF-IDF vectorizer
        self.vectorizer = None
        self.load_or_fit_vectorizer()

    def load_or_fit_vectorizer(self):
        # Try to load pre-trained vectorizer
        vectorizer_path = 'tfidf_vectorizer.pkl'
        if os.path.exists(vectorizer_path):
            with open(vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
        else:
            # Load the annotated_empatheticdialogues.csv dataset
            dataset_path = 'annotated_empatheticdialogues.csv'
            try:
                dataset = pd.read_csv(dataset_path)
                sample_data = dataset['text_column'].tolist()  # Adjust 'text_column' to match your dataset
            except FileNotFoundError:
                print(f"Dataset file '{dataset_path}' not found.")
                sample_data = [
                    "Can I see the menu?",
                    "I would like to order the baked lasagna.",
                    "What are the dessert options?",
                    "I love the seafood sotanghon here!",
                    "Can you recommend a good drink?",
                    "The main course options look great.",
                    "I would like a salad with my meal.",
                    "Do you have any sides available?",
                    "Your pasta dishes are amazing!",
                    "Can you tell me more about the drinks?"
                ]
            
            # Fit the TF-IDF vectorizer on sample data
            self.vectorizer = TfidfVectorizer()
            self.vectorizer.fit(sample_data)
            
            # Save the fitted vectorizer
            with open(vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)

    def preprocess(self, text):
        tokens = word_tokenize(text)
        lowercased = [w.lower() for w in tokens]
        filtered = [w for w in lowercased if w not in self.stop_words or w in self.menu_keywords]
        lemmatized = [w if w in self.menu_keywords else self.lemmatizer.lemmatize(w) for w in filtered]
        preprocessed_text = ' '.join(lemmatized)
        return preprocessed_text

    def get_sentiment(self, text):
        sentiment_scores = self.analyzer.polarity_scores(text)
        return sentiment_scores

    def transform_to_tfidf(self, text):
        if self.vectorizer is None:
            raise ValueError("TF-IDF vectorizer is not fitted.")
        
        preprocessed_text = self.preprocess(text)
        tfidf_vector = self.vectorizer.transform([preprocessed_text])
        dense_tfidf_vector = tfidf_vector.toarray()[0]
        return dense_tfidf_vector

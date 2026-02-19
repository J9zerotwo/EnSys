import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics.pairwise import cosine_similarity

class EmotionModel:
    def __init__(self, engine):
        self.vectorizer = TfidfVectorizer()
        self.model = LogisticRegression() 
        self.engine = engine

    # Load the dataset from a CSV file
    def load_dataset(self, file_path):
        df = pd.read_csv(file_path)
        combined_text = df['context'].astype(str) + ' ' + df['prompt'].astype(str) + ' ' + df['utterance'].astype(str)
        labels = df['emotion'].tolist()
        return combined_text.tolist(), labels

    # Train the model using the dataset
    def train_model(self, file_path):
        # Load dataset
        X, y = self.load_dataset(file_path)
        
        # Split dataset into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Vectorize the training data
        X_train_vec = self.vectorizer.fit_transform(X_train)
        
        # Train the model
        self.model.fit(X_train_vec, y_train)

        # Evaluate model on test set
        X_test_vec = self.vectorizer.transform(X_test)
        y_pred = self.model.predict(X_test_vec)
        accuracy = accuracy_score(y_test, y_pred)
        print("Model accuracy:", accuracy)

    # Predict emotion for a given text
    def predict_emotion(self, text):
        text_vector = self.vectorizer.transform([text])
        predicted_emotion = self.model.predict(text_vector)
        return predicted_emotion[0]  # Return the predicted emotion

    def retrieve_exemplar(self, user_input):
        tfidf_vector = self.vectorizer.transform([user_input])
        cosine_similarities = cosine_similarity(tfidf_vector, self.tfidf_matrix)
        most_similar_index = cosine_similarities.argmax()
        return self.dataset[most_similar_index]

    # Evaluate the model using the test data
    def evaluate_model(self, X_test, y_test):
        # Ensure the vectorizer is fitted
        X_test_vec = self.vectorizer.transform(X_test)
        
        # Predict the labels for the test data
        y_pred = self.model.predict(X_test_vec)
        
        # Calculate evaluation metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        return {
            "Accuracy": accuracy,
            "Precision": precision,
            "Recall": recall,
            "F1": f1
        }
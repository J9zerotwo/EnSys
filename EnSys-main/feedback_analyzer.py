from nltk.sentiment import SentimentIntensityAnalyzer
import re

class FeedbackAnalyzer:
    def __init__(self, conversation):
        self.conversation = conversation
        self.analyzer = SentimentIntensityAnalyzer()

    def split_statements(self, message):
        # Split based on punctuation that usually denotes the end of a statement.
        statements = re.split(r'[.!?]', message)
        return [statement.strip() for statement in statements if statement.strip()]

    def analyze_feedback(self):
        detailed_feedback = []
        unique_messages = set()  # To store unique messages
        for message in self.conversation:
            statements = self.split_statements(message)
            for statement in statements:
                sentiment = self.analyzer.polarity_scores(statement)
                if statement not in unique_messages:  # Check if message is unique
                    unique_messages.add(statement)
                    detailed_feedback.append({
                        'message': statement,
                        'sentiment': sentiment
                    })
        return detailed_feedback

    def categorize_feedback(self, feedback_data):
        categories = {
            'food_quality': {'compliments': [], 'complaints': []},
            'service_quality': {'compliments': [], 'complaints': []},
            'ambiance': {'compliments': [], 'complaints': []},
            'cleanliness': {'compliments': [], 'complaints': []},
            'affordability': {'compliments': [], 'complaints': []},
        }

        for feedback in feedback_data:
            message = feedback['message'].lower()
            sentiment = feedback['sentiment']

            if any(word in message for word in ['food', 'dish', 'meal', 'dessert']):
                category = 'food_quality'
            elif any(word in message for word in ['service', 'waiter', 'staff', 'manager']):
                category = 'service_quality'
            elif any(word in message for word in ['ambiance', 'atmosphere', 'environment', 'noise']):
                category = 'ambiance'
            elif any(word in message for word in ['cleanliness', 'restroom', 'clean', 'hygiene']):
                category = 'cleanliness'
            elif any(word in message for word in ['price', 'cost', 'expensive', 'affordable']):
                category = 'affordability'
            else:
                continue

            if sentiment['compound'] >= 0.05:
                if feedback not in categories[category]['compliments']:
                    categories[category]['compliments'].append(feedback)
            elif sentiment['compound'] <= -0.05:
                if feedback not in categories[category]['complaints']:
                    categories[category]['complaints'].append(feedback)

        return categories

    def calculate_percentages(self, categorized_feedback):
        total_feedback = sum(len(feedbacks['compliments']) + len(feedbacks['complaints']) for feedbacks in categorized_feedback.values())
        percentages = {}

        if total_feedback > 0:
            for category, feedbacks in categorized_feedback.items():
                total_category_feedback = len(feedbacks['compliments']) + len(feedbacks['complaints'])
                percentages[category] = (total_category_feedback / total_feedback) * 100
        else:
            percentages = {category: 0 for category in categorized_feedback.keys()}

        return percentages

    def generate_essay_summary(self, categorized_feedback, category_percentages):
        summary = "Based on the feedback received, customers had varied experiences at the restaurant.\n"

        for category, feedbacks in categorized_feedback.items():
            compliments_set = set()  # Set to store unique compliments
            complaints_set = set()   # Set to store unique complaints

            if feedbacks['compliments']:
                summary += f"{category.replace('_', ' ').capitalize()} received several compliments ({category_percentages[category]:.2f}% of total feedback). "
                for feedback in feedbacks['compliments']:
                    compliments_set.add(feedback['message'])  # Add to set to remove duplicates
                for compliment in compliments_set:  # Iterate over unique compliments
                    summary += f"One customer mentioned, '{compliment}' "
                summary += "\n\n"
            if feedbacks['complaints']:
                summary += f"{category.replace('_', ' ').capitalize()} received some complaints ({category_percentages[category]:.2f}% of total feedback). "
                for feedback in feedbacks['complaints']:
                    complaints_set.add(feedback['message'])  # Add to set to remove duplicates
                for complaint in complaints_set:  # Iterate over unique complaints
                    summary += f"One customer mentioned, '{complaint}' "
                summary += "\n\n"

        summary += "\n\nTo enhance customer satisfaction and loyalty, addressing these specific aspects will be crucial."
        return summary

    def interpret_feedback(self):
        feedback_data = self.analyze_feedback()
        categorized_feedback = self.categorize_feedback(feedback_data)
        category_percentages = self.calculate_percentages(categorized_feedback)
        summary = self.generate_essay_summary(categorized_feedback, category_percentages)
        return categorized_feedback, summary

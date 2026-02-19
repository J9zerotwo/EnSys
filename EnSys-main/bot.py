import os, random
import openai
import pandas as pd
from dotenv import load_dotenv
from model import EmotionModel
from preprocess import TextPreprocessor
from feedback_analyzer import FeedbackAnalyzer

def load_config():
    dotenv_path = os.path.join(os.path.dirname(__file__), 'static', 'key.env')
    load_dotenv(dotenv_path)
    return os.getenv('OPENAI_API_KEY')

class EnSysBot:

    def __init__(self, engine, api_key):
        self.engine = engine
        self.api_key = api_key
        self.last_topic = None
        self.conversation = []
        self.feedback = []
        self.feedback_data = []
        self.feedback_analyzer = FeedbackAnalyzer([])  # Initialize FeedbackAnalyzer with empty conversation
        self.preprocessor = TextPreprocessor() 
        self.model = EmotionModel(engine)
        openai.api_key = self.api_key

        # Load restaurant data
        self.restaurant_data = self.load_restaurant_data()
        self.menu_categories = ['dessert', 'drinks', 'main course', 'pasta', 'salad', 'sides']
        
        # Add a pre-prompt that establishes the bot's identity
        self.pre_prompt = (
            "You are EnSys, a friendly and knowledgeable customer service chatbot. "
            "You assist customers with their inquiries about the menu, the restaurant, take feedback, and above all check on their overall experience. "
            "Make sure to use proper punctuations such as exclamation marks and question marks. "
            "Do not make any sort of order, reservation, and recommendation. "
            "When discussing the menu, strictly stick to the following categories: Desserts, Drinks, Main Course, Pasta, Salad, and Sides. "
            "Please maintain a helpful, polite, and professional tone in your responses."
        )

    def add_system_message(self, content):
        self.conversation.append({"role": "system", "content": content})

    def add_user_message(self, content):
        self.conversation.append({"role": "user", "content": content})
        self.feedback.append(content)

    def save_chat_history(self, filename='chat_history.txt'):
        with open(filename, 'a') as file:
            for message in self.conversation:
                file.write(f"{message['role'].capitalize()}: {message['content']}\n")
            file.write("\n--- End of Conversation ---\n\n")

    def generate_suggestion_prompt(self, context, sentiment):
        if sentiment == "positive":
            base_prompt = "Generate three positive suggestion prompts in customer point of view, about food quality, service, staff, cleanliness, affordability, or ambiance for satisfied customers of Atin-atehan."
        elif sentiment == "neutral":
            base_prompt = "Generate three positive suggestion prompts in customer point of view, about food quality, service, staff, cleanliness, affordability, or ambiance for customers who are neither satisfied nor unsatisfied of Atin-atehan."
        else:
            base_prompt = "Generate three positive suggestion prompts in customer point of view, about food quality, service, staff, cleanliness, affordability, or ambiance for unsatisfied or disappointed customers of Atin-atehan."

        response = openai.ChatCompletion.create(
            model=self.engine,
            messages=[{"role": "system", "content": base_prompt + "\n\n" + context}],
            max_tokens=150,
            temperature=0.7,
            top_p=1.0,
            n=1
        )
        suggestions = response.choices[0].message['content'].strip().split('\n')

        # Clean up suggestions to remove any numbering and filter out empty or incomplete ones
        cleaned_suggestions = [suggestion.lstrip("0123456789. ").strip() for suggestion in suggestions if suggestion.strip()]

        # Ensure suggestions are concise and not incomplete
        cleaned_suggestions = [
            (suggestion[:50].rsplit(' ', 1)[0] + '...') if len(suggestion) > 50 else suggestion
            for suggestion in cleaned_suggestions
        ]

        # Generate more suggestions if there are less than three
        while len(cleaned_suggestions) < 3:
            additional_response = openai.ChatCompletion.create(
                model=self.engine,
                messages=[{"role": "system", "content": base_prompt + "\n\n" + context}],
                max_tokens=150,
                temperature=0.7,
                top_p=1.0,
                n=1
            )
            additional_suggestions = additional_response.choices[0].message['content'].strip().split('\n')
            additional_cleaned_suggestions = [suggestion.lstrip("0123456789. ").strip() for suggestion in additional_suggestions if suggestion.strip()]
            cleaned_suggestions.extend(additional_cleaned_suggestions[:3 - len(cleaned_suggestions)])

        # Ensure exactly three suggestions
        return cleaned_suggestions[:3]

    def generate_response(self, prompt):
        # Add the user's message to the conversation
        self.add_user_message(prompt)

        # Preprocess the user's prompt
        preprocessed_prompt = self.preprocessor.preprocess(prompt)
        sentiment = self.preprocessor.get_sentiment(preprocessed_prompt)

        # Remove the word "please" from the sentiment analysis for more accurate results
        prompt_for_sentiment = preprocessed_prompt.replace("please", "").strip()
        sentiment = self.preprocessor.get_sentiment(prompt_for_sentiment)

        # Print user input, original text, preprocessed text, and sentiment score
        print(f"User Input: {prompt}")
        print(f"Original Text: {prompt}")
        print(f"Preprocessed Text: {preprocessed_prompt}")
        print(f"Sentiment Score: {sentiment}")

        # Handle feedback-related queries only if marked as feedback
        if "feedback:" in prompt.lower():
            feedback_query_response = self.handle_feedback_query(preprocessed_prompt)
            if feedback_query_response:
                self.save_chat_history()  # Save the chat history
                print("Bot:", feedback_query_response)
                return feedback_query_response

        # Check if the user's input matches a specific dish within each menu category
        for cat, items in self.get_menu().items():
            for item in items:
                if item['name'].lower() in preprocessed_prompt:
                    # If the sentiment is positive, treat it as praise
                    if sentiment['compound'] > 0.05:
                        prompt = f"Thank you for the kind words about our {item['name']}!"
                        response = self.generate_gpt_response(prompt, sentiment, context="praise_dish")
                        self.add_system_message(response)
                        self.save_chat_history()  # Save the chat history
                        print("Bot:", response)
                        return response
                    # If the sentiment is negative, treat it as criticism
                    elif sentiment['compound'] < -0.05:
                        prompt = f"We're sorry to hear that you're not satisfied with our {item['name']}. Could you please provide more details?"
                        response = self.generate_gpt_response(prompt, sentiment, context="criticism_dish")
                        self.add_system_message(response)
                        self.save_chat_history()  # Save the chat history
                        print("Bot:", response)
                        return response
                    # Otherwise, treat it as an inquiry and provide the dish description
                    else:
                        prompt = (
                            f"Generate an engaging and appetizing description for the following dish:\n\n"
                            f"Dish Name: {item['name']}\n"
                            f"Description: {item['description']}\n"
                            "Make it sound delicious and appealing to the customer."
                        )
                        response = self.generate_gpt_response(prompt, sentiment, context="dish_description")
                        self.add_system_message(response)
                        self.save_chat_history()  # Save the chat history
                        print("Bot:", response)
                        return response

        # Check if the user's input indicates positive sentiment towards a food item
        if sentiment['compound'] > 0.05 and 'no' not in preprocessed_prompt.lower():
            response = self.generate_gpt_response(prompt, sentiment, context="positive")
            self.add_system_message(response)
            self.save_chat_history()  # Save the chat history
            print("Bot:", response)
            return response

        # Check if the user's input indicates negative sentiment towards a food item
        elif sentiment['compound'] < -0.05:
            response = self.generate_gpt_response(prompt, sentiment, context="negative")
            self.add_system_message(response)
            self.save_chat_history()  # Save the chat history
            print("Bot:", response)
            return response

        # Check if the user's input praises the menu
        menu_praise_keywords = ['love menu', 'great menu', 'awesome menu', 'amazing menu', 'menu is good']
        if any(keyword in preprocessed_prompt for keyword in menu_praise_keywords):
            # Ensure that "like" is part of a valid phrase, not a standalone word
            if 'like ' in preprocessed_prompt or preprocessed_prompt.startswith('like '):
                sentiment_score = sentiment['compound']
                if sentiment_score > 0.05:
                    response = self.get_menu_praise_response()
                    self.add_system_message(response)
                    self.save_chat_history()  # Save the chat history
                    print("Bot:", response)
                    return response

        # Check if the user's input is related to the restaurant name
        restaurant_name_keywords = ['restaurant name', 'name of this place', 'called', 'called this', 'name', 'tell place', 'this place']
        if any(keyword in preprocessed_prompt for keyword in restaurant_name_keywords):
            # Generate a response with the restaurant's name
            response = self.get_restaurant_name_response(sentiment)
            self.add_system_message(response)
            self.save_chat_history()  # Save the chat history
            print("Bot:", response)
            return response

        # Check if the user's input is related to the restaurant profile
        restaurant_profile_keywords = ['restaurant profile', 'about the restaurant', 'more about this place', 'more about this restaurant', 'tell atin-atehan', 'tell restaurant']
        if any(keyword in preprocessed_prompt for keyword in restaurant_profile_keywords):
            response = self.get_restaurant_profile_response(sentiment)
            self.add_system_message(response)
            self.save_chat_history()  # Save the chat history
            print("Bot:", response)
            return response

        # Check if the user's input is related to the menu
        if 'menu' in preprocessed_prompt:
            # If sentiment is neutral, respond with category list
            if -0.05 <= sentiment['compound'] <= 0.05:
                response = self.get_menu_category_response()
                self.add_system_message(response)
                self.save_chat_history()  # Save the chat history
                print("Bot:", response)
                return response

        # Check if the user's input matches a specific category
        for category in self.menu_categories:
            if category.lower() in preprocessed_prompt:
                menu = self.get_menu()
                if category.lower() in menu:
                    # Start with the category name followed by a colon and newline
                    formatted_menu = f"{category.capitalize()}:\n"
                    # Add each menu item on a new line preceded by its index
                    for idx, item in enumerate(menu[category.lower()], start=1):
                        formatted_menu += f"{idx}. {item['name']}\n"
                    response = formatted_menu.strip()  # Remove any trailing newlines
                    self.add_system_message(response)
                    self.last_topic = category.lower()
                    self.save_chat_history()  # Save the chat history
                    print("Bot:", response)
                    return response

        # Check if the user's input is related to recommendations
        recommendation_keywords = ['recommend', 'suggest']
        if any(keyword in preprocessed_prompt for keyword in recommendation_keywords):
            # Sample recommendations
            recommendations = [
                "Our chef's special pasta dish is highly recommended!",
                "If you're a seafood lover, you might enjoy our grilled salmon.",
                "For something light and refreshing, consider trying our seasonal salad.",
                "How about indulging in our decadent chocolate lava cake for dessert?"
            ]
            response = "Sure! Here are some recommendations based on our popular dishes:\n\n" + "\n".join(recommendations)
            self.add_system_message(response)
            self.save_chat_history()  # Save the chat history
            print("Bot:", response)
            return response

        # Check if the user's input is a number after a menu list
        if preprocessed_prompt.isdigit() and self.last_topic:
            selected_index = int(preprocessed_prompt) - 1
            menu_items = self.get_menu().get(self.last_topic, [])
            if 0 <= selected_index < len(menu_items):
                selected_dish = menu_items[selected_index]
                response = self.generate_dish_response(selected_dish)
                self.add_system_message(response)
                self.save_chat_history()  # Save the chat history
                print("Bot:", response)
                return response

        # Check if the user's input is a general positive sentiment
        positive_keywords = ['love', 'great', 'awesome', 'amazing', 'good', 'fantastic', 'delicious']
        if any(keyword in preprocessed_prompt for keyword in positive_keywords):
            response = "Thank you for the kind words! We're glad you're enjoying your experience."
            self.add_system_message(response)
            self.save_chat_history()  # Save the chat history
            print("Bot:", response)
            return response

        # Check if the user's input is a general negative sentiment
        negative_keywords = ['hate', 'bad', 'terrible', 'awful', 'disappointed', 'not good']
        if any(keyword in preprocessed_prompt for keyword in negative_keywords):
            response = "We're sorry to hear that you're not having a great experience. Could you please provide more details so we can address your concerns?"
            self.add_system_message(response)
            self.save_chat_history()  # Save the chat history
            print("Bot:", response)
            return response

        # Default response for other inputs
        default_response = self.generate_gpt_response(prompt, sentiment)
        self.add_system_message(default_response)
        self.save_chat_history()  # Save the chat history
        print("Bot:", default_response)
        return default_response

    def handle_feedback_query(self, preprocessed_prompt):
        # Check if the preprocessed prompt contains feedback keywords
        feedback_keywords = ['feedback', 'rating', 'review']
        if any(keyword in preprocessed_prompt for keyword in feedback_keywords):
            feedback_scores = self.preprocessor.feedback_analysis(preprocessed_prompt)
            feedback_summary = self.preprocessor.summarize_feedback(feedback_scores)
            return feedback_summary
        else:
            return None

    def get_restaurant_name_response(self, sentiment):
        if not self.restaurant_data.empty:
            restaurant_name = self.restaurant_data['Restaurant Name'].iloc[0]
            prompt = f"The name of the restaurant is {restaurant_name}. Provide a friendly and engaging response to a customer who asks for the restaurant's name."
        else:
            prompt = "Our restaurant is Atin-atehan, we're glad to serve you! Provide a friendly and engaging response to a customer who asks for the restaurant's name."

        response = self.generate_gpt_response(prompt, sentiment, context="restaurant_name")
        self.add_system_message(response)
        self.save_chat_history()  # Save the chat history
        print("Bot:", response)
        return response


    def get_restaurant_profile_response(self, sentiment):
        if not self.restaurant_data.empty:
            restaurant_profile = self.restaurant_data['Restaurant Profile'].iloc[0]
            prompt = f"The restaurant profile is: {restaurant_profile}. Provide a friendly and engaging response to a customer who asks for the restaurant's profile."
        else:
            prompt = "Sorry, I couldn't retrieve information about the restaurant profile at the moment. Provide a friendly and apologetic response to a customer who asks for the restaurant's profile."

        response = self.generate_gpt_response(prompt, sentiment, context="restaurant_profile")
        self.add_system_message(response)
        self.save_chat_history()  # Save the chat history
        print("Bot:", response)
        return response

    def get_menu(self):
        menu = {}
        if not self.restaurant_data.empty:
            for dish_type in self.restaurant_data['Dish Type'].unique():
                menu[dish_type.lower()] = []
                group_df = self.restaurant_data[self.restaurant_data['Dish Type'].str.lower() == dish_type.lower()]
                if not group_df.empty:
                    for _, row in group_df.iterrows():
                        # Ensure unique items
                        if row['Dish Name'] not in [item['name'] for item in menu[dish_type.lower()]]:
                            menu[dish_type.lower()].append({
                                'name': row['Dish Name'],
                                'description': row['Description']
                            })
        return menu

    def load_restaurant_data(self):
        file_path = 'Atin-atehan.csv'
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']  # List of encodings to try
        
        for encoding in encodings:
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except UnicodeDecodeError:
                print(f"Failed to read CSV with encoding '{encoding}'. Trying next encoding...")
        
        print("Unable to read CSV file with any of the specified encodings.")
        return pd.DataFrame()  # Return an empty DataFrame if all encodings fail

    def generate_dish_response(self, dish):
        prompt = (
            f"Generate an engaging and appetizing description for the following dish:\n\n"
            f"Dish Name: {dish['name']}\n"
            f"Description: {dish['description']}\n"
            "Make it sound delicious and appealing to the customer."
        )
        response = self.generate_gpt_response(prompt, sentiment={"compound": 0.0}, context="dish_description")
        self.add_system_message(response)
        return response

    def get_menu_praise_response(self):
        prompt = (
            "Generate a friendly and appreciative response to a customer who praised the restaurant's menu. "
            "The response should be engaging and acknowledge their compliment."
        )
        response = self.generate_gpt_response(prompt, sentiment={"compound": 0.0}, context="menu_praise")
        self.add_system_message(response)
        return response

    def get_menu_category_response(self):
        prompt = (
            "Generate a friendly and engaging response that explains the different categories of the menu, "
            "which include Dessert, Drinks, Main Course, Pasta, Salad, and Sides. "
            "Encourage the customer to choose a category they are interested in exploring."
        )
        response = self.generate_gpt_response(prompt, sentiment={"compound": 0.0}, context="menu_categories")
        self.add_system_message(response)
        return response

    def generate_gpt_response(self, prompt, sentiment, context=None):
        messages = [{"role": "system", "content": self.pre_prompt}]
        messages.extend(self.conversation)

        # Add additional context if provided
        if context:
            context_message = f"Context: {context}. Sentiment: {sentiment}"
            messages.append({"role": "system", "content": context_message})

        messages.append({"role": "user", "content": prompt})

        try:
            response = openai.ChatCompletion.create(
                model=self.engine,
                messages=messages
            )
            return response.choices[0].message['content'].strip()
        except openai.error.OpenAIError as e:
            print("Error with OpenAI API:", e)
            return "I'm sorry, but I couldn't process your request at the moment."

    def train_emotion_model(self, dataset_path):
        self.model.train_model(dataset_path)

    def process_feedback(self, feedback):
        analyzer = FeedbackAnalyzer()
        analysis = analyzer.analyze_feedback(feedback)
        return analysis
    
    def analyze_feedback(self, feedback_type, preprocessed_prompt):
        feedback_analysis = self.model.predict_emotion(preprocessed_prompt)
        self.feedback_data.append({
            'type': feedback_type,
            'content': preprocessed_prompt,
            'analysis': feedback_analysis
        })

    def end_chat(self):
        self.save_conversation()
        # Create an instance of FeedbackAnalyzer
        feedback_analyzer = FeedbackAnalyzer(self.feedback)
        # Analyze the feedback
        self.feedback_data = feedback_analyzer.analyze_feedback()

    def save_conversation(self):
        for message in self.conversation:
            if message["role"] == "user":
                self.feedback.append(message["content"])
        self.conversation = []

    def display_feedback_analysis(self):
        if self.feedback_data:
            print("Feedback Analysis Report:")
            print(self.feedback_analyzer.interpret_feedback())
        else:
            print("No feedback to analyze.")

if __name__ == "__main__":
    api_key = input("Enter your OpenAI API key: ")
    bot = EnSysBot("ft:gpt-3.5-turbo-0125:ensys:restaurant-2:9SO7Maw7", api_key)
   
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            bot.end_chat()
            break
        response = bot.generate_response(user_input)
        print("EnSysBot:", response)
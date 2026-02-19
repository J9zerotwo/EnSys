import nltk
import os
nltk.download('stopwords')
nltk.download('punkt_tab')
nltk.download('vader_lexicon')
nltk.download('wordnet')
from flask import Flask
from routes import initialize_routes
from bot import EnSysBot, load_config
import os
from dotenv import load_dotenv

# Load environment variables and get the API key
try:
    api_key = load_config()
    engine = "ft:gpt-3.5-turbo-0125:ensys:empatheticd:9XQSt7AX"
    bot = EnSysBot(engine, api_key)
except Exception as e:
    raise e

# Initialize Flask app
app = Flask(__name__)

# Load secret key from static/key.env
def load_secret_key():
    dotenv_path = os.path.join(os.path.dirname(__file__), 'static', 'key.env')
    load_dotenv(dotenv_path)
    return os.getenv('SECRET_KEY')

# Set the secret key
app.secret_key = load_secret_key()

# Check if the secret key is loaded
if not app.secret_key:
    raise RuntimeError("The session is unavailable because no secret key was set. Set the secret_key on the application to something unique and secret.")

# Initialize routes
initialize_routes(app, bot)

if __name__ == '__main__':
    app.run(debug=True)

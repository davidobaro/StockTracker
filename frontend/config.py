import os
from dotenv import load_dotenv

load_dotenv()

# Use environment variable with fallback to local development
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5001')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
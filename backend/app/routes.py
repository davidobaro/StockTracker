from flask import Blueprint, jsonify, request
import finnhub
import yfinance as yf
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('FINNHUB_API_KEY')
if not API_KEY:
    raise ValueError("Finnhub API key not found. Please set FINNHUB_API_KEY in your .env file.")

print(f"Initializing Finnhub client with API key: {API_KEY[:5]}...{API_KEY[-5:]}")
finnhub_client = finnhub.Client(api_key=API_KEY)

main = Blueprint('main', __name__)

@main.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

@main.route('/api/stock/profile/<ticker>', methods=['GET'])
def get_company_profile(ticker):
    try:
        profile = finnhub_client.company_profile2(symbol=ticker)
        if not profile:
            return jsonify({"error": f"No profile data found for {ticker}"}), 404
        return jsonify(profile)
    except Exception as e:
        if "Invalid API key" in str(e):
            return jsonify({"error": "Invalid Finnhub API key. Please check your API key configuration."}), 401
        return jsonify({"error": str(e)}), 400

@main.route('/api/stock/quote/<ticker>', methods=['GET'])
def get_stock_quote(ticker):
    try:
        print(f"Fetching quote for {ticker}...")
        quote = finnhub_client.quote(ticker)
        print(f"Raw quote response: {quote}")
        
        if not isinstance(quote, dict):
            return jsonify({"error": f"Invalid response type for {ticker}: {type(quote)}"}), 500
            
        if not quote:
            return jsonify({"error": f"Empty quote response for {ticker}"}), 500
            
        # Check if we have valid price data
        current_price = quote.get('c')
        if current_price is None or current_price == 0:
            return jsonify({"error": f"Invalid price data for {ticker}"}), 500
            
        return jsonify(quote)
    except Exception as e:
        print(f"Error fetching quote for {ticker}: {str(e)}")
        if "Invalid API key" in str(e):
            return jsonify({"error": "Invalid Finnhub API key. Please check your API key configuration."}), 401
        return jsonify({"error": str(e)}), 400

@main.route('/api/stock/intraday/<ticker>', methods=['GET'])
def get_intraday_data(ticker):
    try:
        # Get query parameters with defaults
        interval = request.args.get('interval', '1h')  # Default to 1-hour intervals
        days = int(request.args.get('days', '1'))  # Default to 1 day of data
        
        # Validate interval parameter
        valid_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '1h']
        if interval not in valid_intervals:
            return jsonify({"error": f"Invalid interval. Must be one of: {', '.join(valid_intervals)}"}), 400
            
        # Validate days parameter
        if days < 1 or days > 30:
            return jsonify({"error": "Days parameter must be between 1 and 30"}), 400
            
        # Get stock data from Yahoo Finance
        stock = yf.Ticker(ticker)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Convert 1h to 60m for Yahoo Finance API
        interval = '60m' if interval == '1h' else interval
        
        # Fetch intraday data
        df = stock.history(start=start_date, end=end_date, interval=interval)
        
        if df.empty:
            return jsonify({"error": f"No intraday data available for {ticker}"}), 404
            
        # Convert DataFrame to dictionary with ISO format timestamps
        data = {
            'ticker': ticker,
            'interval': interval,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'data': {
                'timestamp': df.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'open': df['Open'].tolist(),
                'high': df['High'].tolist(),
                'low': df['Low'].tolist(),
                'close': df['Close'].tolist(),
                'volume': df['Volume'].tolist()
            }
        }
        
        return jsonify(data)
    except ValueError as ve:
        print(f"Validation error for {ticker}: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching intraday data for {ticker}: {str(e)}")
        if "Symbol may be delisted" in str(e):
            return jsonify({"error": f"Symbol {ticker} may be delisted or invalid"}), 404
        return jsonify({"error": str(e)}), 500

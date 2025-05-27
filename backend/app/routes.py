from flask import Blueprint, jsonify, request
import finnhub
import yfinance as yf
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from data.fetch_data import DataFetcher
from models.lstm_predictor import LSTMPredictor
import pandas as pd

load_dotenv()

def get_market_status():
    """Determine if markets are currently open or closed"""
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()
    
    # Markets are closed on weekends (Saturday=5, Sunday=6)
    if weekday >= 5:
        return "closed_weekend"
    
    # Regular trading hours: 9:30 AM - 4:00 PM ET (assuming ET timezone)
    market_open = datetime.strptime("09:30", "%H:%M").time()
    market_close = datetime.strptime("16:00", "%H:%M").time()
    
    if current_time < market_open:
        return "pre_market"
    elif current_time > market_close:
        return "closed"
    else:
        return "open"

API_KEY = os.getenv('FINNHUB_API_KEY')
if not API_KEY:
    raise ValueError("Finnhub API key not found. Please set FINNHUB_API_KEY in your .env file.")

print(f"Initializing Finnhub client with API key: {API_KEY[:5]}...{API_KEY[-5:]}")
finnhub_client = finnhub.Client(api_key=API_KEY)
fetcher = DataFetcher()
predictor = LSTMPredictor()

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
        valid_intervals = ['1m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo']
        if interval not in valid_intervals:
            return jsonify({"error": f"Invalid interval. Must be one of: {', '.join(valid_intervals)}"}), 400
            
        # Validate days parameter
        if days < 1 or days > 365:
            return jsonify({"error": "Days parameter must be between 1 and 365"}), 400
        
        print(f"DEBUG: Fetching {ticker} data - Interval: {interval}, Days: {days}")
        
        # For daily data or longer intervals, try Finnhub first
        if interval in ['1d', '1wk', '1mo'] or days > 7:
            try:
                # Calculate date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # Convert to Unix timestamps for Finnhub API
                start_timestamp = int(start_date.timestamp())
                end_timestamp = int(end_date.timestamp())
                
                # Use daily resolution for Finnhub
                resolution = 'D' if interval in ['1d', '1wk', '1mo'] else 'D'
                
                print(f"DEBUG: Trying Finnhub with resolution: {resolution}")
                candles = finnhub_client.stock_candles(ticker, resolution, start_timestamp, end_timestamp)
                
                if candles and candles.get('s') == 'ok':
                    # Convert Unix timestamps to readable format
                    timestamps = [datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S') for t in candles['t']]
                    
                    data = {
                        'ticker': ticker,
                        'interval': interval,
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'data': {
                            'timestamp': timestamps,
                            'open': candles['o'],
                            'high': candles['h'],
                            'low': candles['l'],
                            'close': candles['c'],
                            'volume': candles['v']
                        }
                    }
                    
                    print(f"DEBUG: Successfully fetched {len(timestamps)} data points from Finnhub")
                    return jsonify(data)
            except Exception as finnhub_error:
                print(f"DEBUG: Finnhub failed, falling back to Yahoo Finance: {str(finnhub_error)}")
        
        # Fall back to Yahoo Finance for intraday data or if Finnhub fails
        print(f"DEBUG: Using Yahoo Finance for {ticker}")
        stock = yf.Ticker(ticker)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Adjust interval for Yahoo Finance compatibility
        yf_interval = interval
        if interval == '1h':
            yf_interval = '60m'
        
        # For 1-day requests with short intervals, ensure we get recent data
        if days == 1 and interval in ['1m', '5m', '15m', '30m', '1h']:
            # For current day intraday data, use a more recent start time
            start_date = end_date - timedelta(hours=8)  # Last 8 hours of trading
        
        print(f"DEBUG: Yahoo Finance request - Start: {start_date}, End: {end_date}, Interval: {yf_interval}")
        
        # Fetch intraday data
        df = stock.history(start=start_date, end=end_date, interval=yf_interval)
        
        if df.empty:
            # Try with a longer period if no data found
            start_date = end_date - timedelta(days=max(days, 5))
            print(f"DEBUG: Retrying with extended period: {start_date}")
            df = stock.history(start=start_date, end=end_date, interval=yf_interval)
            
        if df.empty:
            return jsonify({"error": f"No intraday data available for {ticker} with {interval} interval"}), 404
            
        # Convert DataFrame to dictionary with ISO format timestamps
        data_info = {
            'ticker': ticker,
            'interval': interval,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'data_source': 'yahoo_finance',
            'last_updated': datetime.now().isoformat(),
            'market_status': get_market_status(),
            'data': {
                'timestamp': df.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'open': df['Open'].tolist(),
                'high': df['High'].tolist(),
                'low': df['Low'].tolist(),
                'close': df['Close'].tolist(),
                'volume': df['Volume'].tolist()
            }
        }
        
        print(f"DEBUG: Successfully fetched {len(df)} data points from Yahoo Finance")
        return jsonify(data_info)
        
    except ValueError as ve:
        print(f"Validation error for {ticker}: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching intraday data for {ticker}: {str(e)}")
        if "Symbol may be delisted" in str(e):
            return jsonify({"error": f"Symbol {ticker} may be delisted or invalid"}), 404
        return jsonify({"error": str(e)}), 500

@main.route('/api/stock/predict/<ticker>', methods=['GET'])
def predict_stock_price(ticker):
    print(f"DEBUG: Prediction endpoint called for ticker: {ticker}")
    try:
        print(f"DEBUG: Starting prediction process for {ticker}")
        # Try Finnhub first
        df = fetcher.fetch_historical_data(ticker, days=5*365)
        print(f"DEBUG: Fetched {len(df) if df is not None else 0} rows from Finnhub")
        
        # If not enough data, try Yahoo Finance
        if df is None or len(df) < predictor.sequence_length:
            print(f"DEBUG: Not enough data from Finnhub, trying Yahoo Finance")
            stock = yf.Ticker(ticker)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5*365)
            ydf = stock.history(start=start_date, end=end_date, interval='1d')
            if not ydf.empty:
                ydf = ydf.rename(columns={
                    'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
                })
                ydf = ydf[['open', 'high', 'low', 'close', 'volume']]
                ydf.index.name = 'timestamp'
                df = ydf
                print(f"DEBUG: Fetched {len(df)} rows from Yahoo Finance")
        
        if df is None or len(df) < predictor.sequence_length:
            error_msg = f'Not enough data for prediction from either Finnhub or Yahoo Finance. Need {predictor.sequence_length} days, got {len(df) if df is not None else 0}'
            print(f"DEBUG: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        print(f"DEBUG: Fetching live quote for {ticker}")
        # Fetch the latest live price and append to df if not already present
        quote = finnhub_client.quote(ticker)
        live_close = quote.get('c')
        if live_close and (df.index[-1].date() < datetime.now().date()):
            print(f"DEBUG: Appending live data: {live_close}")
            # Append a new row for today with the live close
            new_row = pd.DataFrame({
                'open': [quote.get('o', live_close)],
                'high': [quote.get('h', live_close)],
                'low': [quote.get('l', live_close)],
                'close': [live_close],
                'volume': [quote.get('v', 0)]
            }, index=[pd.Timestamp(datetime.now().date())])
            df = pd.concat([df, new_row])
        
        print(f"DEBUG: Training model with {len(df)} data points")
        # Train the model
        predictor.train(df, epochs=10, batch_size=16)
        
        print(f"DEBUG: Making prediction")
        # Predict the next closing price (for the day after the latest date)
        next_price = predictor.predict(df['close'].values)
        last_date = df.index[-1]
        next_date = (last_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        
        result = {'date': next_date, 'predicted_close': float(next_price)}
        print(f"DEBUG: Prediction successful: {result}")
        return jsonify(result)
    except Exception as e:
        error_msg = str(e)
        print(f"DEBUG: Prediction failed with error: {error_msg}")
        return jsonify({'error': error_msg}), 500

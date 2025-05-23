import finnhub
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class DataFetcher:
    def __init__(self):
        self.client = finnhub.Client(api_key=os.getenv('FINNHUB_API_KEY'))
    
    def fetch_historical_data(self, ticker, days=365):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            candles = self.client.stock_candles(
                ticker,
                'D',
                int(start_date.timestamp()),
                int(end_date.timestamp())
            )
            
            if candles['s'] == 'no_data':
                return None
                
            df = pd.DataFrame({
                'timestamp': pd.to_datetime(candles['t'], unit='s'),
                'open': candles['o'],
                'high': candles['h'],
                'low': candles['l'],
                'close': candles['c'],
                'volume': candles['v']
            })
            
            df.set_index('timestamp', inplace=True)
            return df
            
        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            return None
    
    def calculate_technical_indicators(self, df):
        if df is None or len(df) == 0:
            return None
            
        # Calculate moving averages
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA50'] = df['close'].rolling(window=50).mean()
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df

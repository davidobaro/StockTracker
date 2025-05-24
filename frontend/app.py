import streamlit as st
st.set_page_config(page_title="Stock Portfolio Predictor", layout="wide")

import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime
import time

# Backend API URL from Streamlit secrets or default to localhost
BACKEND_URL = st.secrets.get("BACKEND_URL", "https://stocktracker-backend-9n1j.onrender.com")

def get_api_url(endpoint):
    """Helper function to build API URLs"""
    return f"{BACKEND_URL}/api/{endpoint}"

def check_backend_health():
    """Check if backend is accessible"""
    try:
        response = requests.get(get_api_url("health"))
        return response.status_code == 200
    except requests.RequestException:
        return False

# Check backend health
if not check_backend_health():
    st.error(f"⚠️ Could not connect to the backend server at {BACKEND_URL}")
    st.stop()

# Popular stocks with their symbols and categories
POPULAR_STOCKS = {
    "Technology": {
        "Apple": "AAPL",
        "Microsoft": "MSFT",
        "Google": "GOOGL",
        "NVIDIA": "NVDA",
        "Meta": "META"
    },
    "E-commerce": {
        "Amazon": "AMZN",
        "Shopify": "SHOP"
    },
    "Electric Vehicles": {
        "Tesla": "TSLA",
        "Lucid": "LCID"
    },
    "Entertainment": {
        "Netflix": "NFLX",
        "Disney": "DIS"
    },
    "Financial": {
        "Visa": "V",
        "JPMorgan": "JPM"
    }
}

def create_intraday_chart(ticker):
    """Create an intraday price chart using Yahoo Finance data"""
    try:
        # Add time range and interval selectors using session state
        if 'chart_range' not in st.session_state:
            st.session_state.chart_range = '1D'
        
        if 'chart_interval' not in st.session_state:
            st.session_state.chart_interval = '1h'
            
        # Create two columns for range and interval selectors
        range_col, interval_col = st.columns(2)
        
        # Time range selector
        time_range = range_col.selectbox(
            "Time Range",
            ['1D', '5D', '1M', '3M', '6M', '1Y', 'YTD'],
            index=['1D', '5D', '1M', '3M', '6M', '1Y', 'YTD'].index(st.session_state.chart_range),
            key=f"range_{ticker}"
        )
        st.session_state.chart_range = time_range
        
        # Determine available intervals based on selected time range
        interval_options = {
            '1D': ['1m', '5m', '15m', '30m', '1h'],
            '5D': ['5m', '15m', '30m', '1h'],
            '1M': ['30m', '1h', '1d'],
            '3M': ['1h', '1d', '1wk'],
            '6M': ['1d', '1wk'],
            '1Y': ['1d', '1wk', '1mo'],
            'YTD': ['1d', '1wk', '1mo']
        }
        
        # Interval selector with dynamic options
        interval = interval_col.selectbox(
            "Interval",
            interval_options[time_range],
            index=min(len(interval_options[time_range])-1, 
                     interval_options[time_range].index(st.session_state.chart_interval) 
                     if st.session_state.chart_interval in interval_options[time_range] else 0),
            key=f"interval_{ticker}"
        )
        st.session_state.chart_interval = interval
        
        # Calculate days based on time range
        days_mapping = {
            '1D': 1,
            '5D': 5,
            '1M': 30,
            '3M': 90,
            '6M': 180,
            '1Y': 365,
            'YTD': (datetime.now() - datetime(datetime.now().year, 1, 1)).days
        }
        days = days_mapping[time_range]
        
        response = requests.get(
            f"{BACKEND_URL}/api/stock/intraday/{ticker}",
            params={'interval': interval, 'days': days}
        )
        
        if response.status_code == 200:
            data = response.json()['data']  # Access the 'data' key from the enhanced backend response
            
            # Create line chart
            fig = go.Figure()
            
            # Add price line
            fig.add_trace(go.Scatter(
                x=data['timestamp'],
                y=data['close'],
                name='Price',
                line=dict(color='#2962FF', width=2),
                hovertemplate='Price: $%{y:.2f}<br>Time: %{x}<extra></extra>'
            ))
            
            # Add volume bars with subtle coloring
            colors = ['rgba(0, 0, 255, 0.15)' if close >= open else 'rgba(255, 0, 0, 0.15)' 
                     for close, open in zip(data['close'], data['open'])]
            
            fig.add_trace(go.Bar(
                x=data['timestamp'],
                y=data['volume'],
                name='Volume',
                yaxis='y2',
                marker_color=colors,
                opacity=0.3
            ))
            
            # Calculate moving averages
            df = pd.DataFrame({
                'close': data['close'],
                'timestamp': data['timestamp']
            })
            
            ma_periods = [9, 20]
            for period in ma_periods:
                ma = df['close'].rolling(window=period).mean()
                fig.add_trace(go.Scatter(
                    x=data['timestamp'],
                    y=ma,
                    name=f'{period} MA',
                    line=dict(width=1)
                ))
            
            # Update layout with enhanced styling
            fig.update_layout(
                yaxis_title="Price ($)",
                xaxis_title=None,
                height=500,
                yaxis2=dict(
                    title="Volume",
                    overlaying="y",
                    side="right",
                    showgrid=False
                ),
                yaxis=dict(
                    tickformat='$,.2f',
                    gridcolor='rgba(128,128,128,0.2)',
                ),
                xaxis=dict(
                    gridcolor='rgba(128,128,128,0.2)',
                    type='category'
                ),
                plot_bgcolor='white',
                hovermode='x unified',
                margin=dict(l=0, r=0, t=40, b=0),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Add range slider
            fig.update_xaxes(rangeslider_visible=True)
            
            return fig
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to backend server.")
    except Exception as e:
        st.error(f"Error creating intraday chart: {str(e)}")
    return None

# Initialize session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# Sidebar for portfolio management
st.sidebar.title("Portfolio Management")

# Popular Stocks Section
st.sidebar.subheader("Popular Stocks")
for category, stocks in POPULAR_STOCKS.items():
    with st.sidebar.expander(f"📁 {category}"):
        cols = st.columns(2)
        for i, (company, symbol) in enumerate(stocks.items()):
            col = cols[i % 2]
            if col.button(f"{company} ({symbol})", key=f"popular_{symbol}"):
                if symbol not in st.session_state.portfolio:
                    st.sidebar.info(f"Adding {symbol} to portfolio...")
                    try:
                        quote_response = requests.get(f"{BACKEND_URL}/api/stock/quote/{symbol}")
                        quote_data = quote_response.json()
                        
                        if quote_response.status_code == 200 and quote_data.get('c', 0) > 0:
                            st.session_state.portfolio.append(symbol)
                            st.sidebar.success(f"Added {symbol} to portfolio")
                            st.rerun()
                        else:
                            error_msg = quote_data.get('error', 'Unknown error')
                            st.sidebar.error(f"Could not fetch data for {symbol}")
                    except requests.exceptions.ConnectionError:
                        st.sidebar.error("Could not connect to backend server.")
                    except Exception as e:
                        st.sidebar.error(f"Error adding stock: {str(e)}")
                else:
                    st.sidebar.info(f"{symbol} is already in your portfolio")

st.sidebar.markdown("---")

# Custom Stock Input
st.sidebar.subheader("Add Custom Stock")
new_stock = st.sidebar.text_input("Enter Ticker Symbol", "").upper()
if st.sidebar.button("Add") and new_stock:
    # Check if the stock is in any category
    found = False
    for category, stocks in POPULAR_STOCKS.items():
        if new_stock in stocks.keys():  # Check company names
            suggestion = stocks[new_stock]
            st.sidebar.warning(f"Did you mean {suggestion}? Please use the ticker symbol.")
            found = True
            break
        elif new_stock in stocks.values():  # Already a valid symbol
            found = True
            break
    else:
        if new_stock not in st.session_state.portfolio:
            st.sidebar.info(f"Fetching data for {new_stock}...")
            try:
                quote_response = requests.get(f"{BACKEND_URL}/api/stock/quote/{new_stock}")
                quote_data = quote_response.json()
                
                if quote_response.status_code == 200 and quote_data.get('c', 0) > 0:
                    st.session_state.portfolio.append(new_stock)
                    st.sidebar.success(f"Added {new_stock} to portfolio")
                    st.rerun()
                else:
                    error_msg = quote_data.get('error', 'Unknown error')
                    st.sidebar.error(f"Could not fetch data for {new_stock}. Please make sure you're using the correct ticker symbol.")
                    st.sidebar.info("Examples: AAPL (Apple), MSFT (Microsoft), GOOGL (Google)")
            except requests.exceptions.ConnectionError:
                st.sidebar.error("Could not connect to backend server. Make sure it's running on port 5001.")
            except Exception as e:
                st.sidebar.error(f"Error adding stock: {str(e)}")

# Display portfolio
st.sidebar.subheader("Your Portfolio")
for stock in st.session_state.portfolio:
    if st.sidebar.button(f"Remove {stock}"):
        st.session_state.portfolio.remove(stock)
        st.rerun()

# Function to create price range chart
def create_price_range_chart(quote_data):
    """Create a price range chart using available data points"""
    fig = go.Figure()
    
    # Add price range bar
    fig.add_trace(go.Scatter(
        x=['Price Range'],
        y=[quote_data['h']],  # High price
        mode='markers',
        name='High',
        marker=dict(color='green', size=10),
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=['Price Range'],
        y=[quote_data['l']],  # Low price
        mode='markers',
        name='Low',
        marker=dict(color='red', size=10),
        showlegend=True
    ))
    
    # Add current and previous close points
    fig.add_trace(go.Scatter(
        x=['Price Range'],
        y=[quote_data['c']],  # Current price
        mode='markers',
        name='Current',
        marker=dict(color='blue', size=12, symbol='star'),
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=['Price Range'],
        y=[quote_data['pc']],  # Previous close
        mode='markers',
        name='Prev Close',
        marker=dict(color='gray', size=10, symbol='diamond'),
        showlegend=True
    ))
    
    # Add a line connecting high and low
    fig.add_trace(go.Scatter(
        x=['Price Range', 'Price Range'],
        y=[quote_data['l'], quote_data['h']],
        mode='lines',
        line=dict(color='gray', width=2),
        showlegend=False
    ))
    
    # Update layout
    fig.update_layout(
        title=f"Today's Price Range",
        height=300,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(
            title='Price ($)'
        ),
        xaxis=dict(
            showticklabels=False
        ),
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

# Main content
st.title("Stock Portfolio Predictor")

if not st.session_state.portfolio:
    st.info("Add stocks to your portfolio using the sidebar")
else:
    # Display stock data in a grid
    cols = st.columns(3)
    for i, ticker in enumerate(st.session_state.portfolio):
        col = cols[i % 3]
        with col:
            st.subheader(ticker)
            
            # Create a container for each stock card
            with st.container():
                # Fetch company profile
                try:
                    profile_response = requests.get(f"{BACKEND_URL}/api/stock/profile/{ticker}")
                    if profile_response.status_code == 200:
                        profile = profile_response.json()
                        if profile.get('logo'):
                            st.image(profile['logo'], width=50)
                        st.write(f"**Company:** {profile.get('name', 'N/A')}")
                        st.write(f"**Industry:** {profile.get('finnhubIndustry', 'N/A')}")
                    else:
                        st.warning("Could not fetch company profile")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to backend server.")
                
                # Add some spacing
                st.write("")
                
                # Fetch current quote
                try:
                    quote_response = requests.get(f"{BACKEND_URL}/api/stock/quote/{ticker}")
                    if quote_response.status_code == 200:
                        quote = quote_response.json()
                        current_price = quote.get('c')
                        prev_close = quote.get('pc')
                        
                        if isinstance(current_price, (int, float)) and isinstance(prev_close, (int, float)) and prev_close != 0:
                            change = current_price - prev_close
                            change_percent = (change / prev_close) * 100
                            
                            # Display current price
                            st.write(f"**Current Price:** ${current_price:.2f}")
                            
                            # Display change with color
                            if change >= 0:
                                st.markdown(f'<p style="color: green">▲ +${abs(change):.2f} (+{abs(change_percent):.2f}%)</p>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<p style="color: red">▼ -${abs(change):.2f} (-{abs(change_percent):.2f}%)</p>', unsafe_allow_html=True)
                            
                            # Display previous close
                            st.write(f"**Previous Close:** ${prev_close:.2f}")
                            
                            # Add intraday chart
                            fig = create_intraday_chart(ticker)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                            
                            # Add more details in an expander
                            with st.expander("More Details"):
                                st.write(f"**Open:** ${quote['o']:.2f}")
                                st.write(f"**High:** ${quote['h']:.2f}")
                                st.write(f"**Low:** ${quote['l']:.2f}")
                        else:
                            st.warning(f"Current Price: ${current_price if current_price else 'N/A'}")
                    else:
                        error_msg = quote_response.json().get('error', 'Unknown error')
                        st.error(f"Error fetching quote: {error_msg}")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to backend server.")
                except Exception as e:
                    st.error(f"Error displaying quote: {str(e)}")
                
                st.write("---")

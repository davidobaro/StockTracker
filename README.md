# Stock Portfolio Predictor

A modern stock portfolio management and prediction application that combines real-time market data with machine learning predictions. Built with a Flask backend, Streamlit frontend, and powered by Finnhub API.

## Features

- **Portfolio Management**: Add/remove stocks with popular stock categories
- **Real-time Stock Quotes**: Live price data with company profiles and logos
- **Interactive Charts**: Intraday price charts with multiple timeframes (1D-1Y)
- **Technical Analysis**: Moving averages (9-day and 20-day) and volume indicators
- **Smart Date Display**: Automatic detection of trading days vs. weekends/holidays
- **Price Predictions**: LSTM neural network model for next-day price forecasting
- **Company Profiles**: Industry information and company logos
- **Market Context**: Real-time market status and trading hours awareness

## Machine Learning Features

### LSTM Price Prediction Model

- **Architecture**: Long Short-Term Memory (LSTM) neural network
- **Training Data**: 5 years of historical daily price data
- **Sequence Length**: 60-day lookback window for pattern recognition
- **Features**: Multi-layer LSTM with dropout regularization
- **Output**: Next trading day closing price prediction
- **Data Sources**: Hybrid approach using Finnhub and Yahoo Finance APIs

**Note**: Price predictions are currently unavailable due to server memory constraints.

## Setup

1. Clone the repository
2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up your Finnhub API key:
   - Sign up at https://finnhub.io/ to get your API key
   - Copy `.env.example` to `.env`
   - Replace `your_api_key_here` with your actual Finnhub API key

## Running the Application

1. Start the Flask backend:

   ```bash
   cd backend
   flask run
   ```

2. In a new terminal, start the Streamlit frontend:

   ```bash
   cd frontend
   streamlit run app.py
   ```

3. Open your browser and navigate to http://localhost:8501

## Project Structure

```
stock-predictor/
├── backend/           # Flask backend server
│   └── app/
│       ├── __init__.py
│       └── routes.py
├── frontend/         # Streamlit frontend application
│   └── app.py
├── models/          # ML models and prediction logic
│   └── lstm_predictor.py
├── data/           # Data fetching and processing
│   └── fetch_data.py
├── utils/          # Utility functions
├── requirements.txt
└── README.md
```

## Tech Stack 🛠️

- **Backend**: Flask with Flask-CORS
- **Frontend**: Streamlit with interactive charts
- **Data Sources**: Finnhub API, Yahoo Finance (hybrid fallback system)
- **Machine Learning**: TensorFlow/Keras (LSTM neural networks)
- **Data Processing**: Pandas, NumPy, Scikit-learn
- **Visualization**: Plotly (interactive charts with technical indicators)
- **Deployment**: Render (backend), Streamlit Cloud (frontend)
- **Development**: Python 3.12+

## API Architecture 🏗️

### Hybrid Data Fetching

- **Primary**: Finnhub API for daily/weekly/monthly data
- **Fallback**: Yahoo Finance for intraday data and when Finnhub fails
- **Auto-Extension**: Automatically extends time periods when no current data available
- **Market-Aware**: Handles weekends, holidays, and pre/post-market hours

### Endpoints

- `/api/health` - Health check
- `/api/stock/profile/<ticker>` - Company profile and logo
- `/api/stock/quote/<ticker>` - Real-time quote data
- `/api/stock/intraday/<ticker>` - Historical price data with flexible intervals
- `/api/stock/predict/<ticker>` - LSTM price prediction (memory-intensive)

## Deployment & Memory Optimization

### Current Status

- **Frontend**: Deployed on Streamlit Cloud
- **Backend**: Render (free tier with 512MB memory limit)
- **Issue**: LSTM model requires >512MB RAM, causing memory constraints

### Alternative Deployment Options

For the machine learning features to work properly, consider these platforms with higher memory limits:

1. **Railway** (8GB hobby plan, 1GB free tier)
2. **Fly.io** (256MB-8GB configurable)
3. **Google Cloud Run** (up to 8GB, serverless)
4. **DigitalOcean App Platform** (512MB-8GB)
5. **Heroku** (512MB-2.5GB with paid plans)

### Memory Optimization Strategies

- Reduced LSTM model size (25 units vs 50 units per layer)
- TensorFlow memory growth optimization
- Smaller sequence length (30 vs 60 days)
- Lazy model loading (only when prediction requested)

## Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License 📝

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

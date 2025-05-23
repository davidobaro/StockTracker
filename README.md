# Stock Portfolio Predictor 📈

A modern stock portfolio management and prediction application that combines real-time market data with machine learning predictions. Built with a Flask backend, Streamlit frontend, and powered by Finnhub API.

## Features ✨

- Portfolio management (add/remove stocks)
- Real-time stock quotes
- Historical price charts
- Company profiles
- Price predictions using LSTM

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
- **Frontend**: Streamlit
- **Data Sources**: Finnhub API, Yahoo Finance
- **Machine Learning**: TensorFlow (LSTM model)
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly
- **Development**: Python 3.12+

## Contributing 🤝

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License 📝

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

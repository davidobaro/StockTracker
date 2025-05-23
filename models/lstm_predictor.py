import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
import pandas as pd

class LSTMPredictor:
    def __init__(self, sequence_length=60):
        self.sequence_length = sequence_length
        self.model = None
        self.scaler = MinMaxScaler()
        
    def create_sequences(self, data):
        X, y = [], []
        data_len = len(data)
        
        for i in range(self.sequence_length, data_len):
            X.append(data[i-self.sequence_length:i])
            y.append(data[i])
            
        return np.array(X), np.array(y)
    
    def build_model(self, input_shape):
        self.model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        
        self.model.compile(optimizer=Adam(learning_rate=0.001),
                         loss='mse',
                         metrics=['mae'])
        
    def prepare_data(self, df):
        # Extract close prices and convert to numpy array
        close_prices = df['close'].values.reshape(-1, 1)
        
        # Scale the data
        scaled_data = self.scaler.fit_transform(close_prices)
        
        # Create sequences
        X, y = self.create_sequences(scaled_data)
        
        # Split into train and test sets
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        return (X_train, y_train), (X_test, y_test)
    
    def train(self, df, epochs=50, batch_size=32):
        # Prepare data
        (X_train, y_train), (X_test, y_test) = self.prepare_data(df)
        
        # Build model if not already built
        if self.model is None:
            self.build_model((self.sequence_length, 1))
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_test, y_test),
            verbose=1
        )
        
        return history
    
    def predict(self, data):
        # Scale the input data
        scaled_data = self.scaler.transform(data.reshape(-1, 1))
        
        # Create sequence
        X = scaled_data[-self.sequence_length:]
        X = X.reshape(1, self.sequence_length, 1)
        
        # Make prediction
        scaled_prediction = self.model.predict(X)
        
        # Inverse transform the prediction
        prediction = self.scaler.inverse_transform(scaled_prediction)
        
        return prediction[0][0]

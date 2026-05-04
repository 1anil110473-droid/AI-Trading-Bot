import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

def create_model():
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=(10,1)))
    model.add(LSTM(50))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')
    return model

def prepare_data(series):
    X, y = [], []
    for i in range(10, len(series)):
        X.append(series[i-10:i])
        y.append(series[i])
    return np.array(X), np.array(y)

from neuralforecast import NeuralForecast
from neuralforecast.models import RNN
import pandas as pd

def forecast_stock(ticker: str, df: pd.DataFrame) -> dict:
    """
    Predicts the share price for a given ticker symbol by using Nixtla NeuralForecast (RNN model).
    """
    # Step 1: Parse datetimes, keeping timezone info
    df['ds'] = pd.to_datetime(df['ds'], utc=True)

    # Step 2: Remove timezone info, so it's datetime64[ns] (naive)
    df['ds'] = df['ds'].dt.tz_localize(None)    
    df['unique_id'] = df['unique_id'].astype(str)
    df['y'] = df['y'].astype('float64')
    # Further features
    #df['recommendation'] = (df['recommendation'] == 'buy').astype(int)

    feature_columns = [
        'recommendation', 'eps_forward', 'revenue_growth',
        'recommendation_mean', 'gross_margins',
        'dividend_yield', 'debt_to_equity'
    ]

    # Fill NaN values in feature columns with 0.0
    for col in feature_columns:
        if col in df.columns:
            df[col] = df[col].astype('float64').fillna(0.0)

    # Modell
    model = RNN(h=5, input_size=12, max_steps=100)
    nf = NeuralForecast(models=[model], freq='ME')
    nf.fit(df=df)

    # Forecasting
    forecast = nf.predict()

    return forecast
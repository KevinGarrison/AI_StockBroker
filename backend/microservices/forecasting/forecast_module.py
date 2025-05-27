from neuralforecast import NeuralForecast
from neuralforecast.models import RNN
import pandas as pd

def forecast_stock(ticker: str, df: pd.DataFrame) -> dict:
    """
    Predicts the share price for a given ticker symbol by using Nixtla NeuralForecast (RNN model).
    """
    data = df
    df['unique_id'] = ticker

    # Further features
    df['recommendation'] = 1 if data['recommendation_key'] == 'buy' else 0
    df['eps_forward'] = data['eps_forward']
    df['revenue_growth'] = data['revenue_growth']
    df['recommendation_mean'] = data['recommendation_mean']
    df['gross_margins'] = data['gross_margins']
    df['dividend_yield'] = data['dividend_yield']
    df['debt_to_equity'] = data['debt_to_equity']

    feature_columns = [
        'recommendation', 'eps_forward', 'revenue_growth',
        'recommendation_mean', 'gross_margins',
        'dividend_yield', 'debt_to_equity'
    ]

    # Fill NaN values in feature columns with 0.0
    for col in feature_columns:
        if col in df.columns:
            df[col] = df[col].fillna(0.0)

    # Modell
    model = RNN(h=5, input_size=12, max_steps=100)
    nf = NeuralForecast(models=[model], freq='M')
    nf.fit(df=df)

    # Forecasting
    forecast = nf.predict()
    current_price = df['y'].iloc[-1]
    mean_forecast_price = forecast['RNN'].mean()
    price_diff = mean_forecast_price - current_price
    percent_change = (price_diff / current_price) * 100

    recommendation = trading_strategy(percent_change)

    return {
        'ticker': ticker,
        'current_price': float(current_price),
        'forecast_price': float(mean_forecast_price),
        'percent_change': float(percent_change),
        'recommendation': recommendation
    }
 
def trading_strategy(percent_change: float) -> str:
    """
    Returns a trading strategy based on the predicted percentage price change.
 
    Parameters :
        percent_change : The forecast percentage change in the share price
 
    Return :
        A text recommendation for a suitable option strategy.
    """
   
    if percent_change > 5:
        return f"📈 BUY CALL: Expected increase of {percent_change:.2f}% - use possible opportunity!"
    elif percent_change < -5:
        return f"📉 BUY PUT: Expected decrease of {abs(percent_change):. 2f}% - hedge risk!"
    elif -2 <= percent_change <= 2:
        return f"➖ HOLD / SELL COVERED CALL: Movement below 2% - sideways market."
    else:
        return f"🔁 STRADDLE / SPREAD: Movement possible, direction unclear (±{percent_change:.2f}%)"
    

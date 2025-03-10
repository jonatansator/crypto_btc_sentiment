import numpy as np
import pandas as pd
import plotly.graph_objects as go
import ccxt
from datetime import datetime

# Constants
START_DATE = "2024-10-01T00:00:00Z"
END_DATE = "2024-10-12T00:00:00Z"
COLOR_BTC = '#FF9900'
COLOR_BG = 'rgb(40,40,40)'

def fetch_price_data(exchange, ticker='BTC/USDT', timeframe='1h'):
    start_ts = exchange.parse8601(START_DATE)
    ohlcv = exchange.fetch_ohlcv(ticker, timeframe, since=start_ts, limit=1000)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df = df[df['timestamp'] <= pd.to_datetime(END_DATE, utc=True)]
    df.set_index('timestamp', inplace=True)
    return df['close']

def simulate_sentiment(prices):
    # Simulated sentiment: +ve price change = bullish (0 to 1), -ve = bearish (-1 to 0)
    returns = prices.pct_change().fillna(0)
    sentiment = np.tanh(returns * 10)  # Scale and squash to [-1, 1]
    return sentiment

def plot_correlation_heatmap(prices, sentiment, ticker):
    # Rolling correlation over 24-hour windows
    df = pd.DataFrame({'price': prices, 'sentiment': sentiment})
    corr = df['price'].rolling(window=24).corr(df['sentiment']).dropna()
    
    times = corr.index
    corr_values = corr.values
    n_bins = 20
    corr_edges = np.linspace(-1, 1, n_bins + 1)
    heatmap_data, x_edges, _ = np.histogram2d(
        np.arange(len(times)), corr_values, bins=[len(times), n_bins],
        range=[[0, len(times)], [-1, 1]]
    )
    heatmap_data = np.log1p(heatmap_data.T)
    
    x_bins = times
    y_bins = 0.5 * (corr_edges[:-1] + corr_edges[1:])
    
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=heatmap_data,
        x=x_bins,
        y=y_bins,
        colorscale=[[0, COLOR_BG], [0.5, COLOR_BTC], [1, 'white']],
        opacity=0.9,
        showscale=True,
        colorbar=dict(title=dict(text='Log Density', side='right'), tickfont=dict(color='white'))
    ))
    
    fig.update_layout(
        title=dict(text=f'{ticker} Price-Sentiment Correlation', font=dict(color='white'), x=0.5),
        xaxis_title=dict(text='Time', font=dict(color='white')),
        yaxis_title=dict(text='Correlation', font=dict(color='white')),
        plot_bgcolor=COLOR_BG,
        paper_bgcolor=COLOR_BG,
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickangle=45, tickfont=dict(color='white')),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white')),
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    fig.show()

def plot_timeseries(prices, sentiment, ticker):
    times = prices.index
    norm_prices = (prices - prices.min()) / (prices.max() - prices.min())  # Normalize for overlay
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times, y=norm_prices,
        mode='lines',
        line=dict(color=COLOR_BTC, width=2),
        name='Normalized Price'
    ))
    fig.add_trace(go.Scatter(
        x=times, y=sentiment,
        mode='lines',
        line=dict(color='white', width=1),
        name='Sentiment',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title=dict(text=f'{ticker} Price vs Sentiment', font=dict(color='white'), x=0.5),
        xaxis_title=dict(text='Time', font=dict(color='white')),
        yaxis=dict(
            title=dict(text='Price (Norm)', font=dict(color=COLOR_BTC)),
            tickfont=dict(color=COLOR_BTC)
        ),
        yaxis2=dict(
            title=dict(text='Sentiment', font=dict(color='white')),
            tickfont=dict(color='white'),
            overlaying='y',
            side='right'
        ),
        plot_bgcolor=COLOR_BG,
        paper_bgcolor=COLOR_BG,
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickangle=45, tickfont=dict(color='white')),
        margin=dict(l=50, r=50, t=50, b=50),
        legend=dict(font=dict(color='white'))
    )
    
    fig.show()

if __name__ == "__main__":
    exchange = ccxt.binance()
    ticker = 'BTC/USDT'
    
    try:
        prices = fetch_price_data(exchange, ticker)
        print(f"Fetched {len(prices)} price points for {ticker}")
        
        sentiment = simulate_sentiment(prices)
        
        plot_correlation_heatmap(prices, sentiment, ticker)
        plot_timeseries(prices, sentiment, ticker)
        
    except Exception as e:
        print(f"Error: {str(e)}")
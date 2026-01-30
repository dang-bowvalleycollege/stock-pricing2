"""
AI/ML Stock Price Predictor
Uses ensemble of models with technical indicators for 3-day price forecasting
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class StockPredictor:
    """
    ML-based stock price predictor using ensemble methods
    """
    
    def __init__(self):
        self.models = {
            'ridge': Ridge(alpha=1.0),
            'rf': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
            'gbr': GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
        }
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def calculate_technical_indicators(self, df):
        """Calculate technical indicators as features"""
        data = df.copy()
        
        # Price-based features
        data['returns'] = data['close'].pct_change()
        data['log_returns'] = np.log(data['close'] / data['close'].shift(1))
        
        # Moving Averages
        data['sma_5'] = data['close'].rolling(window=5).mean()
        data['sma_10'] = data['close'].rolling(window=10).mean()
        data['sma_20'] = data['close'].rolling(window=20).mean()
        
        # Exponential Moving Averages
        data['ema_5'] = data['close'].ewm(span=5, adjust=False).mean()
        data['ema_10'] = data['close'].ewm(span=10, adjust=False).mean()
        
        # Moving Average Convergence Divergence (MACD)
        ema_12 = data['close'].ewm(span=12, adjust=False).mean()
        ema_26 = data['close'].ewm(span=26, adjust=False).mean()
        data['macd'] = ema_12 - ema_26
        data['macd_signal'] = data['macd'].ewm(span=9, adjust=False).mean()
        
        # Relative Strength Index (RSI)
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        data['bb_middle'] = data['close'].rolling(window=20).mean()
        bb_std = data['close'].rolling(window=20).std()
        data['bb_upper'] = data['bb_middle'] + (bb_std * 2)
        data['bb_lower'] = data['bb_middle'] - (bb_std * 2)
        data['bb_width'] = (data['bb_upper'] - data['bb_lower']) / data['bb_middle']
        
        # Price momentum
        data['momentum_5'] = data['close'] / data['close'].shift(5) - 1
        data['momentum_10'] = data['close'] / data['close'].shift(10) - 1
        
        # Volatility
        data['volatility'] = data['returns'].rolling(window=10).std()
        
        # Price relative to moving averages
        data['price_sma5_ratio'] = data['close'] / data['sma_5']
        data['price_sma20_ratio'] = data['close'] / data['sma_20']
        
        # Volume features (if available)
        if 'volume' in data.columns:
            data['volume_sma'] = data['volume'].rolling(window=10).mean()
            data['volume_ratio'] = data['volume'] / data['volume_sma']
        
        # High-Low range
        if 'high' in data.columns and 'low' in data.columns:
            data['daily_range'] = (data['high'] - data['low']) / data['close']
            data['atr'] = data['daily_range'].rolling(window=14).mean()
        
        return data
    
    def prepare_features(self, df, lookback=5):
        """Prepare features for ML model"""
        data = self.calculate_technical_indicators(df)
        
        # Add lagged features
        for i in range(1, lookback + 1):
            data[f'close_lag_{i}'] = data['close'].shift(i)
            data[f'returns_lag_{i}'] = data['returns'].shift(i)
        
        # Target: next day's close price
        data['target'] = data['close'].shift(-1)
        
        # Drop NaN rows
        data = data.dropna()
        
        # Select feature columns
        feature_cols = [col for col in data.columns if col not in ['target', 'date', 'open', 'high', 'low', 'close', 'volume']]
        
        return data, feature_cols
    
    def train(self, historical_data):
        """Train ensemble models on historical data"""
        # Convert to DataFrame if needed
        if isinstance(historical_data, list):
            df = pd.DataFrame(historical_data)
        else:
            df = historical_data.copy()
        
        if len(df) < 30:
            raise ValueError("Need at least 30 data points for training")
        
        # Prepare features
        data, feature_cols = self.prepare_features(df)
        
        if len(data) < 20:
            raise ValueError("Insufficient data after feature engineering")
        
        X = data[feature_cols].values
        y = data['target'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train each model
        for name, model in self.models.items():
            model.fit(X_scaled, y)
        
        self.feature_cols = feature_cols
        self.is_trained = True
        self.last_data = data
        
        # Calculate training metrics
        predictions = self._ensemble_predict(X_scaled)
        mape = np.mean(np.abs((y - predictions) / y)) * 100
        
        return {
            'trained': True,
            'samples': len(data),
            'features': len(feature_cols),
            'mape': round(mape, 2)
        }
    
    def _ensemble_predict(self, X_scaled):
        """Make predictions using ensemble of models"""
        predictions = []
        weights = {'ridge': 0.2, 'rf': 0.4, 'gbr': 0.4}
        
        for name, model in self.models.items():
            pred = model.predict(X_scaled)
            predictions.append(pred * weights[name])
        
        return np.sum(predictions, axis=0)
    
    def predict_next_days(self, historical_data, days=3):
        """Predict stock prices for the next N days"""
        if isinstance(historical_data, list):
            df = pd.DataFrame(historical_data)
        else:
            df = historical_data.copy()
        
        # Train on the data
        self.train(df)
        
        predictions = []
        current_data = df.copy()
        last_close = float(df['close'].iloc[-1])
        
        for day in range(1, days + 1):
            # Prepare features for prediction
            data, _ = self.prepare_features(current_data)
            
            if len(data) == 0:
                # Fallback: simple trend extrapolation
                trend = (df['close'].iloc[-1] - df['close'].iloc[-5]) / 5
                predicted_price = last_close + (trend * day)
            else:
                # Get last row features
                X = data[self.feature_cols].iloc[-1:].values
                X_scaled = self.scaler.transform(X)
                
                # Ensemble prediction
                predicted_price = float(self._ensemble_predict(X_scaled)[0])
            
            # Calculate confidence based on volatility
            volatility = df['close'].pct_change().std()
            confidence_range = predicted_price * volatility * np.sqrt(day) * 2
            
            prediction_date = datetime.now() + timedelta(days=day)
            
            predictions.append({
                'day': day,
                'date': prediction_date.strftime('%Y-%m-%d'),
                'predicted_price': round(predicted_price, 2),
                'low_estimate': round(predicted_price - confidence_range, 2),
                'high_estimate': round(predicted_price + confidence_range, 2),
                'confidence': round(max(60, 95 - (day * 8)), 1)  # Confidence decreases with time
            })
            
            # Add predicted day to data for next iteration
            new_row = {
                'date': prediction_date.isoformat(),
                'open': predicted_price,
                'high': predicted_price * 1.01,
                'low': predicted_price * 0.99,
                'close': predicted_price,
                'volume': int(df['volume'].mean()) if 'volume' in df.columns else 1000000
            }
            current_data = pd.concat([current_data, pd.DataFrame([new_row])], ignore_index=True)
            last_close = predicted_price
        
        return predictions
    
    def get_analysis(self, historical_data):
        """Get technical analysis summary"""
        if isinstance(historical_data, list):
            df = pd.DataFrame(historical_data)
        else:
            df = historical_data.copy()
        
        data = self.calculate_technical_indicators(df)
        latest = data.iloc[-1]
        
        # Determine trend
        sma_5 = latest.get('sma_5', latest['close'])
        sma_20 = latest.get('sma_20', latest['close'])
        
        if sma_5 > sma_20 * 1.02:
            trend = 'Bullish'
            trend_strength = 'Strong'
        elif sma_5 > sma_20:
            trend = 'Bullish'
            trend_strength = 'Moderate'
        elif sma_5 < sma_20 * 0.98:
            trend = 'Bearish'
            trend_strength = 'Strong'
        elif sma_5 < sma_20:
            trend = 'Bearish'
            trend_strength = 'Moderate'
        else:
            trend = 'Neutral'
            trend_strength = 'Weak'
        
        # RSI analysis
        rsi = latest.get('rsi', 50)
        if rsi > 70:
            rsi_signal = 'Overbought'
        elif rsi < 30:
            rsi_signal = 'Oversold'
        else:
            rsi_signal = 'Neutral'
        
        # MACD analysis
        macd = latest.get('macd', 0)
        macd_signal = latest.get('macd_signal', 0)
        macd_status = 'Bullish' if macd > macd_signal else 'Bearish'
        
        # Volatility
        volatility = data['returns'].std() * np.sqrt(252) * 100  # Annualized
        if volatility > 40:
            vol_level = 'High'
        elif volatility > 20:
            vol_level = 'Moderate'
        else:
            vol_level = 'Low'
        
        return {
            'trend': trend,
            'trend_strength': trend_strength,
            'rsi': round(rsi, 1),
            'rsi_signal': rsi_signal,
            'macd_status': macd_status,
            'volatility': round(volatility, 1),
            'volatility_level': vol_level,
            'support': round(latest.get('bb_lower', latest['close'] * 0.95), 2),
            'resistance': round(latest.get('bb_upper', latest['close'] * 1.05), 2)
        }


# Singleton predictor instance
predictor = StockPredictor()


def predict_stock(historical_data, days=3):
    """Main function to predict stock prices"""
    return predictor.predict_next_days(historical_data, days)


def analyze_stock(historical_data):
    """Main function to get technical analysis"""
    return predictor.get_analysis(historical_data)

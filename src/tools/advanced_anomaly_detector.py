"""Advanced Anomaly Detection with Multiple Indicators"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.models.schemas import StockAnomaly
from src.utils.config import settings
from typing import Optional


class AdvancedAnomalyDetector:
    """
    Production-ready anomaly detector with multiple indicators
    """
    
    def __init__(self):
        self.price_threshold = settings.anomaly_threshold  # 10%
        self.volume_threshold = settings.volume_threshold  # 3x
        
    def calculate_volatility(self, prices: pd.Series) -> float:
        """
        Calculate price volatility (standard deviation)
        Higher volatility = more risky
        """
        return prices.pct_change().std() * 100
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """
        Relative Strength Index (RSI)
        < 30 = Oversold (potential anomaly)
        > 70 = Overbought (potential anomaly)
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not rsi.empty else 50.0
    
    def detect_gap(self, current_price: float, previous_close: float) -> dict:
        """
        Detect price gaps (open significantly different from previous close)
        Gap > 5% = potential anomaly
        """
        gap_percent = ((current_price - previous_close) / previous_close) * 100
        is_gap = abs(gap_percent) >= 5.0
        
        return {
            "has_gap": is_gap,
            "gap_percent": gap_percent,
            "gap_type": "up" if gap_percent > 0 else "down"
        }
    
    def check_for_anomaly(self, ticker: str) -> Optional[StockAnomaly]:
        """
        Multi-factor anomaly detection
        
        Checks:
        1. Price change (> 10%)
        2. Volume spike (> 3x)
        3. High volatility
        4. Extreme RSI
        5. Price gaps
        """
        try:
            print(f"\n📊 Analyzing {ticker}...")
            
            # Fetch data - 5 days for better analysis
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d", interval="5m")
            
            if hist.empty or len(hist) < 20:
                print(f"   ⚠️ Insufficient data")
                return None
            
            # Get latest and baseline data
            latest = hist.iloc[-1]
            baseline = hist.iloc[-20:-1]  # Last 19 intervals for comparison
            
            current_price = float(latest['Close'])
            avg_price = float(baseline['Close'].mean())
            price_change = ((current_price - avg_price) / avg_price) * 100
            
            current_volume = int(latest['Volume'])
            avg_volume = int(baseline['Volume'].mean())
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Calculate indicators
            volatility = self.calculate_volatility(hist['Close'])
            rsi = self.calculate_rsi(hist['Close'])
            gap_info = self.detect_gap(current_price, float(hist.iloc[-2]['Close']))
            
            print(f"   💰 Price: ${current_price:.2f} ({price_change:+.2f}%)")
            print(f"   📈 Volume: {volume_ratio:.2f}x average")
            print(f"   🎲 Volatility: {volatility:.2f}%")
            print(f"   📊 RSI: {rsi:.1f}")
            if gap_info['has_gap']:
                print(f"   ⚡ Gap Detected: {gap_info['gap_percent']:+.2f}% {gap_info['gap_type']}")
            
            # Multi-factor anomaly scoring
            anomaly_score = 0
            reasons = []
            
            # Factor 1: Significant price change
            if abs(price_change) >= self.price_threshold:
                anomaly_score += 3
                reasons.append(f"Large price move: {price_change:+.2f}%")
            
            # Factor 2: Volume spike
            if volume_ratio >= self.volume_threshold:
                anomaly_score += 2
                reasons.append(f"Volume spike: {volume_ratio:.1f}x")
            
            # Factor 3: High volatility
            if volatility > 5.0:
                anomaly_score += 1
                reasons.append(f"High volatility: {volatility:.1f}%")
            
            # Factor 4: Extreme RSI
            if rsi < 30 or rsi > 70:
                anomaly_score += 1
                reasons.append(f"Extreme RSI: {rsi:.1f}")
            
            # Factor 5: Price gap
            if gap_info['has_gap']:
                anomaly_score += 2
                reasons.append(f"Price gap: {gap_info['gap_percent']:+.2f}%")
            
            # Decision: anomaly_score >= 5 = ANOMALY!
            if anomaly_score >= 5:
                print(f"   🚨 ANOMALY DETECTED! (Score: {anomaly_score}/9)")
                print(f"   Reasons: {', '.join(reasons)}")
                
                return StockAnomaly(
                    ticker=ticker,
                    price=current_price,
                    price_change_percent=price_change,
                    volume=current_volume,
                    volume_ratio=volume_ratio
                )
            else:
                print(f"   ✅ Normal (Score: {anomaly_score}/9)")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return None


# Test function
def test_advanced_detector():
    """Test advanced anomaly detection"""
    
    print("\n" + "="*60)
    print("🧪 TESTING ADVANCED ANOMALY DETECTOR")
    print("="*60)
    
    detector = AdvancedAnomalyDetector()
    
    # Test multiple stocks
    watchlist = ["AAPL", "TSLA", "MSFT", "GOOGL"]
    
    for ticker in watchlist:
        anomaly = detector.check_for_anomaly(ticker)
        
        if anomaly:
            print(f"\n⚠️  {anomaly.describe()}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_advanced_detector()

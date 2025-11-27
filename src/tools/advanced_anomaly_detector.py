"""Advanced Anomaly Detection with Multiple Indicators"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.models.schemas import StockAnomaly
from src.utils.config import settings
from src.utils.logger import logger
from typing import Optional


class AdvancedAnomalyDetector:
    """
    Production-ready anomaly detector with multiple indicators
    Works for both CLI and API/Frontend
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
        Gap > 3% = potential anomaly indicator
        """
        gap_percent = ((current_price - previous_close) / previous_close) * 100
        is_gap = abs(gap_percent) >= 3.0
        
        return {
            "has_gap": is_gap,
            "gap_percent": gap_percent,
            "gap_type": "up" if gap_percent > 0 else "down"
        }
    
    def check_for_anomaly(self, ticker: str) -> Optional[StockAnomaly]:
        """
        Multi-factor anomaly detection for CLI monitoring
        
        Checks:
        1. Price change (> 10%)
        2. Volume spike (> 3x)
        3. High volatility
        4. Extreme RSI
        5. Price gaps
        
        Returns StockAnomaly if detected, None otherwise
        """
        try:
            print(f"\n📊 Analyzing {ticker}...")
            
            # Fetch 30 days of data for better analysis
            stock = yf.Ticker(ticker)
            hist = stock.history(period="30d")
            
            if hist.empty or len(hist) < 2:
                print(f"   ⚠️ Insufficient data")
                return None
            
            # Calculate metrics
            current_price = float(hist['Close'].iloc[-1])
            previous_price = float(hist['Close'].iloc[-2])
            price_change_percent = ((current_price - previous_price) / previous_price) * 100
            
            current_volume = int(hist['Volume'].iloc[-1])
            avg_volume = int(hist['Volume'].iloc[:-1].mean())
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            volatility = self.calculate_volatility(hist['Close'])
            rsi = self.calculate_rsi(hist['Close'])
            gap_info = self.detect_gap(
                hist['Open'].iloc[-1], 
                hist['Close'].iloc[-2]
            )
            
            # Print metrics
            print(f"   💰 Price: ${current_price:.2f} ({price_change_percent:+.2f}%)")
            print(f"   📈 Volume: {volume_ratio:.2f}x average")
            print(f"   🎲 Volatility: {volatility:.2f}%")
            print(f"   📊 RSI: {rsi:.1f}")
            
            # Multi-factor anomaly scoring
            anomaly_score = 0
            reasons = []
            
            # Factor 1: Significant price change
            if abs(price_change_percent) >= 10:
                anomaly_score += 3
                reasons.append(f"Large price move: {price_change_percent:+.2f}%")
            elif abs(price_change_percent) >= 5:
                anomaly_score += 2
                reasons.append(f"Moderate price move: {price_change_percent:+.2f}%")
            elif abs(price_change_percent) >= 2:
                anomaly_score += 1
            
            # Factor 2: Volume spike
            if volume_ratio >= 5:
                anomaly_score += 2
                reasons.append(f"High volume spike: {volume_ratio:.1f}x")
            elif volume_ratio >= 3:
                anomaly_score += 1
                reasons.append(f"Volume spike: {volume_ratio:.1f}x")
            
            # Factor 3: High volatility
            if volatility > 2.0:
                anomaly_score += 1
                reasons.append(f"High volatility: {volatility:.1f}%")
            
            # Factor 4: Extreme RSI
            if rsi < 30 or rsi > 70:
                anomaly_score += 1
                reasons.append(f"Extreme RSI: {rsi:.1f}")
            
            # Factor 5: Price gap
            if gap_info['has_gap']:
                anomaly_score += 1
                reasons.append(f"Price gap: {gap_info['gap_percent']:+.2f}%")
            
            # Decision: anomaly_score >= 5 = ANOMALY!
            if anomaly_score >= 5:
                print(f"   🚨 ANOMALY DETECTED! (Score: {anomaly_score}/9)")
                print(f"   Reasons: {', '.join(reasons)}")
                
                return StockAnomaly(
                    ticker=ticker,
                    price=current_price,
                    price_change_percent=price_change_percent,
                    volume=current_volume,
                    volume_ratio=volume_ratio
                )
            else:
                print(f"   ✅ Normal (Score: {anomaly_score}/9)")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            logger.error(f"Error checking anomaly for {ticker}: {e}")
            return None
    
    def analyze_stock_detailed(self, ticker: str) -> Optional[dict]:
        """
        Analyze stock and return detailed metrics as PLAIN DICT
        Used by API endpoint to show all stocks (anomaly or not)
        
        Returns dict with all analysis data or None if data unavailable
        """
        try:
            logger.info(f"\nAnalyzing {ticker}...")
            
            # Get market data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="30d")
            
            if hist.empty or len(hist) < 2:
                logger.warning(f"No data available for {ticker}")
                return None
            
            # Calculate metrics
            current_price = hist['Close'].iloc[-1]
            previous_price = hist['Close'].iloc[-2]
            price_change_percent = ((current_price - previous_price) / previous_price) * 100
            
            current_volume = hist['Volume'].iloc[-1]
            avg_volume = hist['Volume'].iloc[:-1].mean()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            volatility = hist['Close'].pct_change().std() * 100
            
            # RSI
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Calculate anomaly score (same logic as check_for_anomaly)
            score = 0
            if abs(price_change_percent) > 10:
                score += 3
            elif abs(price_change_percent) > 5:
                score += 2
            elif abs(price_change_percent) > 2:
                score += 1
            
            if volume_ratio > 5:
                score += 2
            elif volume_ratio > 3:
                score += 1
            
            if current_rsi < 30 or current_rsi > 70:
                score += 1
            
            if volatility > 2:
                score += 1
            
            gap = abs((hist['Open'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            if gap > 3:
                score += 1
            
            # Determine if anomaly
            is_anomaly = score >= 5
            severity = None
            if is_anomaly:
                severity = "critical" if abs(price_change_percent) > 15 else "high"
            
            # Print to console (for CLI)
            print(f"   💰 Price: ${current_price:.2f} ({price_change_percent:+.2f}%)")
            print(f"   📈 Volume: {volume_ratio:.2f}x average")
            print(f"   🎲 Volatility: {volatility:.2f}%")
            print(f"   📊 RSI: {current_rsi:.1f}")
            
            if is_anomaly:
                print(f"   🚨 ANOMALY DETECTED! (Score: {score}/9)")
            else:
                print(f"   ✅ Normal (Score: {score}/9)")
            
            # Return PLAIN DICT (not Pydantic model to avoid circular import)
            return {
                "ticker": ticker,
                "price": float(current_price),
                "price_change_percent": float(price_change_percent),
                "volume": int(current_volume),
                "volume_ratio": float(volume_ratio),
                "volatility": float(volatility),
                "rsi": float(current_rsi),
                "timestamp": datetime.now().isoformat(),
                "anomaly_score": score,
                "is_anomaly": is_anomaly,
                "severity": severity
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
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
    
    anomalies_found = []
    
    for ticker in watchlist:
        anomaly = detector.check_for_anomaly(ticker)
        
        if anomaly:
            anomalies_found.append(anomaly)
            print(f"\n⚠️  {anomaly.describe()}")
    
    print("\n" + "="*60)
    print(f"Summary: Found {len(anomalies_found)} anomalies out of {len(watchlist)} stocks")
    print("="*60)


if __name__ == "__main__":
    test_advanced_detector()

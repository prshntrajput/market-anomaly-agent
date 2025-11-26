import yfinance as yf
from datetime import datetime, timedelta
from src.models.schemas import StockAnomaly
from src.utils.config import settings
import time

class YFinanceMonitor:
    """yFinance se real-time data (100% FREE!)"""
    
    def __init__(self):
        self.anomaly_threshold = settings.anomaly_threshold
        self.volume_threshold = settings.volume_threshold
    
    def check_for_anomaly(self, ticker: str) -> StockAnomaly | None:
        """
        Real-time anomaly detection using yFinance
        Completely FREE - no API keys needed!
        """
        try:
            print(f"📊 Fetching real-time data for {ticker}...")
            
            # Ticker object banao
            stock = yf.Ticker(ticker)
            
            # Last 2 days ka 5-minute data lo
            hist = stock.history(period="2d", interval="5m")
            
            if hist.empty or len(hist) < 10:
                print(f"   ⚠️ Not enough data for {ticker}")
                return None
            
            # Latest aur previous values
            latest = hist.iloc[-1]
            previous = hist.iloc[-10:-1]  # Last 9 intervals
            
            # Calculations
            current_price = float(latest['Close'])
            avg_price = float(previous['Close'].mean())
            price_change = ((current_price - avg_price) / avg_price) * 100
            
            current_volume = int(latest['Volume'])
            avg_volume = int(previous['Volume'].mean())
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            print(f"   Price: ${current_price:.2f} | Change: {price_change:+.2f}% | Volume: {volume_ratio:.2f}x")
            
            # Anomaly check
            is_significant = abs(price_change) >= self.anomaly_threshold
            is_volume_spike = volume_ratio >= self.volume_threshold
            
            if is_significant and is_volume_spike:
                print(f"   🚨 ANOMALY DETECTED!")
                
                return StockAnomaly(
                    ticker=ticker,
                    price=current_price,
                    price_change_percent=price_change,
                    volume=current_volume,
                    volume_ratio=volume_ratio
                )
            else:
                print(f"   ✅ Normal activity")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return None


# Test function
def test_yfinance_monitor():
    """Test with yFinance"""
    monitor = YFinanceMonitor()
    
    test_tickers = ["AAPL", "TSLA", "MSFT", "GOOGL"]
    
    print("\n" + "="*60)
    print("📊 TESTING WITH YFINANCE (FREE REAL-TIME DATA)")
    print("="*60 + "\n")
    
    for ticker in test_tickers:
        print(f"\n--- {ticker} ---")
        anomaly = monitor.check_for_anomaly(ticker)
        
        if anomaly:
            print(f"\n⚠️  {anomaly.describe()}")
        
        time.sleep(1)  # Rate limiting


if __name__ == "__main__":
    test_yfinance_monitor()

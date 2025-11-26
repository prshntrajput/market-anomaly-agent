from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from src.models.schemas import StockAnomaly
from src.utils.config import settings

class MarketDataMonitor:
    """Historical data se anomaly detect karta hai (FREE tier compatible)"""
    
    def __init__(self):
        self.client = StockHistoricalDataClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_api_secret
        )
        
        self.anomaly_threshold = settings.anomaly_threshold
        self.volume_threshold = settings.volume_threshold
    
    def check_for_anomaly(self, ticker: str) -> StockAnomaly | None:
        """
        Historical bars se anomaly detect karo
        FREE tier: 15+ minutes purana data accessible hai
        """
        try:
            # 2 hours ka data lo (15 min se zyada purana)
            end_date = datetime.now() - timedelta(minutes=20)  # 20 min pehle tak
            start_date = end_date - timedelta(hours=2)  # 2 hours window
            
            print(f"📊 Fetching data for {ticker} from {start_date.strftime('%H:%M')} to {end_date.strftime('%H:%M')}")
            
            # 5-minute bars request karo
            request_params = StockBarsRequest(
                symbol_or_symbols=[ticker],
                start=start_date,
                end=end_date,
                timeframe=TimeFrame.Minute  # 1-minute bars
            )
            
            bars = self.client.get_stock_bars(request_params)
            
            if ticker not in bars or len(bars[ticker]) < 10:
                print(f"⚠️ Not enough data for {ticker}")
                return None
            
            # Latest aur average bars lo
            bar_list = list(bars[ticker])
            latest_bar = bar_list[-1]
            previous_bars = bar_list[-10:-1]  # Last 9 bars for average
            
            # Average price aur volume calculate karo
            avg_price = sum(float(b.close) for b in previous_bars) / len(previous_bars)
            avg_volume = sum(int(b.volume) for b in previous_bars) / len(previous_bars)
            
            # Latest values
            current_price = float(latest_bar.close)
            current_volume = int(latest_bar.volume)
            
            # Price change calculate karo
            price_change = ((current_price - avg_price) / avg_price) * 100
            
            # Volume ratio
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            print(f"   Price: ₹{current_price:.2f} | Change: {price_change:+.2f}% | Volume: {volume_ratio:.2f}x")
            
            # Check anomaly
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
def test_market_monitor():
    """Test with historical data"""
    monitor = MarketDataMonitor()
    
    test_tickers = ["AAPL", "TSLA", "MSFT"]
    
    print("\n" + "="*60)
    print("📊 TESTING WITH ALPACA HISTORICAL DATA (FREE)")
    print("="*60 + "\n")
    
    for ticker in test_tickers:
        print(f"\n--- {ticker} ---")
        anomaly = monitor.check_for_anomaly(ticker)
        
        if anomaly:
            print(f"\n⚠️  {anomaly.describe()}")


if __name__ == "__main__":
    test_market_monitor()

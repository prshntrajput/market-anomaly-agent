import random
from datetime import datetime
from src.models.schemas import StockAnomaly
from src.utils.config import settings

class MockDataGenerator:
    """Mock anomaly data generator for testing"""
    
    def __init__(self):
        self.anomaly_threshold = settings.anomaly_threshold
        
        # Realistic price ranges
        self.stock_prices = {
            "AAPL": 180.0,
            "TSLA": 240.0,
            "MSFT": 380.0,
            "GOOGL": 140.0,
            "AMZN": 175.0,
            "META": 485.0,
            "NVDA": 495.0,
            "NFLX": 645.0
        }
    
    def check_for_anomaly(self, ticker: str, force_anomaly: bool = False) -> StockAnomaly | None:
        """
        Generate mock anomaly data
        
        Args:
            ticker: Stock symbol
            force_anomaly: If True, always generate anomaly (for testing)
        """
        try:
            base_price = self.stock_prices.get(ticker, 100.0)
            
            print(f"📊 Generating mock data for {ticker}...")
            
            if force_anomaly or random.random() < 0.3:  # 30% chance of anomaly
                # Generate anomaly
                price_change = random.uniform(-25.0, -10.0)  # 10-25% drop
                volume_ratio = random.uniform(3.5, 8.0)      # 3.5x-8x spike
                
                current_price = base_price * (1 + price_change/100)
                
                print(f"   🚨 MOCK ANOMALY GENERATED!")
                print(f"   Price: ${current_price:.2f} | Change: {price_change:+.2f}% | Volume: {volume_ratio:.2f}x")
                
                return StockAnomaly(
                    ticker=ticker,
                    price=current_price,
                    price_change_percent=price_change,
                    volume=int(random.uniform(5_000_000, 20_000_000)),
                    volume_ratio=volume_ratio
                )
            else:
                # Normal activity
                price_change = random.uniform(-3.0, 3.0)
                volume_ratio = random.uniform(0.8, 2.0)
                
                print(f"   ✅ Normal activity")
                print(f"   Change: {price_change:+.2f}% | Volume: {volume_ratio:.2f}x")
                
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None


# Test function
def test_mock_generator():
    """Test mock data generation"""
    generator = MockDataGenerator()
    
    test_tickers = ["AAPL", "TSLA", "MSFT", "GOOGL"]
    
    print("\n" + "="*60)
    print("📊 TESTING WITH MOCK DATA GENERATOR")
    print("="*60 + "\n")
    
    print("--- Random Anomalies (30% chance) ---")
    for ticker in test_tickers:
        print(f"\n{ticker}:")
        anomaly = generator.check_for_anomaly(ticker)
        if anomaly:
            print(f"   ⚠️  {anomaly.describe()}")
    
    print("\n\n--- Forced Anomalies (100% chance) ---")
    for ticker in test_tickers:
        print(f"\n{ticker}:")
        anomaly = generator.check_for_anomaly(ticker, force_anomaly=True)
        if anomaly:
            print(f"   ⚠️  {anomaly.describe()}")


if __name__ == "__main__":
    test_mock_generator()

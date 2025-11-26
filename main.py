"""Market Anomaly Detection Agent - Main Entry Point"""

from src.models.schemas import StockAnomaly
from src.chains.query_generator import QueryGenerator
from src.utils.config import settings
import time

def main():
    """Main execution with multiple data source options"""
    
    print("=" * 60)
    print("🚀 MARKET ANOMALY DETECTION AGENT")
    print("=" * 60)
    
    # Choose data source
    print("\nSelect Data Source:")
    print("1. Alpaca Historical (FREE - 15min delay)")
    print("2. yFinance Real-time (FREE - Recommended)")
    print("3. Mock Data (For testing)")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == "1":
        from src.tools.market_data import MarketDataMonitor
        monitor = MarketDataMonitor()
        source_name = "Alpaca Historical"
    elif choice == "2":
        from src.tools.market_data_yfinance import YFinanceMonitor
        monitor = YFinanceMonitor()
        source_name = "yFinance Real-time"
    else:
        from src.tools.mock_data import MockDataGenerator
        monitor = MockDataGenerator()
        source_name = "Mock Data"
    
    print(f"\n✅ Using: {source_name}")
    print(f"\nConfiguration:")
    print(f"  LLM Model: {settings.llm_model}")
    print(f"  Anomaly Threshold: {settings.anomaly_threshold}%")
    print(f"  Volume Threshold: {settings.volume_threshold}x")
    print(f"  Max Retries: {settings.max_retries}")
    print("\n" + "=" * 60 + "\n")
    
    # Initialize query generator
    query_generator = QueryGenerator()
    
    # Stocks to monitor
    watchlist = ["AAPL", "TSLA", "MSFT", "GOOGL"]
    
    print(f"📊 Monitoring {len(watchlist)} stocks: {', '.join(watchlist)}\n")
    
    # Monitoring loop
    for ticker in watchlist:
        print(f"\n{'='*60}")
        print(f"Analyzing: {ticker}")
        print(f"{'='*60}")
        
        # Check for anomaly
        anomaly = monitor.check_for_anomaly(ticker)
        
        if anomaly:
            print(f"\n🚨 ANOMALY DETECTED!")
            print(f"   {anomaly.describe()}\n")
            
            # Generate investigation queries
            print(f"🔍 Generating investigation queries with Gemini...\n")
            
            try:
                queries = query_generator.generate_queries(anomaly, retry_count=0)
                
                print(f"📋 Generated Investigation Queries:")
                for i, query in enumerate(queries, 1):
                    print(f"   {i}. {query}")
                
                print(f"\n✅ Ready for web search (Day 5)!")
                
            except Exception as e:
                print(f"❌ Error generating queries: {e}")
        
        time.sleep(2)  # Rate limiting
    
    print("\n" + "=" * 60)
    print("✅ Monitoring cycle complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Monitoring stopped by user.")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")

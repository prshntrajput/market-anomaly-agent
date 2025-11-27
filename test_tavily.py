"""Test Tavily integration end-to-end"""

from src.tools.tavily_search import TavilySearchTool
from src.models.schemas import StockAnomaly
from src.agents.anomaly_investigation_v3 import create_investigation_graph_v3

def test_end_to_end():
    """Test complete workflow with Tavily"""
    
    print("\n" + "="*60)
    print("🧪 END-TO-END TAVILY INTEGRATION TEST")
    print("="*60)
    
    # Create test anomaly
    anomaly = StockAnomaly(
        ticker="NVDA",
        price=180.19,
        price_change_percent=-15.3,
        volume=80000000,
        volume_ratio=6.5
    )
    
    print(f"\n🚨 Test Anomaly: {anomaly.describe()}")
    
    # Run investigation
    print("\n🔍 Running investigation with real Tavily search...")
    
    app = create_investigation_graph_v3()
    
    result = app.invoke({
        "anomaly": anomaly,
        "search_queries": [],
        "search_results": {},
        "critique": None,
        "iteration": 0,
        "investigation_complete": False
    }, {"recursion_limit": 50})
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)
    print(f"✅ Investigation: {'Success' if result['critique'].explanation_found else 'Needs more data'}")
    print(f"✅ Confidence: {result['critique'].confidence:.0%}")
    print(f"✅ Iterations: {result['iteration'] + 1}")
    print(f"✅ Queries executed: {len(result['search_queries'])}")
    print(f"✅ Search results: {sum(len(r.get('results', [])) for r in result['search_results'].values())}")
    print("="*60)

if __name__ == "__main__":
    test_end_to_end()

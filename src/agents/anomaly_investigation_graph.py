"""Market Anomaly Investigation Graph - Day 2 Implementation"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from src.models.schemas import StockAnomaly
from src.chains.query_generator import QueryGenerator
from src.utils.config import settings


# State for anomaly investigation
class InvestigationState(TypedDict):
    """
    Complete state for anomaly investigation workflow
    """
    # Anomaly data
    anomaly: StockAnomaly | None
    
    # Investigation data
    search_queries: list[str]
    retry_count: int
    
    # Results
    explanation_found: bool
    confidence: float
    
    # Conversation history (for LLM context)
    messages: Annotated[list, add_messages]


# Node 1: Detect anomaly
def detect_anomaly_node(state: InvestigationState) -> dict:
    """
    Node 1: Check if input has a valid anomaly
    """
    anomaly = state.get("anomaly")
    
    if anomaly:
        print(f"🚨 Anomaly detected: {anomaly.describe()}")
        return {
            "explanation_found": False,
            "confidence": 0.0,
            "retry_count": 0
        }
    else:
        print("✅ No anomaly to investigate")
        return {
            "explanation_found": True,  # Skip investigation
            "confidence": 1.0
        }


# Node 2: Generate queries
def generate_queries_node(state: InvestigationState) -> dict:
    """
    Node 2: Generate search queries based on anomaly
    """
    anomaly = state["anomaly"]
    retry_count = state["retry_count"]
    
    print(f"\n🔍 Generating queries (Attempt {retry_count + 1}/{settings.max_retries})...")
    
    # Use query generator from Day 1!
    generator = QueryGenerator()
    queries = generator.generate_queries(anomaly, retry_count)
    
    print(f"📋 Generated {len(queries)} queries:")
    for i, query in enumerate(queries, 1):
        print(f"   {i}. {query}")
    
    return {"search_queries": queries}


# Node 3: Mock search (Day 5 mein real search karenge)
def mock_search_node(state: InvestigationState) -> dict:
    """
    Node 3: Mock search results (placeholder for Day 5)
    """
    queries = state["search_queries"]
    retry_count = state["retry_count"]
    
    print(f"\n🌐 Executing mock search for {len(queries)} queries...")
    
    # Mock: First attempt always fails, second succeeds
    if retry_count == 0:
        print("   ❌ No convincing explanation found (mock)")
        return {
            "explanation_found": False,
            "confidence": 0.3
        }
    else:
        print("   ✅ Convincing explanation found! (mock)")
        return {
            "explanation_found": True,
            "confidence": 0.9
        }


# Node 4: Increment retry
def increment_retry_node(state: InvestigationState) -> dict:
    """
    Node 4: Increment retry counter
    """
    new_count = state["retry_count"] + 1
    print(f"\n🔄 Retrying... (Attempt {new_count + 1}/{settings.max_retries})")
    return {"retry_count": new_count}


# Node 5: Final report
def final_report_node(state: InvestigationState) -> dict:
    """
    Node 5: Generate final investigation report
    """
    anomaly = state["anomaly"]
    explanation_found = state["explanation_found"]
    confidence = state["confidence"]
    retry_count = state["retry_count"]
    
    print(f"\n📊 FINAL INVESTIGATION REPORT")
    print(f"   Anomaly: {anomaly.describe() if anomaly else 'None'}")
    print(f"   Explanation Found: {explanation_found}")
    print(f"   Confidence: {confidence:.2%}")
    print(f"   Retries Used: {retry_count}")
    
    return {}


# Conditional edge function
def should_retry(state: InvestigationState) -> Literal["retry", "report"]:
    """
    Decision: Should we retry or generate final report?
    """
    explanation_found = state["explanation_found"]
    retry_count = state["retry_count"]
    max_retries = settings.max_retries
    
    # If explanation found OR max retries reached -> report
    if explanation_found or retry_count >= max_retries:
        return "report"
    else:
        return "retry"


# Create graph
def create_investigation_graph():
    """
    Complete anomaly investigation graph with self-correction loop
    """
    workflow = StateGraph(InvestigationState)
    
    # Add all nodes
    workflow.add_node("detect", detect_anomaly_node)
    workflow.add_node("generate_queries", generate_queries_node)
    workflow.add_node("search", mock_search_node)
    workflow.add_node("increment_retry", increment_retry_node)
    workflow.add_node("report", final_report_node)
    
    # Add edges
    workflow.add_edge(START, "detect")
    workflow.add_edge("detect", "generate_queries")
    workflow.add_edge("generate_queries", "search")
    
    # Conditional edge - THE SELF-CORRECTION LOOP!
    workflow.add_conditional_edges(
        "search",
        should_retry,
        {
            "retry": "increment_retry",    # Loop back
            "report": "report"              # End investigation
        }
    )
    
    # Complete the loop
    workflow.add_edge("increment_retry", "generate_queries")
    workflow.add_edge("report", END)
    
    return workflow.compile()


# Test function
def test_investigation_graph():
    """Test the complete investigation workflow"""
    
    print("\n" + "="*60)
    print("🧪 TESTING ANOMALY INVESTIGATION GRAPH")
    print("="*60 + "\n")
    
    app = create_investigation_graph()
    
    # Create test anomaly
    from src.models.schemas import StockAnomaly
    
    test_anomaly = StockAnomaly(
        ticker="WIPRO",
        price=385.50,
        price_change_percent=-14.2,
        volume=8500000,
        volume_ratio=4.5
    )
    
    # Run investigation
    initial_state = {
        "anomaly": test_anomaly,
        "search_queries": [],
        "retry_count": 0,
        "explanation_found": False,
        "confidence": 0.0,
        "messages": []
    }
    
    result = app.invoke(initial_state)
    
    print("\n" + "="*60)
    print("✅ Investigation Complete!")
    print("="*60)


if __name__ == "__main__":
    test_investigation_graph()

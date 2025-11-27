"""LangGraph with conditional edges - Price checker"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END

# State
class PriceCheckState(TypedDict):
    """State for price anomaly check"""
    ticker: str
    price_change: float
    is_anomaly: bool
    action: str


# Nodes
def check_price_change(state: PriceCheckState) -> dict:
    """Node 1: Check if price change is significant"""
    ticker = state["ticker"]
    price_change = state["price_change"]
    
    # Anomaly = price drop > 10%
    is_anomaly = abs(price_change) >= 10.0
    
    print(f"📊 Checking {ticker}...")
    print(f"   Price Change: {price_change:+.2f}%")
    print(f"   Is Anomaly: {is_anomaly}")
    
    return {"is_anomaly": is_anomaly}


def handle_normal(state: PriceCheckState) -> dict:
    """Node 2a: Handle normal price movement"""
    action = f"✅ {state['ticker']} is operating normally. No action needed."
    print(f"\n{action}")
    return {"action": action}


def handle_anomaly(state: PriceCheckState) -> dict:
    """Node 2b: Handle price anomaly"""
    action = f"🚨 {state['ticker']} anomaly detected! Starting investigation..."
    print(f"\n{action}")
    return {"action": action}


# Conditional edge function
def decide_action(state: PriceCheckState) -> Literal["normal", "anomaly"]:
    """
    Conditional edge: Decide which node to go to next
    
    Returns:
        "normal" if no anomaly
        "anomaly" if anomaly detected
    """
    if state["is_anomaly"]:
        return "anomaly"
    else:
        return "normal"


# Create graph
def create_price_checker_graph():
    """Price checker with conditional edges"""
    
    workflow = StateGraph(PriceCheckState)
    
    # Add nodes
    workflow.add_node("check", check_price_change)
    workflow.add_node("normal", handle_normal)
    workflow.add_node("anomaly", handle_anomaly)
    
    # Add edges
    workflow.add_edge(START, "check")
    
    # Conditional edge - ye decision lega
    workflow.add_conditional_edges(
        "check",              # Source node
        decide_action,        # Decision function
        {
            "normal": "normal",   # If returns "normal" -> go to "normal" node
            "anomaly": "anomaly"  # If returns "anomaly" -> go to "anomaly" node
        }
    )
    
    # Both end at END
    workflow.add_edge("normal", END)
    workflow.add_edge("anomaly", END)
    
    return workflow.compile()


# Test function
def test_conditional_graph():
    """Test with different scenarios"""
    
    print("\n" + "="*60)
    print("🧪 TESTING CONDITIONAL EDGES")
    print("="*60 + "\n")
    
    app = create_price_checker_graph()
    
    # Test Case 1: Normal movement
    print("--- Test Case 1: Normal Movement ---")
    result1 = app.invoke({
        "ticker": "AAPL",
        "price_change": -3.5,
        "is_anomaly": False,
        "action": ""
    })
    print(f"Action: {result1['action']}")
    
    # Test Case 2: Anomaly
    print("\n--- Test Case 2: Anomaly Detected ---")
    result2 = app.invoke({
        "ticker": "TSLA",
        "price_change": -15.2,
        "is_anomaly": False,
        "action": ""
    })
    print(f"Action: {result2['action']}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_conditional_graph()

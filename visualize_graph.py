"""Visualize LangGraph"""

from src.agents.anomaly_investigation_v2 import create_investigation_graph_v2

def visualize():
    """Generate graph visualization"""
    app = create_investigation_graph_v2()
    
    # Get ASCII representation
    print("\n" + "="*60)
    print("📊 GRAPH STRUCTURE")
    print("="*60)
    print(app.get_graph().draw_ascii())
    print("="*60)


if __name__ == "__main__":
    visualize()

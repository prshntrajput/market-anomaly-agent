"""Production-ready market monitoring system - FIXED"""

from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, START, END
from src.tools.advanced_anomaly_detector import AdvancedAnomalyDetector
from src.agents.anomaly_investigation_v2 import (
    create_investigation_graph_v2,
    InvestigationState
)
from src.models.schemas import StockAnomaly
from src.utils.logger import logger
from src.utils.config import settings
import time


# State for production monitoring
class MonitoringState(TypedDict):
    """State for production monitoring loop"""
    watchlist: list[str]
    current_ticker: str
    current_index: int
    anomaly_detected: StockAnomaly | None
    should_continue: bool


# Node 1: Fetch next ticker
def fetch_next_ticker_node(state: MonitoringState) -> dict:
    """Get next ticker to monitor"""
    watchlist = state["watchlist"]
    current_index = state["current_index"]
    
    # Check if we've completed the watchlist
    if current_index >= len(watchlist):
        logger.info("✅ Completed monitoring cycle")
        return {
            "should_continue": False,
            "current_ticker": ""
        }
    
    ticker = watchlist[current_index]
    logger.info(f"Monitoring {ticker} ({current_index + 1}/{len(watchlist)})")
    
    return {
        "current_ticker": ticker,
        "should_continue": True
    }


# Node 2: Detect anomaly
def detect_anomaly_node(state: MonitoringState) -> dict:
    """Detect anomaly in current ticker"""
    ticker = state["current_ticker"]
    
    detector = AdvancedAnomalyDetector()
    anomaly = detector.check_for_anomaly(ticker)
    
    if anomaly:
        logger.warning(f"🚨 ANOMALY: {anomaly.describe()}")
    else:
        logger.info(f"✅ {ticker} normal")
    
    # Increment index for next iteration
    return {
        "anomaly_detected": anomaly,
        "current_index": state["current_index"] + 1
    }


# Node 3: Investigate anomaly
def investigate_anomaly_node(state: MonitoringState) -> dict:
    """Trigger investigation workflow"""
    anomaly = state["anomaly_detected"]
    
    logger.info(f"🔍 Starting investigation for {anomaly.ticker}")
    
    # Create investigation graph
    investigation_app = create_investigation_graph_v2()
    
    # Initial investigation state
    investigation_state: InvestigationState = {
        "anomaly": anomaly,
        "search_queries": [],
        "search_results": "",
        "critique": None,
        "iteration": 0,
        "investigation_complete": False
    }
    
    try:
        # Run investigation with higher recursion limit
        result = investigation_app.invoke(
            investigation_state,
            {"recursion_limit": 50}  # Increase limit for investigation
        )
        
        logger.info(f"✅ Investigation complete for {anomaly.ticker}")
        logger.info(f"   Confidence: {result['critique'].confidence:.0%}")
        logger.info(f"   Iterations: {result['iteration'] + 1}")
    except Exception as e:
        logger.error(f"Investigation failed: {e}")
    
    return {}


# Conditional edge 1: Should we investigate?
def should_investigate(state: MonitoringState) -> Literal["investigate", "next"]:
    """Decide if investigation is needed"""
    if state["anomaly_detected"]:
        return "investigate"
    else:
        return "next"


# Conditional edge 2: Should monitoring continue?
def should_continue_monitoring(state: MonitoringState) -> Literal["continue", "end"]:
    """Check if we should continue monitoring"""
    if state["should_continue"]:
        return "continue"
    else:
        return "end"


# Create monitoring graph
def create_production_monitor():
    """Production monitoring graph - FIXED VERSION"""
    
    workflow = StateGraph(MonitoringState)
    
    # Add nodes
    workflow.add_node("fetch_next", fetch_next_ticker_node)
    workflow.add_node("detect", detect_anomaly_node)
    workflow.add_node("investigate", investigate_anomaly_node)
    
    # Add edges
    workflow.add_edge(START, "fetch_next")
    
    # From fetch_next, check if we should continue
    workflow.add_conditional_edges(
        "fetch_next",
        should_continue_monitoring,
        {
            "continue": "detect",  # Continue to detection
            "end": END             # Stop monitoring
        }
    )
    
    # From detect, decide: investigate or next ticker?
    workflow.add_conditional_edges(
        "detect",
        should_investigate,
        {
            "investigate": "investigate",  # Go to investigation
            "next": "fetch_next"           # Go to next ticker
        }
    )
    
    # After investigation, go to next ticker
    workflow.add_edge("investigate", "fetch_next")
    
    return workflow.compile()


# Main execution function
def run_production_monitor(watchlist: list[str], continuous: bool = False):
    """
    Run production monitoring - FIXED
    """
    
    logger.info("="*60)
    logger.info("🚀 PRODUCTION MARKET MONITORING STARTED")
    logger.info("="*60)
    logger.info(f"Watchlist: {', '.join(watchlist)}")
    logger.info(f"Anomaly Threshold: {settings.anomaly_threshold}%")
    logger.info(f"Volume Threshold: {settings.volume_threshold}x")
    logger.info(f"Continuous Mode: {continuous}")
    logger.info("="*60)
    
    app = create_production_monitor()
    
    try:
        if continuous:
            # Continuous monitoring loop
            cycle = 1
            while True:
                logger.info(f"\n{'='*60}")
                logger.info(f"📊 MONITORING CYCLE {cycle}")
                logger.info(f"{'='*60}")
                
                initial_state = {
                    "watchlist": watchlist,
                    "current_ticker": "",
                    "current_index": 0,
                    "anomaly_detected": None,
                    "should_continue": True
                }
                
                # Invoke with higher recursion limit
                app.invoke(initial_state, {"recursion_limit": 100})
                
                cycle += 1
                sleep_time = 300  # 5 minutes
                logger.info(f"\n⏰ Sleeping for {sleep_time}s before next cycle...")
                time.sleep(sleep_time)
        else:
            # Single cycle
            initial_state = {
                "watchlist": watchlist,
                "current_ticker": "",
                "current_index": 0,
                "anomaly_detected": None,
                "should_continue": True
            }
            
            # Invoke with higher recursion limit
            app.invoke(initial_state, {"recursion_limit": 100})
            
            logger.info("\n" + "="*60)
            logger.info("✅ MONITORING CYCLE COMPLETE")
            logger.info("="*60)
    
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Monitoring stopped by user")
    except Exception as e:
        logger.error(f"❌ Error in monitoring: {e}", exc_info=True)


# Test function
def test_production_monitor():
    """Test production monitoring system"""
    
    watchlist = ["AAPL", "TSLA", "MSFT", "GOOGL"]
    
    # Run single cycle
    run_production_monitor(watchlist, continuous=False)


if __name__ == "__main__":
    test_production_monitor()

"""Market Anomaly Detection Agent - Production Version"""

import argparse
from src.agents.production_monitor import run_production_monitor
from src.utils.logger import logger
from src.utils.config import settings


def main():
    """Main entry point with CLI arguments"""
    
    parser = argparse.ArgumentParser(
        description="Market Anomaly Detection Agent with AI Investigation"
    )
    
    parser.add_argument(
        "--watchlist",
        nargs="+",
        default=["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "META"],
        help="List of stock tickers to monitor"
    )
    
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run in continuous monitoring mode (infinite loop)"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Interval between cycles in seconds (default: 300)"
    )
    
    args = parser.parse_args()
    
    logger.info("Market Anomaly Detection Agent - Production v1.0")
    logger.info(f"Configuration: {settings.llm_model}")
    
    # Run monitoring
    run_production_monitor(
        watchlist=args.watchlist,
        continuous=args.continuous
    )


if __name__ == "__main__":
    main()

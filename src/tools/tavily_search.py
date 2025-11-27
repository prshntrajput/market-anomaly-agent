"""Tavily Search Tool for Market Anomaly Investigation"""

from tavily import TavilyClient
from typing import List, Dict, Optional
from src.utils.config import settings
from src.utils.logger import logger
import os


class TavilySearchTool:
    """
    Production-ready Tavily search tool
    
    Features:
    - AI-optimized web search
    - Financial domain prioritization
    - Source credibility filtering
    - Automatic content extraction
    """
    
    def __init__(self):
        """Initialize Tavily client"""
        self.client = TavilyClient(api_key=settings.tavily_api_key)
        
        # Trusted financial domains
        self.financial_domains = [
            "sec.gov",
            "reuters.com",
            "bloomberg.com",
            "finance.yahoo.com",
            "seekingalpha.com",
            "marketwatch.com",
            "fool.com",
            "cnbc.com",
            "wsj.com",
            "ft.com"
        ]
    
    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_answer: bool = True,
        include_domains: Optional[List[str]] = None,
        days: Optional[int] = 7
    ) -> Dict:
        """
        Execute Tavily search with financial optimization
        
        Args:
            query: Search query
            max_results: Max number of results (default: 5)
            search_depth: "basic" or "advanced" (default: advanced)
            include_answer: Include AI-synthesized answer (default: True)
            include_domains: Specific domains to search
            days: Limit to last N days (default: 7)
        
        Returns:
            Dict with 'answer', 'results', and 'query' keys
        """
        try:
            logger.info(f"🔍 Searching: {query}")
            logger.debug(f"   Depth: {search_depth}, Max Results: {max_results}")
            
            # Use financial domains by default
            domains = include_domains or self.financial_domains
            
            # Execute search
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=include_answer,
                include_domains=domains,
                days=days,
                topic="news"  # Focus on news/current events
            )
            
            # Log results
            logger.info(f"   ✅ Found {len(response.get('results', []))} results")
            if include_answer and response.get('answer'):
                logger.debug(f"   AI Answer: {response['answer'][:100]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"   ❌ Search failed: {e}")
            return {
                "answer": "",
                "results": [],
                "query": query
            }
    
    def search_multiple_queries(
        self,
        queries: List[str],
        max_results_per_query: int = 3
    ) -> Dict[str, Dict]:
        """
        Execute multiple searches and combine results
        
        Args:
            queries: List of search queries
            max_results_per_query: Results per query
        
        Returns:
            Dict mapping query -> search results
        """
        all_results = {}
        
        for query in queries:
            result = self.search(
                query=query,
                max_results=max_results_per_query,
                search_depth="advanced",
                include_answer=True
            )
            all_results[query] = result
        
        return all_results
    
    def extract_key_insights(self, search_results: Dict) -> List[str]:
        """
        Extract key insights from search results
        
        Args:
            search_results: Tavily search response
        
        Returns:
            List of key insights/facts
        """
        insights = []
        
        # Add AI answer if available
        if search_results.get('answer'):
            insights.append(f"📌 {search_results['answer']}")
        
        # Extract from top results
        for result in search_results.get('results', [])[:3]:
            title = result.get('title', '')
            content = result.get('content', '')
            url = result.get('url', '')
            
            if content:
                insight = f"• {title}: {content[:150]}... [Source: {url}]"
                insights.append(insight)
        
        return insights


# Test function
def test_tavily_search():
    """Test Tavily search functionality"""
    
    print("\n" + "="*60)
    print("🧪 TESTING TAVILY SEARCH")
    print("="*60)
    
    search_tool = TavilySearchTool()
    
    # Test Case 1: Single query
    print("\n--- Test 1: Single Search ---")
    query = "Apple stock drop November 2025 earnings"
    result = search_tool.search(query, max_results=3)
    
    print(f"Query: {query}")
    print(f"\n🤖 AI Answer:")
    print(f"   {result.get('answer', 'No answer')}")
    
    print(f"\n📰 Top Results:")
    for i, res in enumerate(result.get('results', []), 1):
        print(f"   {i}. {res['title']}")
        print(f"      {res['url']}")
    
    # Test Case 2: Multiple queries
    print("\n--- Test 2: Multiple Searches ---")
    queries = [
        "Tesla stock price drop November 2025",
        "Tesla earnings Q3 2025 miss",
        "Tesla SEC filing recent"
    ]
    
    multi_results = search_tool.search_multiple_queries(queries, max_results_per_query=2)
    
    for query, result in multi_results.items():
        print(f"\n📋 {query}")
        print(f"   Results: {len(result.get('results', []))}")
        if result.get('answer'):
            print(f"   Answer: {result['answer'][:80]}...")
    
    # Test Case 3: Extract insights
    print("\n--- Test 3: Key Insights ---")
    insights = search_tool.extract_key_insights(result)
    for insight in insights:
        print(f"   {insight[:150]}...")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_tavily_search()

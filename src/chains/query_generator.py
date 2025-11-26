from langchain_google_genai import ChatGoogleGenerativeAI  # Gemini!
from langchain_core.prompts import PromptTemplate
from src.utils.config import settings
from src.models.schemas import StockAnomaly
from typing import List

class QueryGenerator:
    """Anomaly ke liye search queries generate karta hai using Gemini"""
    
    def __init__(self):
        # Gemini LLM setup
        self.llm = ChatGoogleGenerativeAI(
            model=getattr(settings, "llm_model", "gemini-2.5-flash"),
            temperature=settings.llm_temperature,
            google_api_key=settings.google_api_key,
            convert_system_message_to_human=True  # Gemini ke liye zaroori
        )
        
        self.template = PromptTemplate(
            input_variables=["ticker", "change_percent", "volume_ratio", "retry_count"],
            template="""
You are a financial analyst investigating a market anomaly.

🚨 ANOMALY DETECTED:
Stock: {ticker}
Price Change: {change_percent}%
Volume Spike: {volume_ratio}x normal

TASK: Generate 3 highly specific search queries to find WHY this happened.

RETRY COUNT: {retry_count}
- If retry=0: Generate broad queries (e.g., "{ticker} news today")
- If retry=1: Get more specific (e.g., "{ticker} Q3 earnings miss")
- If retry=2+: Get hyper-specific (e.g., "{ticker} SEC 8-K filing November 2025")

FOCUS AREAS:
1. Earnings reports (miss/beat expectations)
2. SEC filings (8-K, 10-Q, 10-K)
3. Analyst downgrades/upgrades
4. Management changes (CEO resignation, etc.)
5. Legal issues or investigations
6. Major client contracts (won/lost)

FORMAT: Return ONLY a numbered list of 3 queries, no explanations.

Example output:
1. RELIANCE Q3 2025 earnings report miss
2. RELIANCE Jio subscriber loss analyst downgrade
3. RELIANCE petrochemical plant fire incident November 2025
"""
        )
    
    def generate_queries(self, anomaly: StockAnomaly, retry_count: int = 0) -> List[str]:
        """Queries generate karo using Gemini"""
        
        prompt = self.template.format(
            ticker=anomaly.ticker,
            change_percent=anomaly.price_change_percent,
            volume_ratio=anomaly.volume_ratio,
            retry_count=retry_count
        )
        
        # Gemini se response
        response = self.llm.invoke(prompt)
        
        # Parse queries
        queries = []
        for line in response.content.strip().split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                query = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                if query:
                    queries.append(query)
        
        return queries[:3]


# Test function
def test_query_generator():
    """Test with Gemini"""
    generator = QueryGenerator()
    
    anomaly = StockAnomaly(
        ticker="WIPRO",
        price=385.50,
        price_change_percent=-14.2,
        volume=8500000,
        volume_ratio=4.5
    )
    
    print(f"\n🚀 Testing Query Generator with Gemini")
    print(f"Anomaly: {anomaly.describe()}\n")
    
    for retry in range(2):
        print(f"\n--- Retry {retry} ---")
        queries = generator.generate_queries(anomaly, retry_count=retry)
        for i, query in enumerate(queries, 1):
            print(f"{i}. {query}")


if __name__ == "__main__":
    test_query_generator()

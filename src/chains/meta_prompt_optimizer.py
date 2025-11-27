"""Meta-prompting: Let LLM optimize its own prompts"""

from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.config import settings
from src.models.schemas import StockAnomaly


class MetaPromptOptimizer:
    """
    Meta-prompting: LLM analyzes and improves queries
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.google_api_key,
            temperature=0.4,
            convert_system_message_to_human=True
        )
    
    def optimize_queries(
        self,
        original_queries: list[str],
        anomaly: StockAnomaly,
        search_failed: bool = False
    ) -> list[str]:
        """
        Use meta-prompting to improve queries
        LLM critiques and enhances its own queries
        """
        
        meta_prompt = f"""You are a meta-analyst reviewing search queries for quality.

ORIGINAL QUERIES:
{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(original_queries))}

CONTEXT:
Stock: {anomaly.ticker}
Drop: {abs(anomaly.price_change_percent):.1f}%
Volume: {anomaly.volume_ratio:.1f}x

SEARCH STATUS: {'❌ Previous search found nothing useful' if search_failed else '🔍 First attempt'}

TASK: Critique each query and suggest improvements.

Evaluation criteria:
1. Specificity (does it include ticker, timeframe, event type?)
2. Search-engine optimization (will Google/Tavily understand it?)
3. Likelihood of finding root cause (targets right sources?)
4. Relevance to anomaly magnitude (minor news vs major event)

For each query, provide:
- What's good about it
- What's missing
- How to improve it

Then generate 3 IMPROVED queries.

Format:
CRITIQUE:
Query 1: [analysis]
Query 2: [analysis]
Query 3: [analysis]

IMPROVED QUERIES:
1. [better query]
2. [better query]
3. [better query]
"""
        
        response = self.llm.invoke(meta_prompt)
        
        # Parse improved queries
        improved = []
        in_improved_section = False
        
        for line in response.content.split('\n'):
            line = line.strip()
            
            if 'IMPROVED QUERIES' in line.upper():
                in_improved_section = True
                continue
            
            if in_improved_section and line and (line[0].isdigit() or line.startswith('-')):
                query = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                if query:
                    improved.append(query)
        
        return improved[:3] if improved else original_queries


# Test function
def test_meta_optimization():
    """Test meta-prompt optimization"""
    
    print("\n" + "="*60)
    print("🧪 TESTING META-PROMPT OPTIMIZATION")
    print("="*60)
    
    optimizer = MetaPromptOptimizer()
    
    anomaly = StockAnomaly(
        ticker="NVDA",
        price=180.19,
        price_change_percent=-14.2,
        volume=95000000,
        volume_ratio=6.1
    )
    
    # Mediocre original queries
    original = [
        "NVDA news today",
        "NVIDIA stock drop",
        "NVDA earnings"
    ]
    
    print(f"\n🚨 Anomaly: {anomaly.describe()}")
    print(f"\n📋 Original Queries (mediocre):")
    for i, q in enumerate(original, 1):
        print(f"   {i}. {q}")
    
    # Optimize
    print(f"\n🔄 Running meta-optimization...")
    improved = optimizer.optimize_queries(original, anomaly, search_failed=True)
    
    print(f"\n✅ Improved Queries:")
    for i, q in enumerate(improved, 1):
        print(f"   {i}. {q}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_meta_optimization()

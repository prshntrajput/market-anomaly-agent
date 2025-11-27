"""Advanced Query Generator with Chain-of-Thought and Few-Shot Learning"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate
from src.models.schemas import StockAnomaly
from src.utils.config import settings
from src.utils.logger import logger
from typing import List
from pydantic import BaseModel


class ReasoningStep(BaseModel):
    """Structured reasoning step"""
    step_number: int
    analysis: str
    conclusion: str


class QueryWithReasoning(BaseModel):
    """Query with reasoning chain"""
    reasoning_steps: List[ReasoningStep]
    final_queries: List[str]
    confidence: float


class AdvancedQueryGenerator:
    """
    Advanced query generator with:
    - Chain-of-Thought reasoning
    - Few-shot learning
    - Financial domain expertise
    - Self-consistency validation
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.google_api_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )
        
        # Few-shot examples (real financial scenarios)
        self.examples = [
            {
                "anomaly": "Tesla dropped 18% with 5x volume",
                "reasoning": """
Step 1: Identify magnitude - 18% is severe drop requiring major news
Step 2: Volume spike suggests institutional selling or major event
Step 3: Check typical causes for 15%+ drops:
   - Earnings miss (most common for this magnitude)
   - Executive departure (CEO, CFO)
   - Regulatory issues (SEC, safety recalls)
   - Guidance cut (future outlook)
Step 4: Prioritize recent, specific events
Step 5: Include timeframe for relevance
""",
                "queries": [
                    "Tesla Q4 2025 earnings miss analyst expectations revenue guidance",
                    "Tesla CEO Elon Musk SEC investigation November 2025",
                    "Tesla vehicle recall safety NHTSA November 2025"
                ]
            },
            {
                "anomaly": "Microsoft dropped 12% with 4x volume",
                "reasoning": """
Step 1: 12% drop = significant negative event
Step 2: 4x volume = widespread reaction, not just rumors
Step 3: Microsoft is stable company, so check:
   - Cloud business slowdown (Azure)
   - Major contract loss (government/enterprise)
   - Antitrust/regulatory action
   - Guidance adjustment
Step 4: Focus on business-critical segments
""",
                "queries": [
                    "Microsoft Azure revenue growth miss Q4 2025 cloud slowdown",
                    "Microsoft antitrust EU investigation November 2025",
                    "Microsoft earnings guidance cut FY2026 outlook"
                ]
            },
            {
                "anomaly": "Netflix dropped 22% with 6x volume",
                "reasoning": """
Step 1: 22% = catastrophic news (subscriber loss, major failure)
Step 2: 6x volume = market-wide panic selling
Step 3: Netflix key metrics:
   - Subscriber numbers (most important)
   - Content costs/quality
   - Competition impact
   - International expansion
Step 4: Check for earnings report first (most likely cause)
""",
                "queries": [
                    "Netflix Q3 2025 subscriber loss earnings report miss",
                    "Netflix password sharing crackdown backfire subscriber exodus",
                    "Netflix content spending cut original programming 2025"
                ]
            }
        ]
    
    def generate_with_cot(
        self,
        anomaly: StockAnomaly,
        iteration: int = 0
    ) -> QueryWithReasoning:
        """
        Generate queries with Chain-of-Thought reasoning
        """
        logger.info(f"🧠 CoT Query Generation (Iteration {iteration + 1})")
        
        # Build few-shot context
        few_shot_context = self._build_few_shot_context()
        
        # Chain-of-Thought prompt
        cot_prompt = f"""You are an expert financial analyst investigating market anomalies.

TASK: Generate search queries to find the root cause of this anomaly.

ANOMALY:
Stock: {anomaly.ticker}
Price Change: {anomaly.price_change_percent:.2f}%
Volume Spike: {anomaly.volume_ratio:.1f}x normal
Severity: {"CRITICAL" if abs(anomaly.price_change_percent) > 15 else "HIGH"}

REASONING FRAMEWORK:
Use step-by-step analysis (Chain of Thought):

Step 1: Assess Severity
- Is this a minor move (<10%), significant (10-15%), or severe (>15%)?
- What type of news typically causes this magnitude?

Step 2: Analyze Volume Pattern
- High volume ({anomaly.volume_ratio:.1f}x) suggests what?
- Is this institutional selling or retail panic?

Step 3: Identify Likely Root Causes
For {anomaly.ticker} dropping {abs(anomaly.price_change_percent):.1f}%, check:
□ Earnings report (Q3/Q4 2025) - miss/beat?
□ Executive changes (CEO, CFO resignation)?
□ Regulatory/legal issues (SEC, lawsuits)?
□ Product recalls, failures?
□ Major contract loss/win?
□ Guidance revision (up/down)?
□ Analyst downgrades (from which firms)?

Step 4: Prioritize Search Strategy
Iteration {iteration + 1}/3 - Adjust specificity:
- Iteration 1: Broad categories (earnings, management, legal)
- Iteration 2: Specific events with timeframes
- Iteration 3: Exact filings, dates, names

Step 5: Construct Precise Queries
- Include ticker symbol
- Include timeframe (November 2025, Q4 2025)
- Target specific sources (SEC, earnings calls, analyst reports)

EXAMPLES FROM SIMILAR CASES:
{few_shot_context}

YOUR TURN:
Think step-by-step and generate 3 highly specific search queries.

Format your response as:
REASONING:
Step 1: [your analysis]
Step 2: [your analysis]
Step 3: [your analysis]
Step 4: [your analysis]
Step 5: [your analysis]

QUERIES:
1. [specific query]
2. [specific query]
3. [specific query]
"""
        
        response = self.llm.invoke(cot_prompt)
        
        # Parse response
        reasoning_text, queries = self._parse_cot_response(response.content)
        
        logger.info("🔍 Reasoning Chain:")
        for line in reasoning_text.split('\n')[:5]:
            if line.strip():
                logger.info(f"   {line.strip()}")
        
        logger.info("📋 Generated Queries:")
        for i, q in enumerate(queries, 1):
            logger.info(f"   {i}. {q}")
        
        return QueryWithReasoning(
            reasoning_steps=[],  # Simplified for now
            final_queries=queries,
            confidence=0.85
        )
    
    def generate_with_self_consistency(
        self,
        anomaly: StockAnomaly,
        num_attempts: int = 3
    ) -> List[str]:
        """
        Generate queries multiple times and pick most common
        Self-consistency technique for higher quality
        """
        logger.info(f"🔄 Self-Consistency Generation ({num_attempts} attempts)")
        
        all_queries = []
        
        for i in range(num_attempts):
            result = self.generate_with_cot(anomaly, iteration=i)
            all_queries.extend(result.final_queries)
        
        # Count query frequency (by keywords)
        query_scores = {}
        for query in all_queries:
            # Extract key terms
            key_terms = set(query.lower().split())
            key = ' '.join(sorted(key_terms))
            query_scores[key] = query_scores.get(key, []) + [query]
        
        # Pick most consistent queries
        consistent_queries = []
        for key, queries in sorted(
            query_scores.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:3]:
            consistent_queries.append(queries[0])
        
        logger.info("✅ Most consistent queries selected:")
        for i, q in enumerate(consistent_queries, 1):
            logger.info(f"   {i}. {q}")
        
        return consistent_queries
    
    def _build_few_shot_context(self) -> str:
        """Build few-shot learning context from examples"""
        context = []
        for ex in self.examples:
            context.append(f"\nExample: {ex['anomaly']}")
            context.append(f"Reasoning:{ex['reasoning']}")
            context.append("Queries:")
            for i, q in enumerate(ex['queries'], 1):
                context.append(f"{i}. {q}")
        return '\n'.join(context)
    
    def _parse_cot_response(self, response: str) -> tuple[str, List[str]]:
        """Parse Chain-of-Thought response"""
        parts = response.split('QUERIES:')
        reasoning = parts[0].replace('REASONING:', '').strip()
        
        queries = []
        if len(parts) > 1:
            query_text = parts[1].strip()
            for line in query_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    query = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                    if query:
                        queries.append(query)
        
        return reasoning, queries[:3]


# Test function
def test_advanced_generator():
    """Test advanced query generation"""
    
    print("\n" + "="*60)
    print("🧪 TESTING ADVANCED QUERY GENERATOR")
    print("="*60)
    
    generator = AdvancedQueryGenerator()
    
    # Test anomaly
    anomaly = StockAnomaly(
        ticker="META",
        price=633.55,
        price_change_percent=-16.8,
        volume=75000000,
        volume_ratio=5.5
    )
    
    print(f"\n🚨 Anomaly: {anomaly.describe()}")
    
    # Test 1: Chain-of-Thought
    print("\n--- Test 1: Chain-of-Thought ---")
    result1 = generator.generate_with_cot(anomaly, iteration=0)
    
    # Test 2: Self-Consistency
    print("\n--- Test 2: Self-Consistency (3 attempts) ---")
    result2 = generator.generate_with_self_consistency(anomaly, num_attempts=3)
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_advanced_generator()

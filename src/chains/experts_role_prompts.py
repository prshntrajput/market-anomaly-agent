"""Expert role-based prompting for different analysis types - FIXED"""

from enum import Enum
from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.config import settings
from src.models.schemas import StockAnomaly
from src.utils.logger import logger


class ExpertRole(Enum):
    """Different expert personas for analysis"""
    EARNINGS_ANALYST = "earnings_analyst"
    LEGAL_EXPERT = "legal_expert"
    MARKET_TECHNICIAN = "market_technician"
    INSIDER_TRACKER = "insider_tracker"


class ExpertRolePrompts:
    """
    Role-based prompting for specialized query generation
    Each expert has domain-specific knowledge
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.google_api_key,
            temperature=0.6,
            convert_system_message_to_human=True
        )
        
        self.role_definitions = {
            ExpertRole.EARNINGS_ANALYST: """You are a senior earnings analyst at Goldman Sachs with 15 years of experience.

Your expertise:
- Quarterly earnings reports analysis
- Revenue vs. analyst expectations
- Forward guidance evaluation
- Margin compression/expansion analysis

When a stock drops significantly, you FIRST check:
1. Recent earnings reports (Q3/Q4 2025)
2. Revenue beat or miss vs. consensus
3. EPS beat or miss vs. expectations
4. Forward guidance raised or lowered
5. Segment-specific weakness""",

            ExpertRole.LEGAL_EXPERT: """You are a securities litigation attorney specializing in corporate governance.

Your expertise:
- SEC filings (8-K, 10-Q, 10-K)
- Shareholder lawsuits
- Regulatory investigations
- Insider trading violations

When a stock crashes, you check:
1. Recent SEC 8-K filings (material events)
2. DOJ or SEC investigation announcements
3. Class action lawsuits filed
4. Regulatory fines or penalties
5. Executive resignations with legal implications""",

            ExpertRole.MARKET_TECHNICIAN: """You are a chief technical analyst at a major hedge fund.

Your expertise:
- Chart patterns and breakdowns
- Volume analysis
- Institutional order flow
- Options market signals

When volume spikes with a crash, you investigate:
1. Major support level breaks
2. Unusual options activity (puts vs calls)
3. Short interest spikes
4. Insider selling patterns (Form 4)
5. Institutional selling signals""",

            ExpertRole.INSIDER_TRACKER: """You are an investigative financial journalist specializing in corporate insiders.

Your expertise:
- Form 4 SEC filings (insider transactions)
- Executive compensation changes
- Board member resignations
- C-suite departures

When insiders know something, they act first. You check:
1. Recent insider selling (last 30 days)
2. CEO or CFO resignation
3. Board changes or conflicts
4. Whistleblower reports
5. Activist investor 13D filings"""
        }
    
    def generate_expert_queries(
        self,
        anomaly: StockAnomaly,
        role: ExpertRole
    ) -> list[str]:
        """
        Generate queries from expert perspective
        
        Args:
            anomaly: Stock anomaly being investigated
            role: Expert role perspective
        
        Returns:
            List of 3 short, specific search queries
        """
        role_context = self.role_definitions[role]
        
        prompt = f"""{role_context}

URGENT CASE:
Stock: {anomaly.ticker}
Drop: {abs(anomaly.price_change_percent):.1f}%
Volume: {anomaly.volume_ratio:.1f}x normal
Date: November 2025

CRITICAL INSTRUCTIONS:
1. Generate EXACTLY 3 search queries
2. Each query must be SHORT (under 100 characters)
3. Include ticker symbol in each query
4. Include timeframe (November 2025, Q3 2025, etc.)
5. Be SPECIFIC, not generic

FORMAT (follow exactly):
1. [short query under 100 chars]
2. [short query under 100 chars]
3. [short query under 100 chars]

GOOD EXAMPLES:
- AAPL Q3 2025 earnings miss revenue guidance cut
- TSLA SEC investigation November 2025
- META antitrust fine EU November 2025

BAD EXAMPLES (too long):
- Meta Platforms significantly lowered their forward revenue guidance for Q4...

Return ONLY the 3 numbered queries, nothing else.
"""
        
        try:
            response = self.llm.invoke(prompt)
            
            # Parse queries
            queries = []
            for line in response.content.strip().split('\n'):
                line = line.strip()
                
                # Skip empty lines or lines without queries
                if not line or len(line) < 10:
                    continue
                
                # Extract query from numbered or bulleted line
                if line[0].isdigit() or line.startswith('-') or line.startswith('•'):
                    # Remove numbering
                    if '.' in line[:5]:
                        query = line.split('.', 1)[1].strip()
                    else:
                        query = line[1:].strip()
                    
                    # Remove markdown formatting
                    query = query.replace('**', '').replace('*', '').strip()
                    
                    # Remove quotes if present
                    query = query.strip('"').strip("'").strip()
                    
                    # Truncate if too long
                    if len(query) > 250:
                        query = query[:250].rsplit(' ', 1)[0]
                    
                    # Add if valid
                    if 15 < len(query) <= 250:
                        queries.append(query)
            
            # Ensure we have exactly 3 queries
            if len(queries) < 3:
                logger.warning(f"   Only got {len(queries)} queries, adding fallbacks")
                fallback_queries = [
                    f"{anomaly.ticker} earnings Q3 2025 miss",
                    f"{anomaly.ticker} SEC filing November 2025",
                    f"{anomaly.ticker} analyst downgrade November 2025"
                ]
                queries.extend(fallback_queries)
            
            return queries[:3]
            
        except Exception as e:
            logger.error(f"Expert query generation failed: {e}")
            # Return fallback queries
            return [
                f"{anomaly.ticker} earnings report Q3 2025",
                f"{anomaly.ticker} SEC filing November 2025",
                f"{anomaly.ticker} analyst rating November 2025"
            ]
    
    def generate_multi_expert_queries(
        self,
        anomaly: StockAnomaly
    ) -> dict[ExpertRole, list[str]]:
        """
        Get queries from multiple expert perspectives
        Provides comprehensive coverage
        """
        all_queries = {}
        
        for role in ExpertRole:
            queries = self.generate_expert_queries(anomaly, role)
            all_queries[role] = queries
        
        return all_queries


# Test function
def test_expert_roles():
    """Test expert role prompting"""
    
    print("\n" + "="*60)
    print("🧪 TESTING EXPERT ROLE PROMPTING (FIXED)")
    print("="*60)
    
    expert_system = ExpertRolePrompts()
    
    anomaly = StockAnomaly(
        ticker="META",
        price=633.55,
        price_change_percent=-17.2,
        volume=95000000,
        volume_ratio=6.5
    )
    
    print(f"\n🚨 Anomaly: {anomaly.describe()}")
    
    # Get queries from all experts
    all_queries = expert_system.generate_multi_expert_queries(anomaly)
    
    for role, queries in all_queries.items():
        print(f"\n👨‍💼 {role.value.replace('_', ' ').title()}:")
        for i, q in enumerate(queries, 1):
            print(f"   {i}. {q}")
            print(f"      Length: {len(q)} chars")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_expert_roles()

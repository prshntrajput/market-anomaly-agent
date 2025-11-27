"""Expert role-based prompting for different analysis types"""

from enum import Enum
from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.config import settings
from src.models.schemas import StockAnomaly


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
- Dissecting quarterly earnings reports
- Comparing actual vs. analyst expectations
- Understanding revenue guidance implications
- Identifying red flags in CFO commentary
- Tracking margin compression/expansion

When a stock drops significantly, you FIRST check:
1. Did they report earnings recently? (Q3/Q4 2025?)
2. Revenue beat or miss?
3. EPS beat or miss?
4. Forward guidance raised or lowered?
5. Any segment weakness? (e.g., AWS for Amazon, iPhone for Apple)

Your queries are PRECISE with numbers and comparisons.""",

            ExpertRole.LEGAL_EXPERT: """You are a securities litigation attorney specializing in corporate governance and SEC regulations.

Your expertise:
- SEC filings (8-K, 10-Q, 10-K)
- Shareholder lawsuits
- Regulatory investigations
- Insider trading violations
- Patent disputes
- Antitrust cases

When a stock crashes, you check:
1. Any recent SEC 8-K filings? (material events)
2. DOJ or SEC investigation announcements?
3. Class action lawsuits filed?
4. Executive resignations with legal implications?
5. FDA warnings, EPA violations?

Your queries target SPECIFIC legal events and filings.""",

            ExpertRole.MARKET_TECHNICIAN: """You are a chief technical analyst at a major hedge fund.

Your expertise:
- Chart patterns and breakdowns
- Support/resistance levels
- Volume analysis
- Institutional order flow
- Options market signals
- Short interest dynamics

When volume spikes with a crash, you investigate:
1. Was a major support level broken?
2. Unusual options activity? (puts vs calls)
3. Short squeeze or short interest spike?
4. Institutional selling patterns (Form 4 filings)?
5. Insider selling before the drop?

Your queries focus on TRADING ACTIVITY and positioning.""",

            ExpertRole.INSIDER_TRACKER: """You are an investigative financial journalist specializing in corporate insiders.

Your expertise:
- Form 4 SEC filings (insider transactions)
- Executive compensation changes
- Board member resignations
- C-suite departures
- Activist investor campaigns

When insiders know something, they act first. You check:
1. Recent insider selling? (last 30 days)
2. CEO or CFO resignation?
3. Board changes or conflicts?
4. Whistleblower reports?
5. Activist investor 13D filings?

Your queries hunt for INSIDER SIGNALS and governance issues."""
        }
    
    def generate_expert_queries(
        self,
        anomaly: StockAnomaly,
        role: ExpertRole
    ) -> list[str]:
        """
        Generate queries from expert perspective
        """
        role_context = self.role_definitions[role]
        
        prompt = f"""{role_context}

URGENT CASE:
Stock: {anomaly.ticker}
Drop: {abs(anomaly.price_change_percent):.1f}%
Volume: {anomaly.volume_ratio:.1f}x normal
Date: November 2025

Based on YOUR expertise, what are the 3 most likely causes?
Generate 3 specific search queries to investigate.

Format:
1. [specific query]
2. [specific query]
3. [specific query]
"""
        
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
    print("🧪 TESTING EXPERT ROLE PROMPTING")
    print("="*60)
    
    expert_system = ExpertRolePrompts()
    
    anomaly = StockAnomaly(
        ticker="GOOGL",
        price=320.01,
        price_change_percent=-19.5,
        volume=120000000,
        volume_ratio=7.2
    )
    
    print(f"\n🚨 Anomaly: {anomaly.describe()}")
    
    # Get queries from all experts
    all_queries = expert_system.generate_multi_expert_queries(anomaly)
    
    for role, queries in all_queries.items():
        print(f"\n👨‍💼 {role.value.replace('_', ' ').title()}:")
        for i, q in enumerate(queries, 1):
            print(f"   {i}. {q}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_expert_roles()

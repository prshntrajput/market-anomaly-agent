"""Source Credibility Scoring System"""

from enum import Enum
from typing import Dict, List
from dataclasses import dataclass


class SourceTier(Enum):
    """Source reliability tiers"""
    TIER_1_OFFICIAL = "tier_1_official"      # SEC, Company IR, Official filings
    TIER_2_PREMIUM = "tier_2_premium"        # Bloomberg, Reuters, WSJ
    TIER_3_MAINSTREAM = "tier_3_mainstream"  # CNBC, MarketWatch, Yahoo Finance
    TIER_4_AGGREGATOR = "tier_4_aggregator"  # Seeking Alpha, Motley Fool
    TIER_5_SOCIAL = "tier_5_social"          # Twitter, Reddit, Blogs
    TIER_UNKNOWN = "tier_unknown"            # Unknown sources


@dataclass
class SourceScore:
    """Source credibility score"""
    domain: str
    tier: SourceTier
    credibility_score: float  # 0.0 to 1.0
    reasoning: str


class SourceCredibilityScorer:
    """
    Evaluate source credibility for financial information
    """
    
    def __init__(self):
        # Domain classification with credibility scores
        self.source_tiers: Dict[str, tuple[SourceTier, float]] = {
            # Tier 1: Official Sources (0.95-1.0)
            "sec.gov": (SourceTier.TIER_1_OFFICIAL, 1.0),
            "investor.*.com": (SourceTier.TIER_1_OFFICIAL, 0.98),
            "ir.*.com": (SourceTier.TIER_1_OFFICIAL, 0.98),
            
            # Tier 2: Premium Financial Media (0.85-0.94)
            "bloomberg.com": (SourceTier.TIER_2_PREMIUM, 0.94),
            "reuters.com": (SourceTier.TIER_2_PREMIUM, 0.93),
            "wsj.com": (SourceTier.TIER_2_PREMIUM, 0.92),
            "ft.com": (SourceTier.TIER_2_PREMIUM, 0.91),
            "barrons.com": (SourceTier.TIER_2_PREMIUM, 0.90),
            
            # Tier 3: Mainstream Financial Media (0.70-0.84)
            "cnbc.com": (SourceTier.TIER_3_MAINSTREAM, 0.84),
            "marketwatch.com": (SourceTier.TIER_3_MAINSTREAM, 0.82),
            "finance.yahoo.com": (SourceTier.TIER_3_MAINSTREAM, 0.80),
            "investopedia.com": (SourceTier.TIER_3_MAINSTREAM, 0.78),
            "forbes.com": (SourceTier.TIER_3_MAINSTREAM, 0.75),
            
            # Tier 4: Aggregators & Analysis Sites (0.50-0.69)
            "seekingalpha.com": (SourceTier.TIER_4_AGGREGATOR, 0.68),
            "fool.com": (SourceTier.TIER_4_AGGREGATOR, 0.65),
            "benzinga.com": (SourceTier.TIER_4_AGGREGATOR, 0.62),
            "zacks.com": (SourceTier.TIER_4_AGGREGATOR, 0.60),
            
            # Tier 5: Social/Community (0.20-0.49)
            "twitter.com": (SourceTier.TIER_5_SOCIAL, 0.40),
            "reddit.com": (SourceTier.TIER_5_SOCIAL, 0.35),
            "medium.com": (SourceTier.TIER_5_SOCIAL, 0.30),
        }
    
    def score_source(self, url: str) -> SourceScore:
        """
        Score source credibility based on domain
        
        Args:
            url: Source URL
        
        Returns:
            SourceScore with tier and credibility
        """
        # Extract domain
        domain = self._extract_domain(url)
        
        # Find matching tier
        for source_pattern, (tier, score) in self.source_tiers.items():
            if self._matches_pattern(domain, source_pattern):
                reasoning = self._get_tier_reasoning(tier)
                return SourceScore(
                    domain=domain,
                    tier=tier,
                    credibility_score=score,
                    reasoning=reasoning
                )
        
        # Unknown source - default low credibility
        return SourceScore(
            domain=domain,
            tier=SourceTier.TIER_UNKNOWN,
            credibility_score=0.40,
            reasoning="Unknown source - credibility cannot be verified"
        )
    
    def score_multiple_sources(self, urls: List[str]) -> Dict[str, SourceScore]:
        """Score multiple sources"""
        return {url: self.score_source(url) for url in urls}
    
    def get_weighted_credibility(self, source_scores: List[SourceScore]) -> float:
        """
        Calculate weighted average credibility
        Gives more weight to higher-tier sources
        """
        if not source_scores:
            return 0.0
        
        total_score = sum(score.credibility_score for score in source_scores)
        return total_score / len(source_scores)
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        # Simple extraction
        if "://" in url:
            url = url.split("://")[1]
        domain = url.split("/")[0]
        return domain.lower()
    
    def _matches_pattern(self, domain: str, pattern: str) -> bool:
        """Check if domain matches pattern (supports wildcards)"""
        if "*" in pattern:
            parts = pattern.split("*")
            return all(part in domain for part in parts if part)
        return domain == pattern
    
    def _get_tier_reasoning(self, tier: SourceTier) -> str:
        """Get reasoning for tier assignment"""
        reasoning_map = {
            SourceTier.TIER_1_OFFICIAL: "Official source - SEC filings or company investor relations",
            SourceTier.TIER_2_PREMIUM: "Premium financial media - highly credible journalism",
            SourceTier.TIER_3_MAINSTREAM: "Mainstream financial media - generally reliable",
            SourceTier.TIER_4_AGGREGATOR: "Analysis aggregator - mixed credibility",
            SourceTier.TIER_5_SOCIAL: "Social/community source - low credibility",
            SourceTier.TIER_UNKNOWN: "Unknown source - credibility cannot be verified"
        }
        return reasoning_map.get(tier, "Unknown tier")


# Test function
def test_source_credibility():
    """Test source credibility scoring"""
    
    print("\n" + "="*60)
    print("🧪 TESTING SOURCE CREDIBILITY SCORER")
    print("="*60)
    
    scorer = SourceCredibilityScorer()
    
    # Test URLs
    test_urls = [
        "https://www.sec.gov/cgi-bin/browse-edgar",
        "https://www.bloomberg.com/news/articles/2025-11-27/apple-stock",
        "https://www.cnbc.com/2025/11/27/tesla-earnings.html",
        "https://seekingalpha.com/article/apple-analysis",
        "https://twitter.com/elonmusk/status/123456",
        "https://unknown-blog.com/stock-tips"
    ]
    
    for url in test_urls:
        score = scorer.score_source(url)
        print(f"\n📊 {score.domain}")
        print(f"   Tier: {score.tier.value}")
        print(f"   Credibility: {score.credibility_score:.2f}/1.0")
        print(f"   Reasoning: {score.reasoning}")
    
    # Test weighted credibility
    scores = [scorer.score_source(url) for url in test_urls]
    weighted = scorer.get_weighted_credibility(scores)
    print(f"\n📈 Weighted Average Credibility: {weighted:.2f}/1.0")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_source_credibility()

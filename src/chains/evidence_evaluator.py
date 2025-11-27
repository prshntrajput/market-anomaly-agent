"""Advanced Evidence Evaluation System - FIXED"""

from pydantic import BaseModel, Field
from typing import List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.source_credibility import SourceCredibilityScorer, SourceScore
from src.models.schemas import StockAnomaly
from src.utils.config import settings
from src.utils.logger import logger


class EvidenceItem(BaseModel):
    """Single piece of evidence"""
    content: str
    source_url: str
    source_credibility: float
    relevance_score: float
    specificity_score: float


class EvidenceEvaluation(BaseModel):
    """Comprehensive evidence evaluation"""
    evidence_items: List[EvidenceItem]
    overall_credibility: float = Field(ge=0.0, le=1.0)
    overall_relevance: float = Field(ge=0.0, le=1.0)
    explanation_found: bool
    explanation_quality: str  # "excellent", "good", "fair", "poor"
    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    missing_info: List[str]


class SynthesisResult(BaseModel):
    """Structured synthesis result from LLM"""
    explanation_found: bool
    explanation_quality: str
    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    missing_info: List[str] = Field(default_factory=list)


class AdvancedEvidenceEvaluator:
    """
    Multi-level evidence evaluation system
    
    Evaluates:
    1. Source credibility
    2. Content relevance
    3. Explanation quality
    4. Overall confidence
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.google_api_key,
            temperature=0.2,
            convert_system_message_to_human=True
        )
        self.credibility_scorer = SourceCredibilityScorer()
    
    def evaluate_evidence(
        self,
        anomaly: StockAnomaly,
        search_results: Dict[str, Dict]
    ) -> EvidenceEvaluation:
        """
        Comprehensive evidence evaluation
        
        Args:
            anomaly: Stock anomaly being investigated
            search_results: Tavily search results
        
        Returns:
            EvidenceEvaluation with detailed scoring
        """
        logger.info("🔬 Advanced Evidence Evaluation")
        
        # Step 1: Extract evidence items
        evidence_items = self._extract_evidence_items(search_results)
        logger.info(f"   Extracted {len(evidence_items)} evidence items")
        
        if not evidence_items:
            logger.warning("   No evidence items found")
            return self._create_empty_evaluation()
        
        # Step 2: Score each item
        scored_items = []
        for item in evidence_items:
            scored_item = self._score_evidence_item(item, anomaly)
            scored_items.append(scored_item)
        
        # Step 3: Calculate aggregate scores
        overall_credibility = self._calculate_overall_credibility(scored_items)
        overall_relevance = self._calculate_overall_relevance(scored_items)
        
        logger.info(f"   Overall Credibility: {overall_credibility:.0%}")
        logger.info(f"   Overall Relevance: {overall_relevance:.0%}")
        
        # Step 4: Synthesize explanation
        explanation_result = self._synthesize_explanation(
            anomaly,
            scored_items,
            overall_credibility,
            overall_relevance
        )
        
        return explanation_result
    
    def _extract_evidence_items(
        self,
        search_results: Dict[str, Dict]
    ) -> List[Dict]:
        """Extract evidence items from Tavily results"""
        evidence_items = []
        
        for query, result in search_results.items():
            # Add AI answer if available
            if result.get('answer'):
                evidence_items.append({
                    "content": result['answer'],
                    "source_url": "tavily_ai_synthesis",
                    "type": "ai_synthesis"
                })
            
            # Add individual results
            for res in result.get('results', [])[:3]:
                if res.get('content'):
                    evidence_items.append({
                        "content": f"{res.get('title', '')}: {res.get('content', '')}",
                        "source_url": res.get('url', 'unknown'),
                        "type": "search_result"
                    })
        
        return evidence_items
    
    def _score_evidence_item(
        self,
        item: Dict,
        anomaly: StockAnomaly
    ) -> EvidenceItem:
        """Score individual evidence item"""
        
        # Score source credibility
        if item['type'] == 'ai_synthesis':
            source_credibility = 0.85
        else:
            source_score = self.credibility_scorer.score_source(item['source_url'])
            source_credibility = source_score.credibility_score
        
        # Score relevance and specificity using LLM
        scoring_prompt = f"""Score this evidence for investigating a stock anomaly.

ANOMALY: {anomaly.ticker} dropped {abs(anomaly.price_change_percent):.1f}%

EVIDENCE: {item['content'][:300]}

Rate on scale 0.0-1.0:
1. RELEVANCE: Does it explain THIS specific anomaly?
   - 1.0 = Directly explains with specific details
   - 0.5 = Mentions company but not specific
   - 0.0 = Unrelated

2. SPECIFICITY: How specific is the information?
   - 1.0 = Exact numbers, dates, events
   - 0.5 = General statements
   - 0.0 = Vague

Return only two numbers: relevance,specificity
Example: 0.85,0.90
"""
        
        try:
            response = self.llm.invoke(scoring_prompt)
            scores_text = response.content.strip()
            
            # Parse scores
            scores = scores_text.split(',')
            relevance_score = float(scores[0].strip())
            specificity_score = float(scores[1].strip())
            
            # Clamp values
            relevance_score = max(0.0, min(1.0, relevance_score))
            specificity_score = max(0.0, min(1.0, specificity_score))
            
        except Exception as e:
            logger.warning(f"Scoring failed: {e}, using defaults")
            relevance_score = 0.5
            specificity_score = 0.5
        
        return EvidenceItem(
            content=item['content'][:500],
            source_url=item['source_url'],
            source_credibility=source_credibility,
            relevance_score=relevance_score,
            specificity_score=specificity_score
        )
    
    def _calculate_overall_credibility(
        self,
        items: List[EvidenceItem]
    ) -> float:
        """Calculate weighted average credibility"""
        if not items:
            return 0.0
        
        # Weight by relevance
        weighted_sum = sum(
            item.source_credibility * item.relevance_score
            for item in items
        )
        weight_total = sum(item.relevance_score for item in items)
        
        return weighted_sum / weight_total if weight_total > 0 else 0.0
    
    def _calculate_overall_relevance(
        self,
        items: List[EvidenceItem]
    ) -> float:
        """Calculate average relevance"""
        if not items:
            return 0.0
        
        return sum(item.relevance_score for item in items) / len(items)
    
    def _synthesize_explanation(
        self,
        anomaly: StockAnomaly,
        evidence_items: List[EvidenceItem],
        overall_credibility: float,
        overall_relevance: float
    ) -> EvidenceEvaluation:
        """Synthesize final explanation from evidence - FIXED"""
        
        # Build evidence summary
        evidence_summary = []
        for i, item in enumerate(sorted(
            evidence_items,
            key=lambda x: x.relevance_score * x.source_credibility,
            reverse=True
        )[:5], 1):
            evidence_summary.append(
                f"{i}. [{item.source_credibility:.0%} credible, {item.relevance_score:.0%} relevant]\n"
                f"   {item.content[:200]}"
            )
        
        evidence_text = "\n\n".join(evidence_summary) if evidence_summary else "No significant evidence found"
        
        synthesis_prompt = f"""You are a financial analyst synthesizing investigation results.

ANOMALY:
{anomaly.ticker} dropped {abs(anomaly.price_change_percent):.1f}% with {anomaly.volume_ratio:.1f}x volume

EVIDENCE (sorted by quality):
{evidence_text}

EVIDENCE METRICS:
- Overall Source Credibility: {overall_credibility:.0%}
- Overall Relevance: {overall_relevance:.0%}

TASK: Provide final judgment with these fields:

explanation_found: true if clear root cause found, false otherwise
explanation_quality: "excellent", "good", "fair", or "poor"
root_cause: One sentence explanation (or "Unable to determine root cause")
confidence: Number between 0.0 and 1.0
reasoning: Brief explanation of your judgment (max 200 chars)
missing_info: List 1-2 missing items (empty list if none)

Return structured response.
"""
        
        try:
            # FIXED: Use structured output with Pydantic
            llm_with_structure = self.llm.with_structured_output(SynthesisResult)
            result = llm_with_structure.invoke(synthesis_prompt)
            
            logger.info(f"   Synthesis successful")
            
            return EvidenceEvaluation(
                evidence_items=evidence_items,
                overall_credibility=overall_credibility,
                overall_relevance=overall_relevance,
                explanation_found=result.explanation_found,
                explanation_quality=result.explanation_quality,
                root_cause=result.root_cause,
                confidence=result.confidence,
                reasoning=result.reasoning,
                missing_info=result.missing_info
            )
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            
            # FIXED: Better fallback logic
            fallback_explanation_found = overall_credibility > 0.65 and overall_relevance > 0.55
            fallback_confidence = min(0.85, (overall_credibility * 0.5 + overall_relevance * 0.5))
            
            if not fallback_explanation_found:
                fallback_confidence = max(0.25, fallback_confidence * 0.6)
            
            return EvidenceEvaluation(
                evidence_items=evidence_items,
                overall_credibility=overall_credibility,
                overall_relevance=overall_relevance,
                explanation_found=fallback_explanation_found,
                explanation_quality="fair" if fallback_explanation_found else "poor",
                root_cause="Investigation completed but synthesis failed" if fallback_explanation_found else "Unable to determine root cause",
                confidence=fallback_confidence,
                reasoning=f"Synthesis error. Based on credibility ({overall_credibility:.0%}) and relevance ({overall_relevance:.0%}).",
                missing_info=["LLM synthesis failed - manual review recommended"]
            )
    
    def _create_empty_evaluation(self) -> EvidenceEvaluation:
        """Create empty evaluation when no evidence found"""
        return EvidenceEvaluation(
            evidence_items=[],
            overall_credibility=0.0,
            overall_relevance=0.0,
            explanation_found=False,
            explanation_quality="poor",
            root_cause="No evidence found in search results",
            confidence=0.0,
            reasoning="Search returned no usable evidence",
            missing_info=["More targeted search queries needed"]
        )


# Test function
def test_evidence_evaluator():
    """Test evidence evaluation"""
    
    print("\n" + "="*60)
    print("🧪 TESTING ADVANCED EVIDENCE EVALUATOR (FIXED)")
    print("="*60)
    
    evaluator = AdvancedEvidenceEvaluator()
    
    # Mock anomaly
    anomaly = StockAnomaly(
        ticker="AAPL",
        price=277.47,
        price_change_percent=-14.5,
        volume=75000000,
        volume_ratio=5.2
    )
    
    # Mock search results
    mock_results = {
        "AAPL earnings Q4 2025": {
            "answer": "Apple missed Q4 2025 earnings expectations with EPS of $1.25 vs expected $1.50",
            "results": [
                {
                    "title": "Apple Q4 Earnings Miss",
                    "content": "Apple Inc reported Q4 earnings that fell short with 8% revenue decline",
                    "url": "https://www.bloomberg.com/news/apple-earnings"
                }
            ]
        }
    }
    
    print(f"\n🚨 Anomaly: {anomaly.describe()}")
    print(f"\n🔍 Evaluating evidence...")
    
    result = evaluator.evaluate_evidence(anomaly, mock_results)
    
    print(f"\n📊 EVALUATION RESULTS")
    print(f"   Explanation Found: {result.explanation_found}")
    print(f"   Quality: {result.explanation_quality}")
    print(f"   Confidence: {result.confidence:.0%}")
    print(f"   Root Cause: {result.root_cause}")
    print(f"   Reasoning: {result.reasoning}")
    print(f"   Evidence Items: {len(result.evidence_items)}")
    print(f"   Overall Credibility: {result.overall_credibility:.0%}")
    print(f"   Overall Relevance: {result.overall_relevance:.0%}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_evidence_evaluator()

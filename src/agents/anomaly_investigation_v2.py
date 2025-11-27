"""Complete Anomaly Investigation with Reflection Pattern - Day 3 Final"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from src.models.schemas import StockAnomaly
from src.utils.config import settings


# Structured critique model
class InvestigationCritique(BaseModel):
    """Critique of investigation quality"""
    explanation_found: bool = Field(description="Did we find root cause?")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(description="Why this score?")
    improvement_hint: str = Field(description="How to improve queries?")


# State
class InvestigationState(TypedDict):
    """Complete investigation state with reflection"""
    # Input
    anomaly: StockAnomaly
    
    # Query generation
    search_queries: list[str]
    
    # Mock search results (Day 5 mein real hoga)
    search_results: str
    
    # Critique & decision
    critique: InvestigationCritique | None
    
    # Loop control
    iteration: int
    investigation_complete: bool


# Node 1: Generate queries
def generate_investigation_queries(state: InvestigationState) -> dict:
    """Generate investigation queries with refinement"""
    anomaly = state["anomaly"]
    iteration = state["iteration"]
    previous_critique = state.get("critique")
    
    print(f"\n📋 QUERY GENERATOR (Attempt {iteration + 1})")
    print(f"   Investigating: {anomaly.describe()}")
    
    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0.7,
        convert_system_message_to_human=True
    )
    
    # Dynamic prompt based on feedback
    if iteration == 0:
        specificity = "broad"
        example = f"{anomaly.ticker} news today"
    elif iteration == 1:
        specificity = "specific"
        example = f"{anomaly.ticker} earnings report Q3 2025"
    else:
        specificity = "hyper-specific"
        example = f"{anomaly.ticker} SEC 8-K filing November 26 2025"
    
    prompt = f"""Generate 3 {specificity} search queries for this anomaly:

Stock: {anomaly.ticker}
Change: {anomaly.price_change_percent:.2f}%
Volume: {anomaly.volume_ratio:.1f}x

Iteration: {iteration + 1}/3 (be MORE specific each time)
Example query style: "{example}"

Focus areas: earnings, SEC filings, analyst ratings, management changes, legal issues
"""
    
    if previous_critique and not previous_critique.explanation_found:
        prompt += f"""
PREVIOUS QUERIES FAILED!
Issue: {previous_critique.improvement_hint}

Generate BETTER, MORE SPECIFIC queries this time!
"""
    
    response = llm.invoke(prompt)
    
    # Parse
    queries = []
    for line in response.content.strip().split('\n'):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('-')):
            query = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
            if query:
                queries.append(query)
    
    queries = queries[:3]
    
    print(f"   Generated:")
    for i, q in enumerate(queries, 1):
        print(f"     {i}. {q}")
    
    return {"search_queries": queries}


# Node 2: Mock search (Day 5 mein real Tavily search)
def execute_mock_search(state: InvestigationState) -> dict:
    """
    Mock search execution
    In Day 5, this will call Tavily API
    """
    queries = state["search_queries"]
    iteration = state["iteration"]
    
    print(f"\n🌐 SEARCH ENGINE (Mock)")
    print(f"   Executing {len(queries)} queries...")
    
    # Mock results - quality improves with iterations
    if iteration == 0:
        mock_results = f"""
Generic results for {queries[0]}:
- {state['anomaly'].ticker} stock drops in market selloff
- Investors worried about tech sector
- General market volatility continues
"""
    elif iteration == 1:
        mock_results = f"""
Specific results for {queries[0]}:
- {state['anomaly'].ticker} Q3 earnings miss analyst expectations by 15%
- Revenue guidance lowered for Q4 2025
- Major client contract renewal delayed
"""
    else:
        mock_results = f"""
Detailed results for {queries[0]}:
- {state['anomaly'].ticker} SEC 8-K filing (November 26, 2025): CEO resignation announced
- CFO commentary: "Strategic restructuring underway"
- Analyst downgrades from Buy to Hold across 3 major firms
- Insider selling increased 200% in past 30 days
"""
    
    print(f"   Results preview: {mock_results[:80]}...")
    
    return {"search_results": mock_results}


# Node 3: Critique investigation
def critique_investigation(state: InvestigationState) -> dict:
    """Critic evaluates if we found root cause"""
    anomaly = state["anomaly"]
    queries = state["search_queries"]
    search_results = state["search_results"]
    iteration = state["iteration"]
    
    print(f"\n🔍 CRITIC")
    print(f"   Evaluating investigation quality...")
    
    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0.2,
        convert_system_message_to_human=True
    )
    
    llm_with_structure = llm.with_structured_output(InvestigationCritique)
    
    critique_prompt = f"""You are an investigation quality evaluator.

ANOMALY: {anomaly.ticker} dropped {abs(anomaly.price_change_percent):.1f}% with {anomaly.volume_ratio:.1f}x volume

QUERIES USED:
{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(queries))}

SEARCH RESULTS:
{search_results}

EVALUATE:
1. Do results explain WHY stock dropped so much?
2. Is the explanation SPECIFIC (not just "market volatility")?
3. Is it CREDIBLE (earnings, filings, management changes)?
4. Does it explain the MAGNITUDE of drop ({abs(anomaly.price_change_percent):.1f}%)?

SCORING:
- explanation_found = True IF results clearly explain root cause
- confidence = 0.0-1.0 (how convinced are you?)
- reasoning = Why this score?
- improvement_hint = If not found, what type of queries to try next?

Return structured critique.
"""
    
    critique = llm_with_structure.invoke(critique_prompt)
    
    print(f"   Explanation Found: {critique.explanation_found}")
    print(f"   Confidence: {critique.confidence:.0%}")
    print(f"   Reasoning: {critique.reasoning[:80]}...")
    
    investigation_complete = (
        critique.explanation_found or 
        iteration >= settings.max_retries - 1
    )
    
    return {
        "critique": critique,
        "investigation_complete": investigation_complete
    }


# Node 4: Increment iteration
def increment_iteration(state: InvestigationState) -> dict:
    """Prepare for next iteration"""
    new_iteration = state["iteration"] + 1
    print(f"\n🔄 Retrying with iteration {new_iteration + 1}...")
    return {"iteration": new_iteration}


# Node 5: Final report
def generate_final_report(state: InvestigationState) -> dict:
    """Generate final investigation report"""
    anomaly = state["anomaly"]
    critique = state["critique"]
    iteration = state["iteration"]
    
    print(f"\n" + "="*60)
    print("📊 FINAL INVESTIGATION REPORT")
    print("="*60)
    print(f"Anomaly: {anomaly.describe()}")
    print(f"Iterations: {iteration + 1}/{settings.max_retries}")
    print(f"Status: {'✅ SOLVED' if critique.explanation_found else '⚠️ UNSOLVED'}")
    print(f"Confidence: {critique.confidence:.0%}")
    print(f"\nConclusion:")
    print(f"  {critique.reasoning}")
    print("="*60)
    
    return {}


# Conditional edge
def should_continue_investigation(state: InvestigationState) -> Literal["retry", "report"]:
    """Decide: continue or finish?"""
    if state["investigation_complete"]:
        return "report"
    else:
        return "retry"


# Create graph
def create_investigation_graph_v2():
    """Complete investigation with reflection"""
    
    workflow = StateGraph(InvestigationState)
    
    # Add nodes
    workflow.add_node("generate_queries", generate_investigation_queries)
    workflow.add_node("search", execute_mock_search)
    workflow.add_node("critique", critique_investigation)
    workflow.add_node("increment", increment_iteration)
    workflow.add_node("report", generate_final_report)
    
    # Add edges
    workflow.add_edge(START, "generate_queries")
    workflow.add_edge("generate_queries", "search")
    workflow.add_edge("search", "critique")
    
    # THE SELF-CORRECTION LOOP!
    workflow.add_conditional_edges(
        "critique",
        should_continue_investigation,
        {
            "retry": "increment",
            "report": "report"
        }
    )
    
    workflow.add_edge("increment", "generate_queries")
    workflow.add_edge("report", END)
    
    return workflow.compile()


# Test function
def test_investigation_v2():
    """Test complete investigation with reflection"""
    
    print("\n" + "="*60)
    print("🧪 TESTING COMPLETE INVESTIGATION WITH REFLECTION")
    print("="*60)
    
    app = create_investigation_graph_v2()
    
    # Test case
    test_anomaly = StockAnomaly(
        ticker="TCS",
        price=3420.00,
        price_change_percent=-16.8,
        volume=15000000,
        volume_ratio=6.3
    )
    
    initial_state = {
        "anomaly": test_anomaly,
        "search_queries": [],
        "search_results": "",
        "critique": None,
        "iteration": 0,
        "investigation_complete": False
    }
    
    result = app.invoke(initial_state)
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_investigation_v2()

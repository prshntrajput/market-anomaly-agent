"""Market Anomaly Investigation v3 - With Real Tavily Search"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from src.models.schemas import StockAnomaly
from src.tools.tavily_search import TavilySearchTool
from src.utils.config import settings
from src.utils.logger import logger


# Structured critique model
class InvestigationCritique(BaseModel):
    """Critique of investigation quality"""
    explanation_found: bool = Field(description="Did we find root cause?")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(description="Why this score?")
    improvement_hint: str = Field(description="How to improve queries?")


# State
class InvestigationState(TypedDict):
    """Complete investigation state"""
    # Input
    anomaly: StockAnomaly
    
    # Query generation
    search_queries: list[str]
    
    # Real search results!
    search_results: dict  # Tavily responses
    
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
    
    logger.info(f"📋 Query Generator (Attempt {iteration + 1}/{settings.max_retries})")
    logger.info(f"   Investigating: {anomaly.describe()}")
    
    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0.7,
        convert_system_message_to_human=True
    )
    
    # Dynamic prompt based on iteration
    if iteration == 0:
        specificity = "broad but targeted"
        example = f"{anomaly.ticker} news today"
    elif iteration == 1:
        specificity = "specific with timeframes"
        example = f"{anomaly.ticker} earnings report Q4 2025"
    else:
        specificity = "hyper-specific with exact events"
        example = f"{anomaly.ticker} SEC 8-K filing CEO resignation November 27 2025"
    
    prompt = f"""Generate 3 {specificity} search queries for this stock anomaly:

Stock: {anomaly.ticker}
Price Change: {anomaly.price_change_percent:.2f}%
Volume Spike: {anomaly.volume_ratio:.1f}x

Iteration: {iteration + 1}/3
Example style: "{example}"

Focus areas:
- Earnings reports (beats/misses)
- SEC filings (8-K, 10-Q, 10-K)
- Analyst upgrades/downgrades
- Management changes (CEO, CFO resignations)
- Legal issues, investigations
- Major contracts (wins/losses)
- Product announcements, recalls

Requirements:
✓ Include stock ticker
✓ Include timeframe (November 2025, Q4 2025, etc.)
✓ Be search-engine friendly
✓ Target ROOT CAUSE, not symptoms
"""
    
    if previous_critique and not previous_critique.explanation_found:
        prompt += f"""
⚠️ PREVIOUS ATTEMPT FAILED!
Issue: {previous_critique.improvement_hint}

Generate MORE SPECIFIC queries this time!
"""
    
    response = llm.invoke(prompt)
    
    # Parse queries
    queries = []
    for line in response.content.strip().split('\n'):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('-')):
            query = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
            if query:
                queries.append(query)
    
    queries = queries[:3]
    
    logger.info(f"   Generated queries:")
    for i, q in enumerate(queries, 1):
        logger.info(f"     {i}. {q}")
    
    return {"search_queries": queries}


# Node 2: Execute REAL Tavily search!
def execute_real_search(state: InvestigationState) -> dict:
    """
    Execute real Tavily search
    THIS REPLACES MOCK SEARCH!
    """
    queries = state["search_queries"]
    
    logger.info(f"🌐 Tavily Search (Real API)")
    logger.info(f"   Executing {len(queries)} queries...")
    
    # Initialize Tavily
    search_tool = TavilySearchTool()
    
    # Execute all searches
    all_results = search_tool.search_multiple_queries(
        queries=queries,
        max_results_per_query=3
    )
    
    # Log summary
    total_results = sum(len(r.get('results', [])) for r in all_results.values())
    logger.info(f"   ✅ Retrieved {total_results} total results")
    
    return {"search_results": all_results}


# Node 3: Critique with real data
def critique_investigation(state: InvestigationState) -> dict:
    """Critic evaluates if we found root cause using REAL search results"""
    anomaly = state["anomaly"]
    queries = state["search_queries"]
    search_results = state["search_results"]
    iteration = state["iteration"]
    
    logger.info(f"🔍 Critic (Evaluating real search results)")
    
    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0.2,
        convert_system_message_to_human=True
    )
    
    llm_with_structure = llm.with_structured_output(InvestigationCritique)
    
    # Build comprehensive evidence from Tavily results
    evidence = []
    for query, result in search_results.items():
        evidence.append(f"\n🔎 Query: {query}")
        
        # Add AI answer if available
        if result.get('answer'):
            evidence.append(f"   📌 AI Summary: {result['answer']}")
        
        # Add top results
        for i, res in enumerate(result.get('results', [])[:2], 1):
            evidence.append(f"   {i}. {res.get('title', 'N/A')}")
            evidence.append(f"      {res.get('content', 'N/A')[:200]}")
            evidence.append(f"      Source: {res.get('url', 'N/A')}")
    
    evidence_text = "\n".join(evidence)
    
    critique_prompt = f"""You are an expert financial investigator evaluating search results.

ANOMALY:
{anomaly.ticker} dropped {abs(anomaly.price_change_percent):.1f}% with {anomaly.volume_ratio:.1f}x volume

SEARCH EVIDENCE:
{evidence_text}

EVALUATION CRITERIA:
1. Do results explain WHY the stock moved so dramatically?
2. Is the explanation SPECIFIC (not just "market volatility")?
3. Is it CREDIBLE (from reliable sources)?
4. Does it explain the MAGNITUDE ({abs(anomaly.price_change_percent):.1f}% drop)?

SCORING:
- explanation_found = True ONLY if clear root cause identified
- confidence = 0.0-1.0 based on evidence quality
- reasoning = Explain your judgment
- improvement_hint = If not found, suggest more specific query types

Examples of GOOD explanations:
✓ "Q3 earnings missed by 20%, revenue guidance cut"
✓ "CEO resigned amid fraud investigation, SEC filing"
✓ "Major client contract worth $500M cancelled"

Examples of BAD explanations:
✗ "General market selloff"
✗ "Tech sector weakness"
✗ "Investor sentiment"

Return structured critique.
"""
    
    critique = llm_with_structure.invoke(critique_prompt)
    
    logger.info(f"   Explanation Found: {critique.explanation_found}")
    logger.info(f"   Confidence: {critique.confidence:.0%}")
    logger.info(f"   Reasoning: {critique.reasoning[:100]}...")
    
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
    logger.info(f"🔄 Refining queries (Next attempt: {new_iteration + 1}/{settings.max_retries})")
    return {"iteration": new_iteration}


# Node 5: Final report
def generate_final_report(state: InvestigationState) -> dict:
    """Generate comprehensive investigation report"""
    anomaly = state["anomaly"]
    critique = state["critique"]
    iteration = state["iteration"]
    search_results = state["search_results"]
    
    logger.info("\n" + "="*60)
    logger.info("📊 FINAL INVESTIGATION REPORT")
    logger.info("="*60)
    logger.info(f"Anomaly: {anomaly.describe()}")
    logger.info(f"Iterations: {iteration + 1}/{settings.max_retries}")
    logger.info(f"Status: {'✅ SOLVED' if critique.explanation_found else '⚠️ UNSOLVED'}")
    logger.info(f"Confidence: {critique.confidence:.0%}")
    logger.info(f"\n📝 Conclusion:")
    logger.info(f"   {critique.reasoning}")
    
    # Show top evidence
    logger.info(f"\n🔍 Key Evidence:")
    for query, result in list(search_results.items())[:2]:
        if result.get('answer'):
            logger.info(f"   • {result['answer'][:150]}...")
    
    logger.info("="*60)
    
    return {}


# Conditional edge
def should_continue_investigation(state: InvestigationState) -> Literal["retry", "report"]:
    """Decide: continue or finish?"""
    if state["investigation_complete"]:
        return "report"
    else:
        return "retry"


# Create graph
def create_investigation_graph_v3():
    """Complete investigation with REAL Tavily search"""
    
    workflow = StateGraph(InvestigationState)
    
    # Add nodes
    workflow.add_node("generate_queries", generate_investigation_queries)
    workflow.add_node("search", execute_real_search)  # REAL SEARCH!
    workflow.add_node("critique", critique_investigation)
    workflow.add_node("increment", increment_iteration)
    workflow.add_node("report", generate_final_report)
    
    # Add edges
    workflow.add_edge(START, "generate_queries")
    workflow.add_edge("generate_queries", "search")
    workflow.add_edge("search", "critique")
    
    # Self-correction loop
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
def test_investigation_v3():
    """Test with real Tavily search"""
    
    logger.info("\n" + "="*60)
    logger.info("🧪 TESTING INVESTIGATION WITH REAL TAVILY SEARCH")
    logger.info("="*60)
    
    app = create_investigation_graph_v3()
    
    # Test with real anomaly
    test_anomaly = StockAnomaly(
        ticker="AAPL",
        price=277.47,
        price_change_percent=-12.5,  # Simulated anomaly
        volume=50000000,
        volume_ratio=5.2
    )
    
    initial_state = {
        "anomaly": test_anomaly,
        "search_queries": [],
        "search_results": {},
        "critique": None,
        "iteration": 0,
        "investigation_complete": False
    }
    
    result = app.invoke(initial_state, {"recursion_limit": 50})
    
    logger.info("\n✅ Investigation complete!")


if __name__ == "__main__":
    test_investigation_v3()

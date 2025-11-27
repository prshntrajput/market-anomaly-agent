

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from src.models.schemas import StockAnomaly
from src.tools.tavily_search import TavilySearchTool
from src.chains.advanced_query_generator import AdvancedQueryGenerator
from src.chains.experts_role_prompts import ExpertRolePrompts, ExpertRole
from src.chains.meta_prompt_optimizer import MetaPromptOptimizer
from src.utils.config import settings
from src.utils.logger import logger


# ============================================================
# MODELS
# ============================================================

class InvestigationCritique(BaseModel):
    """Critique of investigation quality"""
    explanation_found: bool = Field(description="Did we find root cause?")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(description="Why this score?")
    improvement_hint: str = Field(description="How to improve queries?")


class InvestigationState(TypedDict):
    """Complete investigation state"""
    anomaly: StockAnomaly
    search_queries: list[str]
    search_results: dict
    critique: InvestigationCritique | None
    iteration: int
    investigation_complete: bool


# ============================================================
# NODES
# ============================================================

def generate_advanced_queries(state: InvestigationState) -> dict:
    """
    Node 1: Use advanced techniques for query generation
    - Iteration 0: Chain-of-Thought reasoning
    - Iteration 1: Multi-expert perspectives
    - Iteration 2+: Meta-prompt optimization
    """
    anomaly = state["anomaly"]
    iteration = state["iteration"]
    previous_critique = state.get("critique")
    
    logger.info(f"🧠 Advanced Query Generation (Iteration {iteration + 1}/{settings.max_retries})")
    
    try:
        if iteration == 0:
            # First attempt: Use Chain-of-Thought
            logger.info("   Strategy: Chain-of-Thought reasoning")
            generator = AdvancedQueryGenerator()
            result = generator.generate_with_cot(anomaly, iteration)
            queries = result.final_queries
            
        elif iteration == 1:
            # Second attempt: Use Expert Roles
            logger.info("   Strategy: Multi-expert perspectives")
            expert_system = ExpertRolePrompts()
            
            # Get queries from most relevant experts
            earnings_queries = expert_system.generate_expert_queries(
                anomaly, ExpertRole.EARNINGS_ANALYST
            )
            legal_queries = expert_system.generate_expert_queries(
                anomaly, ExpertRole.LEGAL_EXPERT
            )
            
            # Combine top queries from each expert
            queries = [
                earnings_queries[0] if earnings_queries else f"{anomaly.ticker} earnings report Q4 2025",
                legal_queries[0] if legal_queries else f"{anomaly.ticker} SEC filing November 2025",
                earnings_queries[1] if len(earnings_queries) > 1 else f"{anomaly.ticker} analyst downgrade 2025"
            ]
            
        else:
            # Third attempt: Meta-optimization
            logger.info("   Strategy: Meta-prompt optimization")
            optimizer = MetaPromptOptimizer()
            
            # Use previous queries as base
            original_queries = state.get("search_queries", [
                f"{anomaly.ticker} news today",
                f"{anomaly.ticker} stock drop",
                f"{anomaly.ticker} earnings"
            ])
            
            queries = optimizer.optimize_queries(
                original_queries,
                anomaly,
                search_failed=True
            )
        
        logger.info("   Generated queries:")
        for i, q in enumerate(queries, 1):
            logger.info(f"     {i}. {q}")
        
        return {"search_queries": queries}
        
    except Exception as e:
        logger.error(f"   ❌ Query generation failed: {e}")
        # Fallback to simple queries
        fallback_queries = [
            f"{anomaly.ticker} earnings report Q4 2025 miss",
            f"{anomaly.ticker} SEC filing November 2025",
            f"{anomaly.ticker} analyst downgrade November 2025"
        ]
        logger.info(f"   Using fallback queries")
        return {"search_queries": fallback_queries}


def execute_real_search(state: InvestigationState) -> dict:
    """
    Node 2: Execute real Tavily search
    """
    queries = state["search_queries"]
    
    logger.info(f"🌐 Tavily Search (Real API)")
    logger.info(f"   Executing {len(queries)} queries...")
    
    try:
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
        
    except Exception as e:
        logger.error(f"   ❌ Search failed: {e}")
        return {"search_results": {}}


def critique_investigation(state: InvestigationState) -> dict:
    """
    Node 3: Critique investigation quality using real search results
    """
    anomaly = state["anomaly"]
    queries = state["search_queries"]
    search_results = state["search_results"]
    iteration = state["iteration"]
    
    logger.info(f"🔍 Critic (Evaluating real search results)")
    
    try:
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
        
        evidence_text = "\n".join(evidence) if evidence else "No search results found."
        
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
        
    except Exception as e:
        logger.error(f"   ❌ Critique failed: {e}")
        # Return default critique
        return {
            "critique": InvestigationCritique(
                explanation_found=False,
                confidence=0.0,
                reasoning=f"Critique failed: {str(e)}",
                improvement_hint="Try more specific queries with exact dates and events"
            ),
            "investigation_complete": iteration >= settings.max_retries - 1
        }


def increment_iteration(state: InvestigationState) -> dict:
    """
    Node 4: Increment iteration counter
    """
    new_iteration = state["iteration"] + 1
    logger.info(f"🔄 Refining queries (Next attempt: {new_iteration + 1}/{settings.max_retries})")
    return {"iteration": new_iteration}


def generate_final_report(state: InvestigationState) -> dict:
    """
    Node 5: Generate comprehensive investigation report
    """
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
    if search_results:
        logger.info(f"\n🔍 Key Evidence:")
        evidence_count = 0
        for query, result in list(search_results.items())[:2]:
            if result.get('answer'):
                logger.info(f"   • {result['answer'][:150]}...")
                evidence_count += 1
        
        if evidence_count == 0:
            logger.info(f"   • No strong evidence found in search results")
    
    logger.info("="*60)
    
    return {}


# ============================================================
# CONDITIONAL EDGES
# ============================================================

def should_continue_investigation(state: InvestigationState) -> Literal["retry", "report"]:
    """
    Conditional edge: Decide whether to continue or finish investigation
    """
    if state["investigation_complete"]:
        return "report"
    else:
        return "retry"


# ============================================================
# GRAPH CREATION
# ============================================================

def create_investigation_graph_v4():
    """
    Create complete investigation graph with ADVANCED query generation
    
    Flow:
    1. Generate advanced queries (CoT, Expert Roles, or Meta-optimization)
    2. Execute Tavily search
    3. Critique results
    4. If not solved and retries left -> increment and retry
    5. If solved or max retries -> generate final report
    """
    
    workflow = StateGraph(InvestigationState)
    
    # Add all nodes
    workflow.add_node("generate_queries", generate_advanced_queries)
    workflow.add_node("search", execute_real_search)
    workflow.add_node("critique", critique_investigation)
    workflow.add_node("increment", increment_iteration)
    workflow.add_node("report", generate_final_report)
    
    # Add edges
    workflow.add_edge(START, "generate_queries")
    workflow.add_edge("generate_queries", "search")
    workflow.add_edge("search", "critique")
    
    # Conditional edge - THE SELF-CORRECTION LOOP
    workflow.add_conditional_edges(
        "critique",
        should_continue_investigation,
        {
            "retry": "increment",
            "report": "report"
        }
    )
    
    # Complete the loop
    workflow.add_edge("increment", "generate_queries")
    workflow.add_edge("report", END)
    
    return workflow.compile()


# ============================================================
# TEST FUNCTION
# ============================================================

def test_investigation_v4():
    """Test complete investigation with advanced query generation"""
    
    logger.info("\n" + "="*60)
    logger.info("🧪 TESTING INVESTIGATION V4 (ADVANCED QUERIES)")
    logger.info("="*60)
    
    app = create_investigation_graph_v4()
    
    # Test with simulated anomaly
    test_anomaly = StockAnomaly(
        ticker="MSFT",
        price=485.49,
        price_change_percent=-14.8,  # Simulated significant drop
        volume=65000000,
        volume_ratio=4.8
    )
    
    logger.info(f"\n🚨 Test Anomaly: {test_anomaly.describe()}")
    
    initial_state = {
        "anomaly": test_anomaly,
        "search_queries": [],
        "search_results": {},
        "critique": None,
        "iteration": 0,
        "investigation_complete": False
    }
    
    try:
        result = app.invoke(initial_state, {"recursion_limit": 50})
        
        logger.info("\n✅ Investigation complete!")
        logger.info(f"\nFinal State Summary:")
        logger.info(f"  - Solved: {result['critique'].explanation_found}")
        logger.info(f"  - Confidence: {result['critique'].confidence:.0%}")
        logger.info(f"  - Iterations Used: {result['iteration'] + 1}")
        logger.info(f"  - Total Queries Executed: {len(result['search_queries'])}")
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")


if __name__ == "__main__":
    test_investigation_v4()

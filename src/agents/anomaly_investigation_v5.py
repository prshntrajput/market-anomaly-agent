"""Investigation v5 - With Advanced Evidence Evaluation & Reporting - FIXED"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from src.models.schemas import StockAnomaly
from src.tools.tavily_search import TavilySearchTool
from src.chains.advanced_query_generator import AdvancedQueryGenerator
from src.chains.experts_role_prompts import ExpertRolePrompts, ExpertRole
from src.chains.meta_prompt_optimizer import MetaPromptOptimizer
from src.chains.evidence_evaluator import AdvancedEvidenceEvaluator, EvidenceEvaluation
from src.utils.report_generator import InvestigationReportGenerator
from src.utils.config import settings
from src.utils.logger import logger
from pathlib import Path


# ============================================================
# STATE
# ============================================================

class InvestigationState(TypedDict):
    """Complete investigation state with advanced evaluation"""
    anomaly: StockAnomaly
    search_queries: list[str]
    search_results: dict
    evidence_evaluation: EvidenceEvaluation | None
    iteration: int
    investigation_complete: bool
    final_report: str


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def validate_and_truncate_queries(queries: list[str], max_length: int = 250) -> list[str]:
    """
    Validate and truncate queries to avoid Tavily length errors
    
    Args:
        queries: List of raw queries
        max_length: Maximum query length (Tavily limit is 400)
    
    Returns:
        List of validated queries
    """
    validated = []
    
    for query in queries:
        # Remove markdown formatting
        query = query.replace('**', '').replace('*', '').strip()
        
        # Remove leading numbers and bullets
        if query and (query[0].isdigit() or query[0] in ['-', '•', '▪']):
            if '.' in query[:5]:
                query = query.split('.', 1)[1].strip()
            else:
                query = query[1:].strip()
        
        # Remove quotes
        query = query.strip('"').strip("'").strip()
        
        # Truncate if too long (cut at word boundary)
        if len(query) > max_length:
            query = query[:max_length].rsplit(' ', 1)[0]
        
        # Only add if reasonable length
        if 15 < len(query) <= max_length:
            validated.append(query)
    
    return validated


# ============================================================
# NODES
# ============================================================

def generate_advanced_queries(state: InvestigationState) -> dict:
    """
    Node 1: Generate queries using advanced techniques - FIXED
    """
    anomaly = state["anomaly"]
    iteration = state["iteration"]
    previous_evaluation = state.get("evidence_evaluation")
    
    logger.info(f"🧠 Advanced Query Generation (Iteration {iteration + 1}/{settings.max_retries})")
    
    try:
        if iteration == 0:
            # First attempt: Chain-of-Thought
            logger.info("   Strategy: Chain-of-Thought reasoning")
            generator = AdvancedQueryGenerator()
            result = generator.generate_with_cot(anomaly, iteration)
            queries = result.final_queries
            
        elif iteration == 1:
            # Second attempt: Expert Roles
            logger.info("   Strategy: Multi-expert perspectives")
            expert_system = ExpertRolePrompts()
            
            earnings_queries = expert_system.generate_expert_queries(
                anomaly, ExpertRole.EARNINGS_ANALYST
            )
            legal_queries = expert_system.generate_expert_queries(
                anomaly, ExpertRole.LEGAL_EXPERT
            )
            
            queries = [
                earnings_queries[0] if earnings_queries else f"{anomaly.ticker} earnings Q4 2025",
                legal_queries[0] if legal_queries else f"{anomaly.ticker} SEC filing",
                earnings_queries[1] if len(earnings_queries) > 1 else f"{anomaly.ticker} guidance"
            ]
            
        else:
            # Third attempt: Meta-optimization
            logger.info("   Strategy: Meta-prompt optimization")
            optimizer = MetaPromptOptimizer()
            
            original_queries = state.get("search_queries", [
                f"{anomaly.ticker} news November 2025",
                f"{anomaly.ticker} earnings Q3 2025",
                f"{anomaly.ticker} analyst rating 2025"
            ])
            
            queries = optimizer.optimize_queries(
                original_queries,
                anomaly,
                search_failed=True
            )
        
        # FIXED: Validate and truncate queries
        queries = validate_and_truncate_queries(queries, max_length=250)
        
        # Ensure we have at least 3 queries
        while len(queries) < 3:
            queries.append(f"{anomaly.ticker} stock drop November 2025")
        
        queries = queries[:3]
        
        logger.info("   Generated queries:")
        for i, q in enumerate(queries, 1):
            logger.info(f"     {i}. {q} ({len(q)} chars)")
        
        return {"search_queries": queries}
        
    except Exception as e:
        logger.error(f"   ❌ Query generation failed: {e}")
        fallback_queries = [
            f"{anomaly.ticker} earnings report November 2025",
            f"{anomaly.ticker} SEC filing November 2025",
            f"{anomaly.ticker} analyst rating November 2025"
        ]
        return {"search_queries": fallback_queries}


def execute_real_search(state: InvestigationState) -> dict:
    """
    Node 2: Execute Tavily search
    """
    queries = state["search_queries"]
    
    logger.info(f"🌐 Tavily Search")
    logger.info(f"   Executing {len(queries)} queries...")
    
    try:
        search_tool = TavilySearchTool()
        all_results = search_tool.search_multiple_queries(
            queries=queries,
            max_results_per_query=3
        )
        
        total_results = sum(len(r.get('results', [])) for r in all_results.values())
        logger.info(f"   ✅ Retrieved {total_results} total results")
        
        return {"search_results": all_results}
        
    except Exception as e:
        logger.error(f"   ❌ Search failed: {e}")
        return {"search_results": {}}


def evaluate_evidence_advanced(state: InvestigationState) -> dict:
    """
    Node 3: Advanced evidence evaluation
    """
    anomaly = state["anomaly"]
    search_results = state["search_results"]
    iteration = state["iteration"]
    
    logger.info(f"🔬 Advanced Evidence Evaluation")
    
    try:
        evaluator = AdvancedEvidenceEvaluator()
        evaluation = evaluator.evaluate_evidence(anomaly, search_results)
        
        logger.info(f"   ✅ Evaluation complete")
        logger.info(f"   Explanation Found: {evaluation.explanation_found}")
        logger.info(f"   Quality: {evaluation.explanation_quality}")
        logger.info(f"   Confidence: {evaluation.confidence:.0%}")
        logger.info(f"   Root Cause: {evaluation.root_cause[:100]}...")
        
        investigation_complete = (
            (evaluation.explanation_found and evaluation.confidence >= 0.7) or
            iteration >= settings.max_retries - 1
        )
        
        return {
            "evidence_evaluation": evaluation,
            "investigation_complete": investigation_complete
        }
        
    except Exception as e:
        logger.error(f"   ❌ Evaluation failed: {e}")
        
        # Create minimal evaluation
        from src.chains.evidence_evaluator import EvidenceEvaluation
        
        minimal_evaluation = EvidenceEvaluation(
            evidence_items=[],
            overall_credibility=0.0,
            overall_relevance=0.0,
            explanation_found=False,
            explanation_quality="poor",
            root_cause="Evaluation failed",
            confidence=0.0,
            reasoning=f"Error: {str(e)}",
            missing_info=["Evaluation system error"]
        )
        
        return {
            "evidence_evaluation": minimal_evaluation,
            "investigation_complete": iteration >= settings.max_retries - 1
        }


def increment_iteration(state: InvestigationState) -> dict:
    """
    Node 4: Increment iteration
    """
    new_iteration = state["iteration"] + 1
    logger.info(f"🔄 Refining approach (Attempt {new_iteration + 1}/{settings.max_retries})")
    return {"iteration": new_iteration}


def generate_comprehensive_report(state: InvestigationState) -> dict:
    """
    Node 5: Generate professional investigation report
    """
    anomaly = state["anomaly"]
    evaluation = state["evidence_evaluation"]
    queries = state["search_queries"]
    iteration = state["iteration"]
    
    logger.info(f"\n{'='*60}")
    logger.info("📊 GENERATING COMPREHENSIVE REPORT")
    logger.info(f"{'='*60}")
    
    try:
        report_generator = InvestigationReportGenerator()
        
        # Generate markdown report
        report = report_generator.generate_markdown_report(
            anomaly=anomaly,
            evaluation=evaluation,
            queries_used=queries,
            iterations=iteration + 1
        )
        
        # Save report to file
        Path("logs").mkdir(exist_ok=True)
        filepath = report_generator.save_report(report, anomaly.ticker)
        
        logger.info(f"✅ Report saved to: {filepath}")
        
        # Log summary
        logger.info(f"\n📋 Investigation Summary:")
        logger.info(f"   Anomaly: {anomaly.describe()}")
        logger.info(f"   Status: {'✅ SOLVED' if evaluation.explanation_found else '⚠️ UNSOLVED'}")
        logger.info(f"   Confidence: {evaluation.confidence:.0%}")
        logger.info(f"   Quality: {evaluation.explanation_quality.upper()}")
        logger.info(f"   Root Cause: {evaluation.root_cause}")
        logger.info(f"   Iterations: {iteration + 1}/{settings.max_retries}")
        logger.info(f"   Evidence Items: {len(evaluation.evidence_items)}")
        logger.info(f"   Source Credibility: {evaluation.overall_credibility:.0%}")
        logger.info(f"   Content Relevance: {evaluation.overall_relevance:.0%}")
        
        logger.info(f"{'='*60}\n")
        
        return {"final_report": report}
        
    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}")
        return {"final_report": f"Report generation failed: {str(e)}"}


# ============================================================
# CONDITIONAL EDGES
# ============================================================

def should_continue_investigation(state: InvestigationState) -> Literal["retry", "report"]:
    """
    Conditional edge: Continue investigation or generate report?
    """
    if state["investigation_complete"]:
        return "report"
    else:
        return "retry"


# ============================================================
# GRAPH CREATION
# ============================================================

def create_investigation_graph_v5():
    """
    Create complete investigation graph v5 - FIXED
    """
    
    workflow = StateGraph(InvestigationState)
    
    # Add nodes
    workflow.add_node("generate_queries", generate_advanced_queries)
    workflow.add_node("search", execute_real_search)
    workflow.add_node("evaluate", evaluate_evidence_advanced)
    workflow.add_node("increment", increment_iteration)
    workflow.add_node("report", generate_comprehensive_report)
    
    # Add edges
    workflow.add_edge(START, "generate_queries")
    workflow.add_edge("generate_queries", "search")
    workflow.add_edge("search", "evaluate")
    
    # Self-correction loop
    workflow.add_conditional_edges(
        "evaluate",
        should_continue_investigation,
        {
            "retry": "increment",
            "report": "report"
        }
    )
    
    workflow.add_edge("increment", "generate_queries")
    workflow.add_edge("report", END)
    
    return workflow.compile()


# ============================================================
# TEST FUNCTION
# ============================================================

def test_investigation_v5():
    """Test complete v5 investigation system"""
    
    logger.info("\n" + "="*60)
    logger.info("🧪 TESTING INVESTIGATION V5 (FIXED VERSION)")
    logger.info("="*60)
    
    app = create_investigation_graph_v5()
    
    # Test anomaly
    test_anomaly = StockAnomaly(
        ticker="MSFT",
        price=485.49,
        price_change_percent=-12.8,
        volume=65000000,
        volume_ratio=4.8
    )
    
    logger.info(f"\n🚨 Test Anomaly: {test_anomaly.describe()}")
    
    initial_state = {
        "anomaly": test_anomaly,
        "search_queries": [],
        "search_results": {},
        "evidence_evaluation": None,
        "iteration": 0,
        "investigation_complete": False,
        "final_report": ""
    }
    
    try:
        result = app.invoke(initial_state, {"recursion_limit": 50})
        
        logger.info("\n" + "="*60)
        logger.info("✅ INVESTIGATION V5 TEST COMPLETE")
        logger.info("="*60)
        logger.info(f"Final Status: {'SOLVED' if result['evidence_evaluation'].explanation_found else 'UNSOLVED'}")
        logger.info(f"Confidence: {result['evidence_evaluation'].confidence:.0%}")
        logger.info(f"Iterations Used: {result['iteration'] + 1}")
        logger.info(f"Report Length: {len(result['final_report'])} characters")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    test_investigation_v5()

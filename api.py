"""FastAPI REST API for Market Anomaly Detection Agent - UPDATED"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import uuid

from src.tools.advanced_anomaly_detector import AdvancedAnomalyDetector
from src.agents.anomaly_investigation_v5 import create_investigation_graph_v5, InvestigationState
from src.models.schemas import StockAnomaly
from src.utils.logger import logger

app = FastAPI(
    title="Market Anomaly Detection API",
    description="AI-powered market anomaly detection and investigation",
    version="1.0.0"
)

# Enable CORS for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
investigations_store: Dict[str, dict] = {}

# Request/Response Models
class ScanRequest(BaseModel):
    tickers: List[str]

class StockAnalysis(BaseModel):
    """Analysis for any stock (anomaly or normal)"""
    ticker: str
    price: float
    price_change_percent: float
    volume: int
    volume_ratio: float
    volatility: float
    rsi: float
    timestamp: str
    anomaly_score: int
    is_anomaly: bool
    severity: Optional[str] = None

class ScanResponse(BaseModel):
    """Complete scan response with all stocks analyzed"""
    total_scanned: int
    anomalies_found: int
    stocks_analyzed: List[StockAnalysis]

class AnomalyResponse(BaseModel):
    ticker: str
    price: float
    price_change_percent: float
    volume: int
    volume_ratio: float
    timestamp: str
    anomaly_score: int
    severity: str

class InvestigationStatusResponse(BaseModel):
    investigation_id: str
    ticker: str
    status: str
    created_at: str
    updated_at: str
    explanation_found: Optional[bool] = None
    confidence: Optional[float] = None
    root_cause: Optional[str] = None
    quality: Optional[str] = None

# Endpoints

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "Market Anomaly Detection API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/scan", response_model=ScanResponse)
async def scan_watchlist(request: ScanRequest):
    """
    Scan multiple stocks and return analysis for ALL stocks
    """
    logger.info(f"Scanning watchlist: {request.tickers}")
    
    detector = AdvancedAnomalyDetector()
    stocks_analyzed = []
    anomalies_count = 0
    
    for ticker in request.tickers:
        try:
            # Get detailed analysis (we need to modify detector to return this)
            analysis_data = detector.analyze_stock_detailed(ticker)
            
            if analysis_data:
                stocks_analyzed.append(analysis_data)
                if analysis_data.is_anomaly:
                    anomalies_count += 1
                    
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            continue
    
    logger.info(f"Analyzed {len(stocks_analyzed)} stocks, found {anomalies_count} anomalies")
    
    return ScanResponse(
        total_scanned=len(stocks_analyzed),
        anomalies_found=anomalies_count,
        stocks_analyzed=stocks_analyzed
    )

@app.post("/investigate/{ticker}")
async def start_investigation(ticker: str, background_tasks: BackgroundTasks):
    """Start investigation for a specific ticker"""
    logger.info(f"Starting investigation for {ticker}")
    
    detector = AdvancedAnomalyDetector()
    
    try:
        anomaly = detector.check_for_anomaly(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomaly: {str(e)}")
    
    if not anomaly:
        raise HTTPException(status_code=404, detail=f"No anomaly detected for {ticker}")
    
    investigation_id = str(uuid.uuid4())
    
    investigations_store[investigation_id] = {
        "investigation_id": investigation_id,
        "ticker": ticker,
        "status": "pending",
        "anomaly": {
            "ticker": anomaly.ticker,
            "price": anomaly.price,
            "price_change_percent": anomaly.price_change_percent,
            "volume": anomaly.volume,
            "volume_ratio": anomaly.volume_ratio,
            "timestamp": anomaly.timestamp.isoformat()
        },
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    background_tasks.add_task(run_investigation_task, investigation_id, anomaly)
    
    return {
        "investigation_id": investigation_id,
        "ticker": ticker,
        "status": "started",
        "message": "Investigation started in background"
    }

async def run_investigation_task(investigation_id: str, anomaly: StockAnomaly):
    """Background task to run investigation"""
    try:
        investigations_store[investigation_id]["status"] = "in_progress"
        investigations_store[investigation_id]["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"Running investigation {investigation_id} for {anomaly.ticker}")
        
        investigation_app = create_investigation_graph_v5()
        
        result = investigation_app.invoke({
            "anomaly": anomaly,
            "search_queries": [],
            "search_results": {},
            "evidence_evaluation": None,
            "iteration": 0,
            "investigation_complete": False,
            "final_report": ""
        }, {"recursion_limit": 50})
        
        eval_result = result.get('evidence_evaluation')
        
        investigations_store[investigation_id].update({
            "status": "completed",
            "explanation_found": eval_result.explanation_found if eval_result else False,
            "confidence": eval_result.confidence if eval_result else 0.0,
            "root_cause": eval_result.root_cause if eval_result else "Unknown",
            "quality": eval_result.explanation_quality if eval_result else "poor",
            "reasoning": eval_result.reasoning if eval_result else "",
            "overall_credibility": eval_result.overall_credibility if eval_result else 0.0,
            "overall_relevance": eval_result.overall_relevance if eval_result else 0.0,
            "iterations": result.get('iteration', 0) + 1,
            "queries_used": result.get('search_queries', []),
            "report": result.get('final_report', ''),
            "updated_at": datetime.now().isoformat()
        })
        
        logger.info(f"Investigation {investigation_id} completed")
        
    except Exception as e:
        logger.error(f"Investigation {investigation_id} failed: {e}")
        investigations_store[investigation_id].update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.now().isoformat()
        })

@app.get("/investigation/{investigation_id}", response_model=InvestigationStatusResponse)
async def get_investigation_status(investigation_id: str):
    """Get investigation status and results"""
    if investigation_id not in investigations_store:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    data = investigations_store[investigation_id]
    
    return InvestigationStatusResponse(
        investigation_id=data["investigation_id"],
        ticker=data["ticker"],
        status=data["status"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        explanation_found=data.get("explanation_found"),
        confidence=data.get("confidence"),
        root_cause=data.get("root_cause"),
        quality=data.get("quality")
    )

@app.get("/investigation/{investigation_id}/details")
async def get_investigation_details(investigation_id: str):
    """Get complete investigation details"""
    if investigation_id not in investigations_store:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    return investigations_store[investigation_id]

@app.get("/investigations")
async def list_investigations():
    """List all investigations"""
    investigations_list = [
        {
            "investigation_id": inv_id,
            "ticker": data["ticker"],
            "status": data["status"],
            "created_at": data["created_at"]
        }
        for inv_id, data in investigations_store.items()
    ]
    
    return {
        "total": len(investigations_list),
        "investigations": investigations_list
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

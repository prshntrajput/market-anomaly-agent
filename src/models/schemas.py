from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

# Stock ka data model
class StockAnomaly(BaseModel):
    """Market anomaly ko represent karta hai"""
    
    ticker: str = Field(..., description="Stock symbol (e.g., RELIANCE, TCS)")
    price: float = Field(..., gt=0, description="Current price (positive hona chahiye)")
    price_change_percent: float = Field(..., description="Price change %")
    volume: int = Field(..., gt=0, description="Trading volume")
    volume_ratio: float = Field(..., gt=1.0, description="Volume spike ratio (3x, 4x)")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Custom validation
    @field_validator('ticker')
    @classmethod
    def ticker_must_be_uppercase(cls, v: str) -> str:
        """Ticker UPPERCASE hona chahiye"""
        return v.upper()
    
    @field_validator('price_change_percent')
    @classmethod
    def significant_change(cls, v: float) -> float:
        """Anomaly sirf agar 10% se zyada drop/rise"""
        if abs(v) < 10.0:
            raise ValueError('Change 10% se kam hai - ye anomaly nahi hai!')
        return v
    
    def describe(self) -> str:
        """Human-readable description"""
        direction = "dropped" if self.price_change_percent < 0 else "surged"
        return (f"{self.ticker} {direction} {abs(self.price_change_percent):.2f}% "
                f"to ₹{self.price:.2f} with {self.volume_ratio:.1f}x volume")


# Search query ka model
class SearchQuery(BaseModel):
    """Generated search query"""
    query: str
    priority: int = Field(ge=1, le=5, description="1=highest, 5=lowest")
    search_type: str = Field(default="news", description="news/filing/analyst")


# Investigation result ka model
class InvestigationResult(BaseModel):
    """Final output after investigation"""
    anomaly: StockAnomaly
    queries_generated: List[SearchQuery]
    explanation_found: bool
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: Optional[str] = None
    sources: List[str] = []
    retries_taken: int = 0

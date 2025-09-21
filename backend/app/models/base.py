"""Base model classes."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model."""
    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Optional[dict] = None


class ErrorResponse(BaseResponse):
    """Error response model."""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "OK"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str = "SPM Backend API"
    version: str = "1.0.0"

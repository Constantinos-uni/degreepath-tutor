"""
Pydantic models for API request/response validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Unit(BaseModel):
    """Unit details model."""
    title: str = Field(..., description="The full title of the unit")
    prerequisites: List[str] = Field(..., description="List of prerequisite unit codes")
    corequisites: List[str] = Field(..., description="List of corequisite unit codes")
    incompatible_units: List[str] = Field(..., description="List of incompatible unit codes")
    credit_points: int = Field(..., description="Credit points value")
    year_level: int = Field(..., description="Year level (1, 2, 3, etc.)")
    learning_outcomes: List[str] = Field(..., description="List of learning outcomes")


class EligibilityRequest(BaseModel):
    """Request model for eligibility checking."""
    degree: str = Field(..., description="Student's enrolled degree")
    completed_units: List[str] = Field(..., description="List of completed unit codes")
    query_units: List[str] = Field(..., description="Unit codes to check eligibility for")


class EligibilityResponse(BaseModel):
    """Response model for eligibility checking."""
    eligible: bool = Field(..., description="Whether the student is eligible")
    missing_prerequisites: List[str] = Field(..., description="Missing prerequisite units")
    incompatible_units: List[str] = Field(..., description="Incompatible units already taken")
    errors: List[str] = Field(default=[], description="Any errors encountered")


class UnitResponse(BaseModel):
    """Response model for unit lookup."""
    unit_code: str = Field(..., description="The unit code")
    details: Unit = Field(..., description="Unit details")

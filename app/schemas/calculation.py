from __future__ import annotations

from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class CalculationType(str, Enum):
    """Enumeration of valid calculation types."""
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION = "division"


class CalculationBase(BaseModel):
    """Base schema with common fields for all calculation operations."""
    
    type: CalculationType = Field(..., description="Type of calculation operation")
    inputs: List[float] = Field(..., min_length=2, description="List of numeric inputs (minimum 2 required)")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        """Normalize type string to lowercase for case-insensitive matching."""
        if isinstance(v, str):
            return v.lower()
        return v

    @model_validator(mode="after")
    def validate_division_by_zero(self) -> "CalculationBase":
        """Prevent division by zero (LBYL approach).
        
        This validation happens at the schema level before the operation is attempted.
        """
        if self.type == CalculationType.DIVISION:
            if any(x == 0 for x in self.inputs[1:]):
                raise ValueError("Cannot divide by zero")
        return self


class CalculationCreate(CalculationBase):
    """Schema for creating a new calculation.
    
    Includes user_id to associate the calculation with a user.
    """
    user_id: Optional[UUID] = Field(None, description="Optional user ID to associate with this calculation")


class CalculationUpdate(BaseModel):
    """Schema for updating an existing calculation.
    
    All fields are optional to support partial updates.
    """
    type: Optional[CalculationType] = None
    inputs: Optional[List[float]] = Field(None, min_length=2)
    user_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v: Optional[str]) -> Optional[str]:
        """Normalize type string to lowercase."""
        if isinstance(v, str):
            return v.lower()
        return v

    @model_validator(mode="after")
    def validate_division_by_zero(self) -> "CalculationUpdate":
        """Prevent division by zero in updates."""
        if self.type == CalculationType.DIVISION and self.inputs:
            if any(x == 0 for x in self.inputs[1:]):
                raise ValueError("Cannot divide by zero")
        return self


class CalculationResponse(BaseModel):
    """Schema for reading calculation data.
    
    Includes computed fields like id and result.
    Does not inherit validation from CalculationBase to allow division by zero in responses.
    """
    id: UUID = Field(..., description="Unique identifier for the calculation")
    type: CalculationType = Field(..., description="Type of calculation operation")
    inputs: List[float] = Field(..., description="List of numeric inputs")
    user_id: Optional[UUID] = Field(None, description="User who created this calculation")
    result: Optional[float] = Field(None, description="Computed result of the calculation")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        """Normalize type string to lowercase for case-insensitive matching."""
        if isinstance(v, str):
            return v.lower()
        return v

    @classmethod
    def from_orm_with_result(cls, calculation) -> "CalculationResponse":
        """Create response from ORM object, computing the result.
        
        Args:
            calculation: Calculation ORM instance
            
        Returns:
            CalculationResponse with computed result
        """
        try:
            result = calculation.get_result()
        except (ValueError, ZeroDivisionError):
            result = None
            
        return cls(
            id=calculation.id,
            type=calculation.type,
            inputs=calculation.inputs,
            user_id=calculation.user_id,
            result=result
        )

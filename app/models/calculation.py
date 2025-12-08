from __future__ import annotations

import uuid
from typing import Optional, List, Union
from abc import abstractmethod

from sqlalchemy import Column, String, ForeignKey, ARRAY, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Calculation(Base):
    """Polymorphic base model for calculations using single-table inheritance.
    
    This is the base class that defines the common interface for all calculation types.
    SQLAlchemy will automatically instantiate the correct subclass based on the 'type' discriminator.
    
    Polymorphic Pattern:
    - Single table stores all calculation types
    - 'type' column determines which subclass to instantiate
    - Factory method creates appropriate subclass
    - Each subclass implements get_result() differently
    """

    __tablename__ = "calculations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    inputs = Column(ARRAY(Float), nullable=False)

    # Polymorphic configuration
    __mapper_args__ = {
        "polymorphic_identity": "calculation",
        "polymorphic_on": type,
    }

    # Relationship to User
    user = relationship("User", back_populates="calculations")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id}, inputs={self.inputs})>"

    @abstractmethod
    def get_result(self) -> float:
        """Calculate and return the result. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement get_result()")

    @classmethod
    def create(cls, calc_type: str, user_id: Optional[UUID], inputs: List[float]) -> "Calculation":
        """Factory method to create the appropriate calculation subclass.
        
        Args:
            calc_type: Type of calculation ('addition', 'subtraction', 'multiplication', 'division')
            user_id: Optional user ID
            inputs: List of numeric inputs
            
        Returns:
            Instance of appropriate Calculation subclass
            
        Raises:
            ValueError: If calc_type is invalid
        """
        calc_type_lower = calc_type.lower()
        
        if calc_type_lower == "addition":
            return Addition(user_id=user_id, inputs=inputs)
        elif calc_type_lower == "subtraction":
            return Subtraction(user_id=user_id, inputs=inputs)
        elif calc_type_lower == "multiplication":
            return Multiplication(user_id=user_id, inputs=inputs)
        elif calc_type_lower == "division":
            return Division(user_id=user_id, inputs=inputs)
        else:
            raise ValueError(f"Invalid calculation type: {calc_type}")


class Addition(Calculation):
    """Addition calculation: sum all inputs."""

    __mapper_args__ = {
        "polymorphic_identity": "addition",
    }

    def get_result(self) -> float:
        """Sum all input values."""
        return sum(self.inputs)


class Subtraction(Calculation):
    """Subtraction calculation: first input minus all subsequent inputs."""

    __mapper_args__ = {
        "polymorphic_identity": "subtraction",
    }

    def get_result(self) -> float:
        """Subtract all subsequent inputs from the first input."""
        if not self.inputs:
            return 0.0
        result = self.inputs[0]
        for value in self.inputs[1:]:
            result -= value
        return result


class Multiplication(Calculation):
    """Multiplication calculation: product of all inputs."""

    __mapper_args__ = {
        "polymorphic_identity": "multiplication",
    }

    def get_result(self) -> float:
        """Multiply all input values."""
        if not self.inputs:
            return 0.0
        result = 1.0
        for value in self.inputs:
            result *= value
        return result


class Division(Calculation):
    """Division calculation: first input divided by all subsequent inputs."""

    __mapper_args__ = {
        "polymorphic_identity": "division",
    }

    def get_result(self) -> float:
        """Divide the first input by all subsequent inputs.
        
        Raises:
            ValueError: If any divisor is zero (EAFP approach)
        """
        if not self.inputs:
            return 0.0
        result = self.inputs[0]
        for value in self.inputs[1:]:
            if value == 0:
                raise ValueError("Cannot divide by zero.")
            result /= value
        return result

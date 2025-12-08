"""
Unit tests for Pydantic calculation schemas.

These tests verify:
1. Valid data acceptance
2. Invalid data rejection
3. Type validation and normalization
4. Division by zero validation (LBYL)
5. Cross-field validation
6. Edge cases
"""

import pytest
from pydantic import ValidationError
from uuid import uuid4

from app.schemas.calculation import (
    CalculationType,
    CalculationBase,
    CalculationCreate,
    CalculationUpdate,
    CalculationResponse,
)


class TestCalculationType:
    """Test the CalculationType enum."""

    def test_enum_values(self):
        """Test all enum values are defined correctly."""
        assert CalculationType.ADDITION == "addition"
        assert CalculationType.SUBTRACTION == "subtraction"
        assert CalculationType.MULTIPLICATION == "multiplication"
        assert CalculationType.DIVISION == "division"

    def test_enum_from_string(self):
        """Test creating enum from string."""
        assert CalculationType("addition") == CalculationType.ADDITION
        assert CalculationType("division") == CalculationType.DIVISION


class TestCalculationBase:
    """Test the CalculationBase schema."""

    def test_valid_addition(self):
        """Test valid addition schema."""
        calc = CalculationBase(type="addition", inputs=[1.0, 2.0, 3.0])
        assert calc.type == CalculationType.ADDITION
        assert calc.inputs == [1.0, 2.0, 3.0]

    def test_valid_subtraction(self):
        """Test valid subtraction schema."""
        calc = CalculationBase(type="subtraction", inputs=[10.0, 3.0])
        assert calc.type == CalculationType.SUBTRACTION

    def test_valid_multiplication(self):
        """Test valid multiplication schema."""
        calc = CalculationBase(type="multiplication", inputs=[2.0, 3.0])
        assert calc.type == CalculationType.MULTIPLICATION

    def test_valid_division(self):
        """Test valid division schema."""
        calc = CalculationBase(type="division", inputs=[10.0, 2.0])
        assert calc.type == CalculationType.DIVISION

    def test_type_normalization_lowercase(self):
        """Test type is normalized to lowercase."""
        calc = CalculationBase(type="ADDITION", inputs=[1.0, 2.0])
        assert calc.type == CalculationType.ADDITION

    def test_type_normalization_mixed_case(self):
        """Test type normalization with mixed case."""
        calc = CalculationBase(type="DiViSiOn", inputs=[10.0, 2.0])
        assert calc.type == CalculationType.DIVISION

    def test_minimum_two_inputs_required(self):
        """Test that at least 2 inputs are required."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationBase(type="addition", inputs=[1.0])
        
        assert "at least 2 items" in str(exc_info.value).lower()

    def test_empty_inputs_rejected(self):
        """Test that empty inputs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationBase(type="addition", inputs=[])
        
        assert "at least 2 items" in str(exc_info.value).lower()

    def test_division_by_zero_rejected(self):
        """Test division by zero is rejected (LBYL)."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationBase(type="division", inputs=[10.0, 0.0])
        
        assert "Cannot divide by zero" in str(exc_info.value)

    def test_division_by_zero_in_middle(self):
        """Test division by zero is caught even in middle of inputs."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationBase(type="division", inputs=[10.0, 2.0, 0.0, 5.0])
        
        assert "Cannot divide by zero" in str(exc_info.value)

    def test_division_first_element_can_be_zero(self):
        """Test that first element can be zero (only divisors are checked)."""
        calc = CalculationBase(type="division", inputs=[0.0, 2.0])
        assert calc.inputs[0] == 0.0

    def test_invalid_type_rejected(self):
        """Test invalid operation type is rejected."""
        with pytest.raises(ValidationError):
            CalculationBase(type="invalid", inputs=[1.0, 2.0])


class TestCalculationCreate:
    """Test the CalculationCreate schema."""

    def test_create_without_user_id(self):
        """Test creating calculation without user_id."""
        calc = CalculationCreate(type="addition", inputs=[1.0, 2.0])
        assert calc.user_id is None

    def test_create_with_user_id(self):
        """Test creating calculation with user_id."""
        user_id = uuid4()
        calc = CalculationCreate(type="addition", inputs=[1.0, 2.0], user_id=user_id)
        assert calc.user_id == user_id

    def test_create_inherits_validation(self):
        """Test CalculationCreate inherits base validation."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationCreate(type="division", inputs=[10.0, 0.0])
        
        assert "Cannot divide by zero" in str(exc_info.value)


class TestCalculationUpdate:
    """Test the CalculationUpdate schema."""

    def test_update_all_optional(self):
        """Test that all fields are optional in update."""
        update = CalculationUpdate()
        assert update.type is None
        assert update.inputs is None
        assert update.user_id is None

    def test_update_type_only(self):
        """Test updating only the type."""
        update = CalculationUpdate(type="multiplication")
        assert update.type == CalculationType.MULTIPLICATION
        assert update.inputs is None

    def test_update_inputs_only(self):
        """Test updating only the inputs."""
        update = CalculationUpdate(inputs=[5.0, 10.0])
        assert update.inputs == [5.0, 10.0]
        assert update.type is None

    def test_update_validates_division_by_zero(self):
        """Test update validates division by zero."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationUpdate(type="division", inputs=[10.0, 0.0])
        
        assert "Cannot divide by zero" in str(exc_info.value)

    def test_update_type_normalization(self):
        """Test type normalization in updates."""
        update = CalculationUpdate(type="SUBTRACTION")
        assert update.type == CalculationType.SUBTRACTION


class TestCalculationResponse:
    """Test the CalculationResponse schema."""

    def test_response_includes_all_fields(self):
        """Test response schema includes id, result, and other fields."""
        calc_id = uuid4()
        user_id = uuid4()
        
        response = CalculationResponse(
            id=calc_id,
            type="addition",
            inputs=[1.0, 2.0],
            user_id=user_id,
            result=3.0
        )
        
        assert response.id == calc_id
        assert response.type == CalculationType.ADDITION
        assert response.inputs == [1.0, 2.0]
        assert response.user_id == user_id
        assert response.result == 3.0

    def test_response_result_can_be_none(self):
        """Test that result can be None (for division by zero, etc.)."""
        response = CalculationResponse(
            id=uuid4(),
            type="division",
            inputs=[10.0, 0.0],
            result=None
        )
        
        assert response.result is None


class TestEdgeCases:
    """Test edge cases in schema validation."""

    def test_very_large_numbers(self):
        """Test handling of very large numbers."""
        calc = CalculationBase(type="addition", inputs=[1e100, 2e100])
        assert calc.inputs == [1e100, 2e100]

    def test_negative_numbers(self):
        """Test handling of negative numbers."""
        calc = CalculationBase(type="addition", inputs=[-10.0, -20.0, 30.0])
        assert calc.inputs == [-10.0, -20.0, 30.0]

    def test_float_precision(self):
        """Test handling of float precision."""
        calc = CalculationBase(type="addition", inputs=[0.1, 0.2, 0.3])
        assert len(calc.inputs) == 3

    def test_many_inputs(self):
        """Test handling of many inputs."""
        inputs = list(range(100))
        calc = CalculationBase(type="addition", inputs=inputs)
        assert len(calc.inputs) == 100

    def test_mixed_integer_float(self):
        """Test mixing integers and floats in inputs."""
        calc = CalculationBase(type="addition", inputs=[1, 2.5, 3])
        assert calc.inputs == [1.0, 2.5, 3.0]

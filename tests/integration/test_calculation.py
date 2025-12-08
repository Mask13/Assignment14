"""
Integration tests for polymorphic Calculation models.

These tests verify:
1. Individual operation behavior (Addition, Subtraction, Multiplication, Division)
2. Factory pattern creates correct subclasses
3. Polymorphic behavior (mixed types in queries)
4. Database persistence and retrieval
5. Edge cases (division by zero, empty inputs, etc.)
"""

import pytest
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.calculation import (
    Calculation,
    Addition,
    Subtraction,
    Multiplication,
    Division,
)


class TestIndividualOperations:
    """Test each calculation type individually."""

    def test_addition_simple(self, db_session: Session):
        """Test basic addition with positive numbers."""
        calc = Addition(user_id=None, inputs=[1.0, 2.0, 3.0])
        db_session.add(calc)
        db_session.commit()
        db_session.refresh(calc)

        assert calc.get_result() == 6.0
        assert isinstance(calc, Addition)
        assert calc.type == "addition"

    def test_addition_negative_numbers(self, db_session: Session):
        """Test addition with negative numbers."""
        calc = Addition(user_id=None, inputs=[-5.0, 10.0, -3.0])
        db_session.add(calc)
        db_session.commit()

        assert calc.get_result() == 2.0

    def test_subtraction_simple(self, db_session: Session):
        """Test basic subtraction."""
        calc = Subtraction(user_id=None, inputs=[10.0, 3.0, 2.0])
        db_session.add(calc)
        db_session.commit()
        db_session.refresh(calc)

        assert calc.get_result() == 5.0
        assert isinstance(calc, Subtraction)
        assert calc.type == "subtraction"

    def test_subtraction_negative_result(self, db_session: Session):
        """Test subtraction resulting in negative number."""
        calc = Subtraction(user_id=None, inputs=[5.0, 10.0])
        db_session.add(calc)
        db_session.commit()

        assert calc.get_result() == -5.0

    def test_multiplication_simple(self, db_session: Session):
        """Test basic multiplication."""
        calc = Multiplication(user_id=None, inputs=[2.0, 3.0, 4.0])
        db_session.add(calc)
        db_session.commit()
        db_session.refresh(calc)

        assert calc.get_result() == 24.0
        assert isinstance(calc, Multiplication)
        assert calc.type == "multiplication"

    def test_multiplication_with_zero(self, db_session: Session):
        """Test multiplication with zero."""
        calc = Multiplication(user_id=None, inputs=[5.0, 0.0, 10.0])
        db_session.add(calc)
        db_session.commit()

        assert calc.get_result() == 0.0

    def test_division_simple(self, db_session: Session):
        """Test basic division."""
        calc = Division(user_id=None, inputs=[20.0, 4.0, 2.0])
        db_session.add(calc)
        db_session.commit()
        db_session.refresh(calc)

        assert calc.get_result() == 2.5
        assert isinstance(calc, Division)
        assert calc.type == "division"

    def test_division_by_zero_raises_error(self, db_session: Session):
        """Test that division by zero raises ValueError (EAFP)."""
        calc = Division(user_id=None, inputs=[10.0, 0.0])
        db_session.add(calc)
        db_session.commit()

        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calc.get_result()


class TestFactoryPattern:
    """Test the Calculation.create() factory method."""

    def test_factory_creates_addition(self, db_session: Session):
        """Test factory creates Addition subclass."""
        calc = Calculation.create("addition", None, [1.0, 2.0])
        db_session.add(calc)
        db_session.commit()

        assert isinstance(calc, Addition)
        assert calc.get_result() == 3.0

    def test_factory_creates_subtraction(self, db_session: Session):
        """Test factory creates Subtraction subclass."""
        calc = Calculation.create("subtraction", None, [10.0, 3.0])
        db_session.add(calc)
        db_session.commit()

        assert isinstance(calc, Subtraction)
        assert calc.get_result() == 7.0

    def test_factory_creates_multiplication(self, db_session: Session):
        """Test factory creates Multiplication subclass."""
        calc = Calculation.create("multiplication", None, [2.0, 3.0])
        db_session.add(calc)
        db_session.commit()

        assert isinstance(calc, Multiplication)
        assert calc.get_result() == 6.0

    def test_factory_creates_division(self, db_session: Session):
        """Test factory creates Division subclass."""
        calc = Calculation.create("division", None, [10.0, 2.0])
        db_session.add(calc)
        db_session.commit()

        assert isinstance(calc, Division)
        assert calc.get_result() == 5.0

    def test_factory_case_insensitive(self, db_session: Session):
        """Test factory handles case-insensitive type names."""
        calc1 = Calculation.create("ADDITION", None, [1.0, 2.0])
        calc2 = Calculation.create("Addition", None, [1.0, 2.0])
        calc3 = Calculation.create("aDdItIoN", None, [1.0, 2.0])

        assert isinstance(calc1, Addition)
        assert isinstance(calc2, Addition)
        assert isinstance(calc3, Addition)

    def test_factory_invalid_type_raises_error(self):
        """Test factory raises ValueError for invalid type."""
        with pytest.raises(ValueError, match="Invalid calculation type"):
            Calculation.create("invalid", None, [1.0, 2.0])


class TestPolymorphicBehavior:
    """Test polymorphic query behavior."""

    def test_query_returns_mixed_types(self, db_session: Session):
        """Test that querying Calculation returns mixed subclass types."""
        # Create different types of calculations
        add = Addition(user_id=None, inputs=[1.0, 2.0])
        sub = Subtraction(user_id=None, inputs=[10.0, 3.0])
        mul = Multiplication(user_id=None, inputs=[2.0, 3.0])
        div = Division(user_id=None, inputs=[20.0, 4.0])

        db_session.add_all([add, sub, mul, div])
        db_session.commit()

        # Query all calculations
        calculations = db_session.query(Calculation).all()

        # Verify we got all 4
        assert len(calculations) >= 4

        # Find our calculations and verify their types
        types_found = {type(c).__name__ for c in calculations}
        assert "Addition" in types_found
        assert "Subtraction" in types_found
        assert "Multiplication" in types_found
        assert "Division" in types_found

    def test_polymorphic_identity_persists(self, db_session: Session):
        """Test that type discriminator persists correctly."""
        calc = Addition(user_id=None, inputs=[1.0, 2.0])
        db_session.add(calc)
        db_session.commit()
        calc_id = calc.id

        # Clear session and reload
        db_session.expire_all()
        reloaded = db_session.query(Calculation).filter(Calculation.id == calc_id).first()

        assert isinstance(reloaded, Addition)
        assert reloaded.type == "addition"
        assert reloaded.get_result() == 3.0

    def test_each_subclass_has_unique_behavior(self, db_session: Session):
        """Test that each subclass implements get_result() differently."""
        inputs = [10.0, 2.0]

        add = Addition(user_id=None, inputs=inputs)
        sub = Subtraction(user_id=None, inputs=inputs)
        mul = Multiplication(user_id=None, inputs=inputs)
        div = Division(user_id=None, inputs=inputs)

        db_session.add_all([add, sub, mul, div])
        db_session.commit()

        # Each should produce different results from same inputs
        assert add.get_result() == 12.0  # 10 + 2
        assert sub.get_result() == 8.0   # 10 - 2
        assert mul.get_result() == 20.0  # 10 * 2
        assert div.get_result() == 5.0   # 10 / 2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_inputs_addition(self, db_session: Session):
        """Test addition with empty inputs."""
        calc = Addition(user_id=None, inputs=[])
        db_session.add(calc)
        db_session.commit()

        assert calc.get_result() == 0.0

    def test_empty_inputs_subtraction(self, db_session: Session):
        """Test subtraction with empty inputs."""
        calc = Subtraction(user_id=None, inputs=[])
        db_session.add(calc)
        db_session.commit()

        assert calc.get_result() == 0.0

    def test_single_input(self, db_session: Session):
        """Test operations with single input."""
        add = Addition(user_id=None, inputs=[5.0])
        sub = Subtraction(user_id=None, inputs=[5.0])
        mul = Multiplication(user_id=None, inputs=[5.0])
        div = Division(user_id=None, inputs=[5.0])

        db_session.add_all([add, sub, mul, div])
        db_session.commit()

        assert add.get_result() == 5.0
        assert sub.get_result() == 5.0
        assert mul.get_result() == 5.0
        assert div.get_result() == 5.0

    def test_large_numbers(self, db_session: Session):
        """Test operations with large numbers."""
        calc = Addition(user_id=None, inputs=[1e10, 2e10, 3e10])
        db_session.add(calc)
        db_session.commit()

        assert calc.get_result() == 6e10

    def test_user_association(self, db_session: Session):
        """Test calculation can be associated with a user."""
        # Create without user_id (nullable)
        calc = Addition(user_id=None, inputs=[1.0, 2.0])
        db_session.add(calc)
        db_session.commit()

        assert calc.user_id is None
        assert calc.get_result() == 3.0

from enum import Enum

class CalculationType(str, Enum):
    ADDITION = "addition"

print(f"Value: {CalculationType.ADDITION}")
print(f"String: {str(CalculationType.ADDITION)}")
print(f"Lower: {CalculationType.ADDITION.lower()}")

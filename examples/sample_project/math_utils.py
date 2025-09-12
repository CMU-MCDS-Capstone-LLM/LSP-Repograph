"""
Math utilities for demonstration
"""

def calculate_sum(a, b):
    """Calculate the sum of two numbers"""
    return a + b

def calculate_product(a, b):
    """Calculate the product of two numbers"""
    return a * b

class Calculator:
    """A simple calculator class"""
    
    def __init__(self):
        self.history = []
    
    def add(self, x, y):
        """Add two numbers"""
        result = calculate_sum(x, y)
        self.history.append(f"{x} + {y} = {result}")
        return result
    
    def multiply(self, x, y):
        """Multiply two numbers"""
        result = calculate_product(x, y)
        self.history.append(f"{x} * {y} = {result}")
        return result
    
    def get_history(self):
        """Get calculation history"""
        return self.history
    
    def clear_history(self):
        """Clear calculation history"""
        self.history = []

class AdvancedCalculator(Calculator):
    """Advanced calculator with more operations"""
    
    def power(self, base, exponent):
        """Calculate power"""
        result = base ** exponent
        self.history.append(f"{base} ^ {exponent} = {result}")
        return result
    
    def sqrt(self, number):
        """Calculate square root"""
        import math
        result = math.sqrt(number)
        self.history.append(f"sqrt({number}) = {result}")
        return result

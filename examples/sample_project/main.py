"""
Main application demonstrating calculator usage
"""

from core.math_utils import Calculator, AdvancedCalculator, calculate_sum
import numpy as np

def main():
    """Main application function"""
    print(f"Numpy version: {np.__version__}")
    # Test basic calculator
    calc = Calculator()
    result1 = calc.add(5, 3)
    result2 = calc.multiply(4, 7)
    
    print(f"Calculator results: {result1}, {result2}")
    print("Basic calculator history:", calc.get_history())
    
    # Test advanced calculator
    advanced_calc = AdvancedCalculator()
    result3 = advanced_calc.power(2, 8)
    result4 = advanced_calc.sqrt(16)
    
    print(f"Advanced calculator results: {result3}, {result4}")
    print("Advanced calculator history:", advanced_calc.get_history())
    
    # Test standalone function
    result5 = calculate_sum(10, 20)
    print(f"Direct calculation: {result5}")

def helper_function():
    """Helper function that uses Calculator"""
    calc = Calculator()
    calc.add(1, 2)
    return calc

class DataProcessor:
    """Class that uses calculator for processing"""
    
    def __init__(self):
        self.calculator = Calculator()
    
    def process_numbers(self, numbers):
        """Process a list of numbers"""
        total = 0
        for i, num in enumerate(numbers):
            if i == 0:
                total = num
            else:
                total = self.calculator.add(total, num)
        return total

if __name__ == "__main__":
    main()

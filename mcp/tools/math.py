from typing import Any
from server import mcp

@mcp.tool()
def multiply(first_val: float, second_val: float) -> float:
    '''
    Calculate the product of two numbers

    Args:
        first_val: the first value to be multiplied
        second_val: the second value to be multiplied
    '''
    return round(first_val * second_val, 4)

from typing import Dict, List, Optional, Any
import json
from server import mcp

@mcp.tool()
def validate_api_request(request_data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """
    Validate API request data against required fields.

    Args:
        request_data: The incoming request data
        required_fields: List of required field names

    Returns:
        Validation result with success status and error details
    """
    missing_fields = []
    invalid_fields = []

    for field in required_fields:
        if field not in request_data:
            missing_fields.append(field)
        elif request_data[field] is None or request_data[field] == "":
            invalid_fields.append(field)

    is_valid = len(missing_fields) == 0 and len(invalid_fields) == 0

    return {
        "valid": is_valid,
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
        "message": "Valid request" if is_valid else "Request validation failed"
    }


@mcp.tool()
def format_api_response(data: Any, status_code: int = 200, message: str = "Success") -> Dict[str, Any]:
    """
    Format data into a standardized API response structure.

    Args:
        data: The response data
        status_code: HTTP status code
        message: Response message

    Returns:
        Formatted API response
    """
    return {
        "status": "success" if 200 <= status_code < 300 else "error",
        "status_code": status_code,
        "message": message,
        "data": data,
        "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
    }


@mcp.tool()
def paginate_results(items: List[Any], page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    """
    Paginate a list of items.

    Args:
        items: List of items to paginate
        page: Page number (1-based)
        per_page: Number of items per page

    Returns:
        Paginated results with metadata
    """
    total_items = len(items)
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1

    start_index = (page - 1) * per_page
    end_index = start_index + per_page

    paginated_items = items[start_index:end_index]

    return {
        "items": paginated_items,
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


import math  # Add this import at the top

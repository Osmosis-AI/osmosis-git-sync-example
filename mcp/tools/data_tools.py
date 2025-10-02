import mcp
from typing import Dict, List, Optional, Any
import json
import requests


@mcp.tool()
def fetch_user_data(user_id: int, include_metadata: bool = False) -> Dict[str, Any]:
    """
    Fetch user data from the platform API.
    
    Args:
        user_id: The unique identifier for the user
        include_metadata: Whether to include additional metadata in response
    
    Returns:
        Dictionary containing user information and optionally metadata
    """
    # Simulate API call
    user_data = {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    if include_metadata:
        user_data["metadata"] = {
            "last_login": "2024-01-15T10:30:00Z",
            "profile_completion": 85,
            "subscription_status": "active"
        }
    
    return user_data


@mcp.tool()
async def analyze_user_behavior(user_id: int, days_back: int = 30) -> Dict[str, Any]:
    """
    Analyze user behavior patterns over a specified time period.
    
    Args:
        user_id: The unique identifier for the user
        days_back: Number of days to analyze (default 30)
    
    Returns:
        Analysis results including activity patterns and insights
    """
    # Simulate behavior analysis
    analysis = {
        "user_id": user_id,
        "period_days": days_back,
        "total_sessions": 45,
        "avg_session_duration": 12.5,
        "most_active_hour": 14,
        "preferred_features": ["dashboard", "reports", "settings"],
        "engagement_score": 7.8
    }
    
    return analysis


@mcp.tool()
def export_data(data: Dict[str, Any], format_type: str = "json") -> str:
    """
    Export data in the specified format.
    
    Args:
        data: The data to export
        format_type: Format for export (json, csv, xml)
    
    Returns:
        Formatted data as string
    """
    if format_type.lower() == "json":
        return json.dumps(data, indent=2)
    elif format_type.lower() == "csv":
        # Simple CSV conversion for flat dictionaries
        if isinstance(data, dict):
            headers = list(data.keys())
            values = list(data.values())
            return f"{','.join(headers)}\n{','.join(map(str, values))}"
    elif format_type.lower() == "xml":
        # Simple XML conversion
        xml_parts = ["<data>"]
        for key, value in data.items():
            xml_parts.append(f"  <{key}>{value}</{key}>")
        xml_parts.append("</data>")
        return "\n".join(xml_parts)
    
    return str(data)
# Example Repository for Osmosis GitHub Sync

This repository demonstrates the expected structure and content that will be automatically synced by the Osmosis GitHub integration.

## Repository Structure

### `/mcp/` - MCP Tools Directory

Contains Python files with MCP (Model Context Protocol) tool functions that will be automatically discovered and synced to the Osmosis platform.

**Files:**
- `data_tools.py` - Tools for fetching and processing user data
- `ml_utils.py` - Machine learning utility functions
- `api_helpers.py` - API validation and formatting helpers

**Requirements:**
- Functions must be decorated with `@mcp.tool()`
- Functions should include proper type hints
- Docstrings should describe the function's purpose and parameters

### `/reward_fn/` - Reward Function Directory

Contains the reward function implementation for reinforcement learning or behavior analysis.

**Files:**
- `compute_reward.py` - Main reward computation function

**Requirements:**
- Must contain a `compute_reward` function
- Function should accept state, action, next_state, and optional metadata parameters
- Should return a numeric reward value

## Sync Process

When this repository is connected to the Osmosis platform:

1. **MCP Tools**: All `@mcp.tool()` decorated functions in `/mcp/` will be:
   - Parsed for function signatures and parameters
   - Stored in the tools database with metadata
   - Made available for use in the platform

2. **Reward Functions**: The `compute_reward` function in `/reward_fn/compute_reward.py` will be:
   - Extracted and stored as a reward function
   - Available for reinforcement learning workflows
   - Used in behavior analysis and optimization

## Example Usage

### MCP Tools
```python
import mcp

@mcp.tool()
def my_custom_tool(param1: str, param2: int = 10) -> dict:
    """
    Description of what this tool does.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter with default
    
    Returns:
        Description of return value
    """
    # Tool implementation
    return {"result": "processed"}
```

### Reward Function
```python
def compute_reward(state: dict, action: dict, next_state: dict, metadata: dict = None) -> float:
    """
    Compute reward for a state transition.
    
    Args:
        state: Current state
        action: Action taken
        next_state: Resulting state
        metadata: Additional context
    
    Returns:
        Numeric reward value
    """
    # Reward computation logic
    return 1.0
```

## Development Notes

- All Python files should follow proper Python conventions
- Type hints are recommended for better tool discovery
- Docstrings help with automatic documentation generation
- Functions should handle edge cases gracefully
- Consider the execution environment when implementing tools

# Repo structure
```
your-repo/
├── mcp/              # MCP tools directory
│   ├── server/
│   │   └── mcp_server.py
│   └── tools/
│       ├── tool1.py
│       └── tool2.py
└── reward_fn/        # Reward functions directory
    └── compute_reward.py
```
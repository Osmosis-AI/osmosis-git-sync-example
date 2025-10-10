# Example Repository for Osmosis GitHub Sync

This repository demonstrates the expected structure and content that will be automatically synced by the Osmosis GitHub integration. It is expected that your tools and reward use python version 3.10

## Repository Structure

### `/mcp/` - MCP Tools Directory

Contains a FastMCP HTTP server with MCP (Model Context Protocol) tool functions that will be automatically discovered and synced to the Osmosis platform.

**Structure:**
```
mcp/
├── main.py                    # HTTP server entry point
├── server/
│   └── mcp_server.py         # FastMCP server instance ("OsmosisTools")
└── tools/
    ├── math.py               # Mathematical operations
    ├── ml_utils.py           # Machine learning utility functions
    └── api_helpers.py        # API validation and formatting helpers
```

**Available Tools:**

*math.py:*
- `multiply(first_val, second_val)` - Calculates the product of two numbers

*api_helpers.py:*
- `validate_api_request(request_data, required_fields)` - Validates API request data against required fields
- `format_api_response(data, status_code, message)` - Formats data into standardized API response structure
- `paginate_results(items, page, per_page)` - Paginates a list of items

*ml_utils.py:*
- `calculate_similarity(vector_a, vector_b)` - Calculates cosine similarity between two vectors
- `normalize_features(data, feature_names)` - Performs min-max normalization on specified features
- `return_true()` - Always returns true (test function)
- `cluster_analysis(data_points, num_clusters)` - Performs k-means clustering analysis

**Server Features:**
- HTTP transport support (default: 0.0.0.0:8080)
- Health check endpoint at `/health`
- Streamable responses

**Requirements:**
- Functions must be decorated with `@mcp.tool()` or `@mcp.tool`
- Functions should include proper type hints
- Docstrings should describe the function's purpose and parameters

### `/reward_fn/` - Reward Function Directory

Contains the reward function implementation for evaluating mathematical problem solutions.

**Files:**
- `compute_reward.py` - Reward computation function for numerical answer validation

**Implementation:**
- `numbers_match_reward(solution_str, ground_truth, extra_info)` - Extracts numerical answers from solution strings and compares them against ground truth
  - Expects solutions in format: `#### [number]`
  - Returns 1.0 if extracted solution matches ground truth (within 1e-7 tolerance)
  - Returns 0.0 otherwise

**Requirements:**
- Functions must be decorated with `@osmosis_reward`
- Function should return a numeric reward value

## Sync Process

When this repository is connected to the Osmosis platform:

1. **MCP Tools**: All `@mcp.tool()` decorated functions in `/mcp/tools/` will be:
   - Parsed for function signatures and parameters
   - Stored in the tools database with metadata
   - Made available for use in the platform

2. **Reward Functions**: The `@osmosis_reward` decorated functions in `/reward_fn/compute_reward.py` will be:
   - Extracted and stored as a reward function
   - Available for reinforcement learning workflows
   - Used in behavior analysis and optimization

## Running the MCP Server

To start the HTTP server:

```bash
# Default (0.0.0.0:8080)
python mcp/main.py

# Custom host and port
python mcp/main.py --host 127.0.0.1 --port 3000
```

Health check endpoint:
```bash
curl http://localhost:8080/health
# Returns: OK
```

## Example Usage

### MCP Tools
```python
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
```

### Reward Function
```python
import re
from osmosis_ai import osmosis_reward

def extract_solution(solution_str):
    solution = re.search(r'####\s*([-+]?\d*\.?\d+)', solution_str)
    if(not solution or solution is None):
        return None
    final_solution = solution.group(1)
    return final_solution

@osmosis_reward
def numbers_match_reward(solution_str: str, ground_truth: str, extra_info: dict=None):
    """
    Extract numerical answer from solution string and compare with ground truth.

    Args:
        solution_str: Solution string containing answer after ####
        ground_truth: Expected numerical answer as string
        extra_info: Additional context (optional)

    Returns:
        1.0 if answers match (within 1e-7), 0.0 otherwise
    """
    extracted = extract_solution(solution_str)
    try:
        sol_val = float(extracted)
    except:
        return 0.0

    gt_val = float(ground_truth)

    if(sol_val is None):
        return 0.0

    if(abs(gt_val - sol_val) < 1e-7):
        return 1.0
    return 0.0
```

# Repo structure
```
osmosis-git-sync-example/
├── mcp/                        # MCP tools directory
│   ├── main.py                 # HTTP server entry point
│   ├── server/
│   │   ├── __init__.py
│   │   └── mcp_server.py      # FastMCP server instance
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── math.py            # Mathematical operations
│   │   ├── api_helpers.py     # API validation and formatting
│   │   └── ml_utils.py        # ML utility functions
│   └── test/
│       └── test.py            # Test files
└── reward_fn/                  # Reward functions directory
    └── compute_reward.py      # Numerical answer validation
```
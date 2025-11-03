import re
from osmosis_ai import osmosis_reward

def extract_solution(solution_str):
    solution = re.search(r'####\s*([-+]?\d*\.?\d+)', solution_str)
    if(not solution or solution is None):
        return None
    final_solution = solution.group(1)
    return final_solution

@osmosis_reward
def numbers_match_reward(solution_str: str, ground_truth: str, extra_info: dict=None, **kwargs):
    extracted = extract_solution(solution_str)
    try:
        sol_val = float(extracted)
    except:
        # Logging
        # print(f"Failed to extract {extracted}")
        return 0.0

    gt_val = float(ground_truth)

    if(sol_val is None):
        return 0.0

    if(abs(gt_val - sol_val) < 1e-7):
        return 1.0
    return 0.0

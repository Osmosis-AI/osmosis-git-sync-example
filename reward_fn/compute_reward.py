from osmosis_ai import osmosis_reward


@osmosis_reward
def engagement_quality_reward(solution_str: str, ground_truth: str, extra_info: dict = None) -> float:
    """
    Reward based on solution engagement quality and completeness.
    """
    if not solution_str.strip():
        return 0.0

    # Base reward for providing a solution
    reward = 0.1

    # Length-based engagement (solutions that are more detailed)
    solution_length = len(solution_str.strip())
    truth_length = len(ground_truth.strip())

    if truth_length > 0:
        # Reward solutions that are appropriately detailed
        length_ratio = min(solution_length / truth_length, 2.0)
        reward += length_ratio * 0.3

    # Additional engagement metrics from extra_info
    if extra_info:
        engagement_score = extra_info.get("engagement_score", 0)
        reward += min(engagement_score * 0.2, 1.0)

    return reward


@osmosis_reward
def correctness_reward(solution_str: str, ground_truth: str, extra_info: dict = None) -> float:
    """
    Reward based on solution correctness with partial credit.
    """
    solution_clean = solution_str.strip().lower()
    truth_clean = ground_truth.strip().lower()

    # Exact match gets full points
    if solution_clean == truth_clean:
        return 5.0

    # Partial credit for similar solutions
    if solution_clean in truth_clean or truth_clean in solution_clean:
        return 2.5

    # Check for keyword matches if extra_info provides them
    if extra_info and "key_concepts" in extra_info:
        key_concepts = [k.lower() for k in extra_info["key_concepts"]]
        matches = sum(1 for concept in key_concepts if concept in solution_clean)
        if matches > 0:
            return matches * 1.0

    return 0.0


@osmosis_reward
def explanation_quality_reward(solution_str: str, ground_truth: str, extra_info: dict = None) -> float:
    """
    Reward solutions that demonstrate good explanation and reasoning.
    """
    solution_clean = solution_str.strip()

    if not solution_clean:
        return 0.0

    reward = 0.0

    # Reward explanatory keywords
    explanation_keywords = ["because", "therefore", "since", "due to", "as a result",
                           "this means", "in other words", "for example"]

    keyword_count = sum(1 for keyword in explanation_keywords
                       if keyword in solution_clean.lower())
    reward += min(keyword_count * 0.5, 2.0)

    # Reward structured thinking (lists, steps)
    if any(marker in solution_clean for marker in ["1.", "2.", "•", "-", "first", "second"]):
        reward += 1.0

    # Reward if explanation covers key learning concepts
    if extra_info and "learning_objectives" in extra_info:
        objectives = extra_info["learning_objectives"]
        covered = sum(1 for obj in objectives if obj.lower() in solution_clean.lower())
        reward += covered * 0.8

    return reward


@osmosis_reward
def creativity_reward(solution_str: str, ground_truth: str, extra_info: dict = None) -> float:
    """
    Reward creative and innovative approaches to solutions.
    """
    solution_clean = solution_str.strip()
    truth_clean = ground_truth.strip()

    if not solution_clean:
        return 0.0

    reward = 0.0

    # Reward alternative valid approaches
    if solution_clean.lower() != truth_clean.lower() and len(solution_clean) > len(truth_clean) * 0.8:
        reward += 1.5  # Bonus for different but substantial answers

    # Reward creative language and examples
    creativity_indicators = ["innovative", "creative", "alternative", "another way",
                           "different approach", "for instance", "imagine"]

    creative_count = sum(1 for indicator in creativity_indicators
                        if indicator in solution_clean.lower())
    reward += min(creative_count * 0.7, 2.0)

    # Bonus for providing multiple solutions or perspectives
    if "alternatively" in solution_clean.lower() or "option" in solution_clean.lower():
        reward += 1.0

    return reward


@osmosis_reward
def clarity_reward(solution_str: str, ground_truth: str, extra_info: dict = None) -> float:
    """
    Reward clear, well-structured solutions.
    """
    solution_clean = solution_str.strip()

    if not solution_clean:
        return 0.0

    reward = 0.0

    # Reward proper grammar and punctuation
    sentences = solution_clean.split('.')
    if len(sentences) > 1 and sentences[-1].strip() == '':
        reward += 0.5  # Bonus for proper sentence ending

    # Reward appropriate length (not too short, not too verbose)
    word_count = len(solution_clean.split())
    if 10 <= word_count <= 100:
        reward += 1.0
    elif 5 <= word_count <= 150:
        reward += 0.5

    # Reward clear structure
    if any(transition in solution_clean.lower() for transition in
           ["first", "next", "then", "finally", "in conclusion"]):
        reward += 0.8

    # Quality indicators from extra_info
    if extra_info:
        clarity_score = extra_info.get("clarity_score", 0)
        reward += clarity_score * 1.5

    return reward


@osmosis_reward
def appropriateness_penalty(solution_str: str, ground_truth: str, extra_info: dict = None) -> float:
    """
    Apply penalties for inappropriate or low-quality responses.
    """
    solution_clean = solution_str.strip().lower()

    if not solution_clean:
        return -1.0  # Penalty for empty responses

    penalty = 0.0

    # Penalty for very short, low-effort responses
    if len(solution_clean) < 3:
        penalty -= 2.0

    # Penalty for spam-like content
    spam_indicators = ["spam", "click here", "buy now", "free money"]
    if any(indicator in solution_clean for indicator in spam_indicators):
        penalty -= 5.0

    # Penalty for inappropriate content flags from extra_info
    if extra_info:
        if extra_info.get("inappropriate", False):
            penalty -= 10.0
        if extra_info.get("off_topic", False):
            penalty -= 3.0

    return penalty


def compute_reward(solution_str: str, ground_truth: str, extra_info: dict = None) -> float:
    """
    Compute combined reward for evaluating solution quality in the Osmosis platform.

    This function combines multiple specialized reward functions to evaluate
    solution quality across different dimensions: correctness, engagement,
    explanation quality, creativity, clarity, and appropriateness.

    Args:
        solution_str: The solution string provided by the user
        ground_truth: The expected/correct solution string to compare against
        extra_info: Additional context information such as learning objectives,
                   key concepts, engagement metrics, and quality scores

    Returns:
        Float reward value (higher is better, bounded between -20.0 and 50.0)
    """
    # Combine rewards from all specialized reward functions
    reward = 0.0
    reward += engagement_quality_reward(solution_str, ground_truth, extra_info)
    reward += correctness_reward(solution_str, ground_truth, extra_info)
    reward += explanation_quality_reward(solution_str, ground_truth, extra_info)
    reward += creativity_reward(solution_str, ground_truth, extra_info)
    reward += clarity_reward(solution_str, ground_truth, extra_info)
    reward += appropriateness_penalty(solution_str, ground_truth, extra_info)

    # Ensure reward is within reasonable bounds
    reward = max(-20.0, min(50.0, reward))

    return reward


def compute_discounted_reward(rewards: list, discount_factor: float = 0.9) -> float:
    """
    Compute discounted cumulative reward from a sequence of rewards.
    
    Args:
        rewards: List of reward values
        discount_factor: Discount factor for future rewards (0-1)
    
    Returns:
        Discounted cumulative reward
    """
    discounted_reward = 0.0
    for i, reward in enumerate(rewards):
        discounted_reward += reward * (discount_factor ** i)
    return discounted_reward
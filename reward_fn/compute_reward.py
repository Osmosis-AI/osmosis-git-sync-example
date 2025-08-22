def compute_reward(state: dict, action: dict, next_state: dict, metadata: dict = None) -> float:
    """
    Compute reward for a given state transition in the Osmosis platform.
    
    This reward function evaluates user actions and state changes to provide
    feedback for reinforcement learning algorithms or behavior analysis.
    
    Args:
        state: Current state of the system/user
        action: Action taken by the user
        next_state: Resulting state after the action
        metadata: Additional context information
    
    Returns:
        Float reward value (higher is better)
    """
    reward = 0.0
    
    # Base reward for any action (encourages engagement)
    reward += 0.1
    
    # Reward for task completion
    if state.get("task_status") == "pending" and next_state.get("task_status") == "completed":
        task_complexity = state.get("task_complexity", 1)
        reward += 5.0 * task_complexity
    
    # Reward for learning progress
    if "skill_level" in state and "skill_level" in next_state:
        skill_improvement = next_state["skill_level"] - state["skill_level"]
        reward += skill_improvement * 2.0
    
    # Reward for collaboration
    if action.get("type") == "collaborate":
        num_collaborators = action.get("collaborators", 0)
        reward += num_collaborators * 1.5
    
    # Reward for knowledge sharing
    if action.get("type") == "share_knowledge":
        knowledge_quality = action.get("quality_score", 0)
        reward += knowledge_quality * 3.0
    
    # Penalty for negative actions
    if action.get("type") == "spam" or action.get("inappropriate", False):
        reward -= 10.0
    
    # Time-based rewards (encourage timely completion)
    if metadata and "time_taken" in metadata:
        time_taken = metadata["time_taken"]
        expected_time = metadata.get("expected_time", time_taken)
        if time_taken <= expected_time:
            efficiency_bonus = (expected_time - time_taken) / expected_time * 2.0
            reward += efficiency_bonus
    
    # Quality-based rewards
    if "output_quality" in next_state:
        quality_score = next_state["output_quality"]
        reward += quality_score * 1.0
    
    # User satisfaction rewards
    if "user_satisfaction" in next_state:
        satisfaction = next_state["user_satisfaction"]
        reward += satisfaction * 2.5
    
    # Platform engagement rewards
    if "engagement_metrics" in next_state:
        engagement = next_state["engagement_metrics"]
        session_length = engagement.get("session_length", 0)
        interactions = engagement.get("interactions", 0)
        
        # Reward longer, more interactive sessions (with diminishing returns)
        reward += min(session_length * 0.1, 2.0)
        reward += min(interactions * 0.2, 3.0)
    
    # Learning outcome rewards
    if "learning_outcomes" in next_state:
        outcomes = next_state["learning_outcomes"]
        concepts_mastered = outcomes.get("concepts_mastered", 0)
        retention_rate = outcomes.get("retention_rate", 0.0)
        
        reward += concepts_mastered * 1.0
        reward += retention_rate * 5.0
    
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
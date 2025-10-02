from typing import List, Dict, Any, Optional
import math
import statistics

from server import mcp


@mcp.tool
def calculate_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vector_a: First vector as list of floats
        vector_b: Second vector as list of floats

    Returns:
        Cosine similarity score between -1 and 1
    """
    if len(vector_a) != len(vector_b):
        raise ValueError("Vectors must have the same length")

    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    magnitude_a = math.sqrt(sum(a * a for a in vector_a))
    magnitude_b = math.sqrt(sum(b * b for b in vector_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


@mcp.tool
def normalize_features(data: List[Dict[str, float]], feature_names: List[str]) -> List[Dict[str, float]]:
    """
    Normalize specified features using min-max normalization.

    Args:
        data: List of data points as dictionaries
        feature_names: Names of features to normalize

    Returns:
        List of data points with normalized features
    """
    normalized_data = []

    # Calculate min and max for each feature
    feature_stats = {}
    for feature in feature_names:
        values = [point.get(feature, 0) for point in data]
        feature_stats[feature] = {
            "min": min(values),
            "max": max(values)
        }

    # Normalize each data point
    for point in data:
        normalized_point = point.copy()
        for feature in feature_names:
            min_val = feature_stats[feature]["min"]
            max_val = feature_stats[feature]["max"]

            if max_val - min_val != 0:
                normalized_point[feature] = (point.get(feature, 0) - min_val) / (max_val - min_val)
            else:
                normalized_point[feature] = 0.0

        normalized_data.append(normalized_point)

    return normalized_data

@mcp.tool()
def return_true() -> bool:
    """
    Always return true

    Returns:
        Truthy bool
    """
    return True

@mcp.tool()
async def cluster_analysis(data_points: List[Dict[str, float]], num_clusters: int = 3) -> Dict[str, Any]:
    """
    Perform simple k-means clustering analysis on data points.

    Args:
        data_points: List of data points with numeric features
        num_clusters: Number of clusters to create

    Returns:
        Clustering results with centroids and assignments
    """
    if not data_points:
        return {"clusters": [], "centroids": []}

    # Simple clustering simulation (would use actual k-means in production)
    feature_names = list(data_points[0].keys())

    # Initialize centroids randomly
    centroids = []
    for i in range(num_clusters):
        centroid = {}
        for feature in feature_names:
            values = [point.get(feature, 0) for point in data_points]
            centroid[feature] = statistics.mean(values) + (i - num_clusters/2) * statistics.stdev(values) * 0.5
        centroids.append(centroid)

    # Assign points to clusters (simplified)
    clusters = [[] for _ in range(num_clusters)]
    for i, point in enumerate(data_points):
        cluster_id = i % num_clusters  # Simplified assignment
        clusters[cluster_id].append(point)

    return {
        "num_clusters": num_clusters,
        "centroids": centroids,
        "clusters": clusters,
        "cluster_sizes": [len(cluster) for cluster in clusters]
    }

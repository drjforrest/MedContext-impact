"""
Threshold optimization tool for agentic workflow.

Allows the agent to automatically optimize decision thresholds when
validation data is provided.
"""

from typing import Any
import logging

from app.orchestrator.threshold_optimizer import optimize_thresholds_from_dataset

logger = logging.getLogger(__name__)


async def optimize_thresholds_tool(dataset_path: str) -> dict[str, Any]:
    """
    Tool for agent to optimize decision thresholds on a validation dataset.
    
    Args:
        dataset_path: Path to validation dataset JSON file
        
    Returns:
        Dict with optimal configuration:
        {
            "optimal": {
                "logic": str,
                "veracity_threshold": float,
                "alignment_threshold": float,
                "accuracy": float,
                "precision": float,
                "recall": float,
                "f1": float
            },
            "bootstrap_ci": {...},
            "n_samples": int
        }
    """
    try:
        logger.info(f"Agent invoking threshold optimization tool for {dataset_path}")
        results = await optimize_thresholds_from_dataset(dataset_path)
        
        logger.info(
            f"Threshold optimization complete: {results['optimal']['logic']} logic, "
            f"veracity<{results['optimal']['veracity_threshold']:.2f}, "
            f"alignment<{results['optimal']['alignment_threshold']:.2f}, "
            f"accuracy={results['optimal']['accuracy']:.1%}"
        )
        
        return results
    except Exception as e:
        logger.error(f"Threshold optimization tool failed: {e}")
        return {
            "error": str(e),
            "optimal": None,
        }


def get_tool_description() -> dict[str, Any]:
    """
    Returns tool description for agent's tool selection.
    """
    return {
        "name": "optimize_thresholds",
        "description": (
            "Optimize decision thresholds for contextual authenticity scoring. "
            "Use this tool when the user provides a labeled validation dataset "
            "(image-claim pairs with ground truth labels) and wants to find optimal "
            "veracity and alignment thresholds for their specific domain. "
            "Returns optimal threshold configuration with performance metrics and "
            "bootstrap confidence intervals. The optimized thresholds can then be "
            "applied to subsequent verifications."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset_path": {
                    "type": "string",
                    "description": "Path to validation dataset JSON file with format: [{\"image_path\": str, \"claim\": str, \"label\": \"misinformation\" | \"legitimate\"}]"
                }
            },
            "required": ["dataset_path"]
        }
    }

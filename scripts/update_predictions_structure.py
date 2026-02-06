#!/usr/bin/env python3
"""Script to update the predictions structure to use new metrics:
- veracity of claim (instead of plausibility)
- alignment with image
- authenticity of image
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def load_predictions(file_path: Path) -> List[Dict[str, Any]]:
    """Load predictions from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_predictions(file_path: Path, predictions: List[Dict[str, Any]]) -> None:
    """Save predictions to JSON file."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)


def update_ground_truth_structure(
    predictions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Update ground truth structure to use new metrics instead of old ones."""
    updated_predictions = []

    for record in predictions:
        # Copy the record
        updated_record = record.copy()

        # Update ground truth structure
        old_gt = record.get("ground_truth", {})
        new_gt = old_gt.copy()

        # Map old "plausibility" to new "veracity"
        if "plausibility" in old_gt:
            plausibility = old_gt["plausibility"]
            # Map old plausibility values to new veracity values
            veracity_mapping = {"high": "high", "medium": "medium", "low": "low"}
            new_gt["veracity"] = veracity_mapping.get(plausibility, plausibility)
            # Remove the old plausibility field
            del new_gt["plausibility"]

        # Add the updated ground truth
        updated_record["ground_truth"] = new_gt

        # Update contextual analysis to ensure it has semantic categories
        predictions_data = record.get("predictions", {})
        if "contextual_analysis" in predictions_data:
            ctx_analysis = predictions_data["contextual_analysis"].copy()

            # Ensure semantic categories exist
            if "veracity_category" not in ctx_analysis:
                veracity_score = ctx_analysis.get("veracity_score", 0.5)
                if veracity_score >= 0.7:
                    ctx_analysis["veracity_category"] = "true"
                elif veracity_score >= 0.3:
                    ctx_analysis["veracity_category"] = "partially_true"
                else:
                    ctx_analysis["veracity_category"] = "false"

            if "alignment_category" not in ctx_analysis:
                alignment_score = ctx_analysis.get("alignment_score", 0.5)
                if alignment_score >= 0.7:
                    ctx_analysis["alignment_category"] = "aligns_fully"
                elif alignment_score >= 0.3:
                    ctx_analysis["alignment_category"] = "partially_aligns"
                else:
                    ctx_analysis["alignment_category"] = "does_not_align"

            updated_record["predictions"]["contextual_analysis"] = ctx_analysis

            # Also update combined analysis to have the same categories
            if "combined_analysis" in predictions_data:
                combined_analysis = predictions_data["combined_analysis"].copy()
                combined_analysis.update(
                    {
                        "veracity_category": ctx_analysis["veracity_category"],
                        "alignment_category": ctx_analysis["alignment_category"],
                    }
                )
                updated_record["predictions"]["combined_analysis"] = combined_analysis

        updated_predictions.append(updated_record)

    return updated_predictions


def main():
    # Define file paths
    original_file = Path(
        "validation_results/three_method_v1/raw_predictions_corrected.json"
    )
    updated_file = Path(
        "validation_results/three_method_v1/raw_predictions_updated.json"
    )

    print("Loading predictions...")
    predictions = load_predictions(original_file)

    print("Updating ground truth structure...")
    updated_predictions = update_ground_truth_structure(predictions)

    print("Saving updated predictions...")
    save_predictions(updated_file, updated_predictions)

    print(f"Done! Updated file saved to {updated_file}")
    print(f"Total records processed: {len(updated_predictions)}")

    # Show sample of updated structure
    if updated_predictions:
        sample_record = updated_predictions[0]
        print("\nSample updated structure:")
        print(f"Ground truth keys: {list(sample_record['ground_truth'].keys())}")
        if "contextual_analysis" in sample_record["predictions"]:
            ctx_keys = list(sample_record["predictions"]["contextual_analysis"].keys())
            print(f"Contextual analysis keys: {ctx_keys}")


if __name__ == "__main__":
    main()

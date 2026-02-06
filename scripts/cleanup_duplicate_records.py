#!/usr/bin/env python3
"""Script to clean up duplicate records in raw_predictions.json."""

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


def deduplicate_records(predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate records for the same image_id with same claim."""
    seen_keys = set()
    unique_predictions = []

    for record in predictions:
        image_id = record["image_id"]
        claim = record["claim"]

        # Create a unique key based on image_id and claim
        key = (image_id, claim)

        if key not in seen_keys:
            seen_keys.add(key)
            unique_predictions.append(record)
        else:
            print(
                f"Removing duplicate record: image_id='{image_id}', claim='{claim[:50]}...'"
            )

    print(
        f"Original records: {len(predictions)}, Unique records: {len(unique_predictions)}"
    )
    return unique_predictions


def fix_file_size_consistency(
    predictions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Ensure file_size consistency for each image_id across all related entries."""
    # Group records by image_id
    image_groups = {}
    for record in predictions:
        img_id = record["image_id"]
        if img_id not in image_groups:
            image_groups[img_id] = []
        image_groups[img_id].append(record)

    # For each image_id group, find the most common file_size
    fixed_predictions = []
    for img_id, records in image_groups.items():
        # Find the most common file_size for this image_id
        file_sizes = []
        for record in records:
            pixel_forensics = record["predictions"].get("pixel_forensics", {})
            file_size = pixel_forensics.get("file_size")
            if file_size is not None:
                file_sizes.append(file_size)

        if file_sizes:
            # Find the most common file_size
            from collections import Counter

            size_counts = Counter(file_sizes)
            most_common_size = size_counts.most_common(1)[0][0]

            # Update all records for this image_id to use the consistent file_size
            for record in records:
                # Update pixel_forensics file_size
                if "pixel_forensics" in record["predictions"]:
                    record["predictions"]["pixel_forensics"]["file_size"] = (
                        most_common_size
                    )

                # Update combined_analysis file_size
                if "combined_analysis" in record["predictions"]:
                    record["predictions"]["combined_analysis"]["file_size"] = (
                        most_common_size
                    )

                fixed_predictions.append(record)
        else:
            # If no file_size found, keep records as is
            fixed_predictions.extend(records)

    return fixed_predictions


def main():
    # Define file paths
    original_file = Path("validation_results/three_method_v1/raw_predictions.json")
    backup_file = Path("validation_results/three_method_v1/raw_predictions.json.backup")
    corrected_file = Path(
        "validation_results/three_method_v1/raw_predictions_corrected.json"
    )

    print("Loading predictions...")
    predictions = load_predictions(original_file)

    print(f"Backing up original file to {backup_file}")
    save_predictions(backup_file, predictions)

    print("Removing duplicate records...")
    unique_predictions = deduplicate_records(predictions)

    print("Fixing file size consistency...")
    fixed_predictions = fix_file_size_consistency(unique_predictions)

    print("Saving corrected predictions...")
    save_predictions(corrected_file, fixed_predictions)

    print(f"Done! Corrected file saved to {corrected_file}")
    print(f"Original count: {len(predictions)}")
    print(f"After deduplication: {len(unique_predictions)}")
    print(f"After fixing file sizes: {len(fixed_predictions)}")


if __name__ == "__main__":
    main()

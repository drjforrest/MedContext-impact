#!/usr/bin/env python3
"""Add misleading cases (authentic + true + misaligned) to dataset."""

import json
import shutil
from collections import Counter
from pathlib import Path


def add_misleading_cases():
    input_path = Path("data/three_dimensional_validation_v1.json")

    # Create backup before modifying
    backup_path = input_path.with_suffix(".json.bak")
    shutil.copy(input_path, backup_path)

    with open(input_path) as f:
        data = json.load(f)

    # Find "other_authentic" cases and reclassify some as "misleading"
    misleading_count = 0
    for item in data:
        gt = item["ground_truth"]

        # If authentic + high plausibility but misaligned → misleading
        if (
            gt.get("pixel_authentic")
            and gt.get("plausibility") == "high"
            and gt.get("alignment") == "misaligned"
        ):
            gt["label"] = "misleading"
            misleading_count += 1

    # Save updated dataset
    with open(input_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✓ Reclassified {misleading_count} cases as 'misleading'")
    print("\nNew distribution:")
    labels = [item["ground_truth"]["label"] for item in data]
    for label, count in sorted(Counter(labels).items()):
        print(f"  {label:25s}: {count:3d}")


if __name__ == "__main__":
    add_misleading_cases()

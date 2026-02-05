#!/usr/bin/env python3
"""Add misleading cases (authentic + true + misaligned) to dataset."""

import json
from collections import Counter


def add_misleading_cases():
    with open("data/three_dimensional_validation_v1.json") as f:
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
    with open("data/three_dimensional_validation_v1.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"✓ Reclassified {misleading_count} cases as 'misleading'")
    print("\nNew distribution:")
    labels = [item["ground_truth"]["label"] for item in data]
    for label, count in sorted(Counter(labels).items()):
        print(f"  {label:25s}: {count:3d}")


if __name__ == "__main__":
    add_misleading_cases()
    add_misleading_cases()
    add_misleading_cases()

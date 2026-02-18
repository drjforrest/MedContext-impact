#!/usr/bin/env python3
"""Create three-dimensional validation dataset from existing datasets."""

import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


def augment_contextual_dataset(contextual_path: Path) -> List[Dict[Any, Any]]:
    """Add pixel_authentic dimension to existing contextual dataset."""

    print(f"Loading authentic contextual dataset: {contextual_path}")
    with open(contextual_path, encoding="utf-8") as f:
        data = json.load(f)

    # Add pixel authenticity (all BTD images are authentic)
    for item in data:
        gt = item["ground_truth"]
        gt["pixel_authentic"] = True

        # Derive 3D label
        if (
            gt["pixel_authentic"]
            and gt["alignment"] == "aligned"
            and gt["plausibility"] == "high"
        ):
            gt["label"] = "legitimate"
        elif (
            gt["pixel_authentic"]
            and gt["alignment"] != "aligned"
            and gt["plausibility"] == "high"
        ):
            gt["label"] = "misleading"
        elif gt["pixel_authentic"] and gt["plausibility"] == "low":
            gt["label"] = "intentional_misinfo"
        else:
            gt["label"] = "other_authentic"

    print(f"✓ Augmented {len(data)} authentic image-claim pairs")
    return data


def create_tampered_entries(
    tampered_labels_path: Path, tampered_base_path: Path
) -> List[Dict[Any, Any]]:
    """Create tampered image entries with claims."""

    print(f"Loading tampered image labels: {tampered_labels_path}")
    with open(tampered_labels_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tampered_images = list(reader)

    # Medical claim templates by category
    claim_templates = {
        "true_aligned": [
            "CT scan showing clear tissue structure",
            "MRI scan of internal anatomy",
            "Medical imaging of organ tissue",
            "Diagnostic scan showing normal anatomy",
        ],
        "true_misaligned": [
            "This scan proves vaccines cause brain damage",
            "Clear evidence of radiation poisoning",
            "MRI shows electromagnetic hypersensitivity",
            "Scan proves microplastics in bloodstream",
        ],
        "false_aligned": [
            "Scan shows tumor growth in liver tissue",
            "Clear evidence of genetic mutation",
            "MRI reveals abnormal cellular structure",
            "CT shows metastatic cancer spread",
        ],
        "false_misaligned": [
            "5G radiation burns visible in scan",
            "Vaccine-induced neurological damage",
            "Graphene oxide crystals in bloodstream",
            "COVID vaccine spike protein aggregates",
        ],
    }

    tampered_entries = []
    target_per_category = 10  # 40 total tampered entries

    for category in claim_templates.keys():
        for i in range(target_per_category):
            if not tampered_images:
                break

            img = random.choice(tampered_images)
            tampered_images.remove(img)  # Avoid reuse

            claim = random.choice(claim_templates[category])
            veracity = "high" if "true" in category else "low"
            alignment = "aligned" if "aligned" in category else "misaligned"

            entry = {
                "image_id": f"tampered_exp1_{img['uuid']}_{img['slice']}",
                "image_path": str(
                    tampered_base_path
                    / "Experiment 1 - Blind"
                    / img["uuid"]
                    / f"{img['slice']}.dcm"
                ),
                "claim": claim,
                "ground_truth": {
                    "pixel_authentic": False,
                    "alignment": alignment,
                    "plausibility": veracity,
                    "is_misinformation": True,
                    "label": f"tampered_{category}",
                },
            }
            tampered_entries.append(entry)

    print(f"✓ Created {len(tampered_entries)} tampered image-claim pairs")
    return tampered_entries


def create_complete_3d_dataset():
    """Merge authentic contextual + tampered datasets."""

    contextual_path = Path("data/contextual_validation_v1.json")
    tampered_labels_path = Path(
        "data/deepfakes+medical+image+tamper+detection/data/Tampered Scans/labels_exp1.csv"
    )
    tampered_base_path = Path(
        "data/deepfakes+medical+image+tamper+detection/data/Tampered Scans"
    )

    # Check prerequisites
    if not contextual_path.exists():
        raise FileNotFoundError(f"Authentic dataset missing: {contextual_path}")
    if not tampered_labels_path.exists():
        raise FileNotFoundError(f"Tampered labels missing: {tampered_labels_path}")
    if not tampered_base_path.exists():
        raise FileNotFoundError(
            f"Tampered images directory missing: {tampered_base_path}"
        )

    # Create datasets
    authentic_data = augment_contextual_dataset(contextual_path)
    tampered_data = create_tampered_entries(tampered_labels_path, tampered_base_path)

    # Combine
    complete_dataset = authentic_data + tampered_data

    # Save
    output_path = Path("data/three_dimensional_validation_v1.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(complete_dataset, f, indent=2)

    # Analyze distribution
    label_counts = Counter(item["ground_truth"]["label"] for item in complete_dataset)

    print("\n" + "=" * 70)
    print("THREE-DIMENSIONAL DATASET CREATION COMPLETE")
    print("=" * 70)
    print(f"✓ Total samples: {len(complete_dataset)}")
    print(f"✓ Output saved: {output_path}")

    print("\nDataset distribution:")
    print("-" * 30)
    total = len(complete_dataset)
    for label, count in sorted(label_counts.items()):
        pct = 100 * count / total
        print(f"  {label:25s}: {count:3d} ({pct:5.1f}%)")

    print("\nNext steps:")
    print(
        "  1. Verify image paths exist: ls data/BTD data/deepfakes+medical+image+tamper+detection/data/Tampered Scans/"
    )
    print(
        "  2. Review sample entries: head -20 data/three_dimensional_validation_v1.json"
    )
    print(
        "  3. Run validation: uv run python -m app.validation.run_validation --dataset data/three_dimensional_validation_v1.json"
    )

    return output_path


def main():
    try:
        create_complete_3d_dataset()
        print("\n🎉 Dataset ready for validation!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Check that both datasets exist:")
        print("  data/contextual_validation_v1.json")
        print(
            "  data/deepfakes+medical+image+tamper+detection/data/Tampered Scans/labels_exp1.csv"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

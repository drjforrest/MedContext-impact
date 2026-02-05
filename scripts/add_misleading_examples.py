#!/usr/bin/env python3
"""Add misleading cases (authentic + true claim + misaligned context)."""

import json
from collections import Counter


def add_misleading_examples():
    with open("data/three_dimensional_validation_v1.json") as f:
        data = json.load(f)

    # Misleading claim templates (medically true advice, but can't be verified from image alone)
    misleading_claims = [
        "This shows why you should wear sunscreen",  # True advice, but can't determine UV cause from lesion
        "Wear protective equipment to avoid injuries like this",  # True advice, generic image
        "This is why regular screening is important",  # True advice, but overgeneralizes
        "Early detection could have prevented this",  # True principle, unverifiable claim
        "Proper hygiene prevents conditions like this",  # True advice, but causal link unclear
        "This demonstrates the importance of vaccination",  # True principle, but image doesn't prove it
        "Regular exercise helps prevent conditions like this",  # True advice, causal link unclear
        "This shows why diet is important for health",  # True principle, but image alone doesn't prove it
        "Genetic testing could have identified this risk",  # True capability, but unverifiable from image
        "This condition is preventable with lifestyle changes",  # True generally, but oversimplified
    ]

    # Take first 30 legitimate cases and duplicate them with misleading claims
    legitimate_cases = [
        item for item in data if item["ground_truth"]["label"] == "legitimate"
    ]

    new_misleading = []
    for i, item in enumerate(legitimate_cases[:30]):
        # Create misleading variant
        misleading_item = {
            "image_id": f"{item['image_id']}_misleading",
            "image_path": item["image_path"],
            "claim": misleading_claims[i % len(misleading_claims)],
            "ground_truth": {
                "alignment": "misaligned",
                "plausibility": "high",  # Claim itself is true medical advice
                "is_misinformation": True,  # But misleading because image doesn't support it
                "pixel_authentic": True,
                "label": "misleading",
            },
        }
        new_misleading.append(misleading_item)

    # Add to dataset
    data.extend(new_misleading)

    # Save updated dataset
    with open("data/three_dimensional_validation_v1.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"✓ Added {len(new_misleading)} misleading cases")
    print("\nNew distribution:")
    labels = [item["ground_truth"]["label"] for item in data]
    for label, count in sorted(Counter(labels).items()):
        pct = 100 * count / len(data)
        print(f"  {label:25s}: {count:3d} ({pct:5.1f}%)")

    print(f"\nTotal samples: {len(data)}")


if __name__ == "__main__":
    add_misleading_examples()

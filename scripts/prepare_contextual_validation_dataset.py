"""Helper script to prepare validation datasets for contextual signals.

This script helps convert medical image-claim pairs into the format expected
by the contextual signals validator.

Usage:
    python scripts/prepare_contextual_validation_dataset.py \
        --input-csv data/raw/image_claims.csv \
        --image-dir data/raw/images \
        --output validation_datasets/contextual_signals_v1.json
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def load_csv_dataset(csv_path: Path, image_dir: Path) -> List[Dict[str, Any]]:
    """Load dataset from CSV file.

    Expected CSV format:
        image_filename,claim,alignment,plausibility,is_misinformation
        image001.jpg,"This shows pneumonia",aligned,high,false
        image002.jpg,"Ivermectin cures COVID",misaligned,low,true
        ...

    Args:
        csv_path: Path to CSV file
        image_dir: Directory containing images

    Returns:
        List of dataset items in validator format
    """
    dataset = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            image_filename = row.get("image_filename")
            if not image_filename:
                continue

            image_path = image_dir / image_filename

            if not image_path.exists():
                print(f"Warning: Image not found: {image_path}")
                continue

            item = {
                "image_id": Path(image_filename).stem,
                "image_path": str(image_path.resolve()),
                "claim": row.get("claim", ""),
                "ground_truth": {
                    "alignment": row.get("alignment", "unclear").lower(),
                    "plausibility": row.get("plausibility", "medium").lower(),
                    "is_misinformation": row.get("is_misinformation", "").lower()
                    == "true",
                },
            }

            # Validate alignment label
            if item["ground_truth"]["alignment"] not in [
                "aligned",
                "misaligned",
                "partially_aligned",
                "unclear",
            ]:
                print(
                    f"Warning: Invalid alignment label '{item['ground_truth']['alignment']}' "
                    f"for {image_filename}. Setting to 'unclear'."
                )
                item["ground_truth"]["alignment"] = "unclear"

            # Validate plausibility label
            if item["ground_truth"]["plausibility"] not in [
                "high",
                "medium",
                "low",
            ]:
                print(
                    f"Warning: Invalid plausibility label '{item['ground_truth']['plausibility']}' "
                    f"for {image_filename}. Setting to 'medium'."
                )
                item["ground_truth"]["plausibility"] = "medium"

            dataset.append(item)

    return dataset


def load_jsonl_dataset(jsonl_path: Path) -> List[Dict[str, Any]]:
    """Load dataset from JSONL file.

    Expected JSONL format (one object per line):
        {"image_path": "path/to/img.jpg", "claim": "...", "ground_truth": {...}}
        {"image_path": "path/to/img2.jpg", "claim": "...", "ground_truth": {...}}

    Args:
        jsonl_path: Path to JSONL file

    Returns:
        List of dataset items in validator format
    """
    dataset = []

    with open(jsonl_path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"Warning: Invalid JSON on line {line_num}: {exc}")
                continue

            # Validate required fields
            if "image_path" not in item or "claim" not in item:
                print(
                    f"Warning: Missing required fields on line {line_num}. Skipping."
                )
                continue

            # Ensure ground_truth exists
            if "ground_truth" not in item:
                item["ground_truth"] = {
                    "alignment": "unclear",
                    "plausibility": "medium",
                    "is_misinformation": False,
                }

            dataset.append(item)

    return dataset


def create_sample_dataset() -> List[Dict[str, Any]]:
    """Create a sample dataset for testing.

    This is useful for initial validation testing before curating a full dataset.

    Returns:
        List of synthetic dataset items (without actual images)
    """
    return [
        {
            "image_id": "sample_001",
            "image_path": "data/samples/chest_xray_pneumonia.jpg",
            "claim": "Chest X-ray showing bilateral pneumonia infiltrates",
            "ground_truth": {
                "alignment": "aligned",
                "plausibility": "high",
                "is_misinformation": False,
            },
            "notes": "Correct diagnosis with clear visual evidence",
        },
        {
            "image_id": "sample_002",
            "image_path": "data/samples/brain_mri.jpg",
            "claim": "This MRI proves that vaccines cause autism",
            "ground_truth": {
                "alignment": "misaligned",
                "plausibility": "low",
                "is_misinformation": True,
            },
            "notes": "Generic brain MRI with false anti-vaccine claim",
        },
        {
            "image_id": "sample_003",
            "image_path": "data/samples/skin_rash.jpg",
            "claim": "Possible allergic reaction or contact dermatitis",
            "ground_truth": {
                "alignment": "partially_aligned",
                "plausibility": "medium",
                "is_misinformation": False,
            },
            "notes": "Vague claim that matches image but lacks specificity",
        },
        {
            "image_id": "sample_004",
            "image_path": "data/samples/ultrasound.jpg",
            "claim": "Abnormal mass detected",
            "ground_truth": {
                "alignment": "unclear",
                "plausibility": "medium",
                "is_misinformation": False,
            },
            "notes": "Insufficient information to verify claim",
        },
    ]


def validate_dataset(dataset: List[Dict[str, Any]]) -> bool:
    """Validate dataset format and contents.

    Args:
        dataset: List of dataset items

    Returns:
        True if valid, False otherwise
    """
    if not dataset:
        print("Error: Dataset is empty")
        return False

    required_fields = ["image_path", "claim", "ground_truth"]
    required_gt_fields = ["alignment", "plausibility"]

    for i, item in enumerate(dataset):
        # Check required fields
        for field in required_fields:
            if field not in item:
                print(f"Error: Item {i} missing required field '{field}'")
                return False

        # Check ground truth fields
        gt = item.get("ground_truth", {})
        for field in required_gt_fields:
            if field not in gt:
                print(
                    f"Error: Item {i} ground_truth missing required field '{field}'"
                )
                return False

        # Validate alignment values
        if gt["alignment"] not in [
            "aligned",
            "misaligned",
            "partially_aligned",
            "unclear",
        ]:
            print(
                f"Error: Item {i} has invalid alignment value '{gt['alignment']}'"
            )
            return False

        # Validate plausibility values
        if gt["plausibility"] not in ["high", "medium", "low"]:
            print(
                f"Error: Item {i} has invalid plausibility value '{gt['plausibility']}'"
            )
            return False

    print(f"✓ Dataset validation passed ({len(dataset)} items)")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Prepare validation dataset for contextual signals"
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        help="Path to input CSV file",
    )
    parser.add_argument(
        "--input-jsonl",
        type=Path,
        help="Path to input JSONL file",
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        help="Directory containing images (for CSV input)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output path for validation dataset JSON",
    )
    parser.add_argument(
        "--create-sample",
        action="store_true",
        help="Create sample dataset template",
    )

    args = parser.parse_args()

    # Load or create dataset
    if args.create_sample:
        print("Creating sample dataset...")
        dataset = create_sample_dataset()
        print(f"Created {len(dataset)} sample items")
        print(
            "\nNote: This is a template. Replace with actual images and ground truth labels."
        )

    elif args.input_csv:
        if not args.input_csv.exists():
            print(f"Error: CSV file not found: {args.input_csv}")
            return

        if not args.image_dir:
            print("Error: --image-dir required when using --input-csv")
            return

        if not args.image_dir.exists():
            print(f"Error: Image directory not found: {args.image_dir}")
            return

        print(f"Loading dataset from CSV: {args.input_csv}")
        dataset = load_csv_dataset(args.input_csv, args.image_dir)
        print(f"Loaded {len(dataset)} items")

    elif args.input_jsonl:
        if not args.input_jsonl.exists():
            print(f"Error: JSONL file not found: {args.input_jsonl}")
            return

        print(f"Loading dataset from JSONL: {args.input_jsonl}")
        dataset = load_jsonl_dataset(args.input_jsonl)
        print(f"Loaded {len(dataset)} items")

    else:
        print(
            "Error: Must specify --input-csv, --input-jsonl, or --create-sample"
        )
        return

    # Validate dataset
    if not validate_dataset(dataset):
        print("\nDataset validation failed. Please fix errors and try again.")
        return

    # Save dataset
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"\n✓ Dataset saved to: {args.output}")

    # Print statistics
    print("\nDataset Statistics:")
    print(f"  Total samples: {len(dataset)}")

    alignment_counts = {}
    plausibility_counts = {}
    misinformation_count = 0

    for item in dataset:
        gt = item["ground_truth"]

        # Count alignments
        alignment = gt["alignment"]
        alignment_counts[alignment] = alignment_counts.get(alignment, 0) + 1

        # Count plausibility
        plausibility = gt["plausibility"]
        plausibility_counts[plausibility] = (
            plausibility_counts.get(plausibility, 0) + 1
        )

        # Count misinformation
        if gt.get("is_misinformation"):
            misinformation_count += 1

    print("\n  Alignment distribution:")
    for alignment, count in sorted(alignment_counts.items()):
        print(f"    {alignment:20s}: {count:4d} ({count/len(dataset)*100:.1f}%)")

    print("\n  Plausibility distribution:")
    for plausibility, count in sorted(plausibility_counts.items()):
        print(
            f"    {plausibility:20s}: {count:4d} ({count/len(dataset)*100:.1f}%)"
        )

    print(
        f"\n  Misinformation cases: {misinformation_count} "
        f"({misinformation_count/len(dataset)*100:.1f}%)"
    )

    print("\nReady for validation! Run:")
    print(
        f"  python scripts/validate_contextual_signals.py --dataset {args.output}"
    )


if __name__ == "__main__":
    main()

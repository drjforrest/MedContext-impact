#!/usr/bin/env python3
"""Download and prepare Med-MMHL dataset for validation.

Med-MMHL is a multimodal medical misinformation dataset with ~1,778 image-claim pairs.
Data must be downloaded manually from Dropbox (no direct API).

Usage:
  1. Download from: https://www.dropbox.com/scl/fo/zvud6ta0uaqm2j1liupts/h?rlkey=zhychubvhspdxramyjdqjteqd&dl=0
  2. Extract to data/med-mmhl/ (or --output)
  3. Run this script to verify structure and create annotation template:

     python scripts/download_med_mmhl.py --output data/med-mmhl

Expected structure after extraction:
  data/med-mmhl/
    benchmarked_data/
      image_article/
        train.csv
        dev.csv
        test.csv
    images/
      2023-05-09_fakenews/
        LeadStories/
          *.png
        ...
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.validation.loaders import load_med_mmhl_dataset, create_annotation_template


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare Med-MMHL dataset for validation"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/med-mmhl"),
        help="Output directory (default: data/med-mmhl)",
    )
    parser.add_argument(
        "--create-template",
        action="store_true",
        help="Create annotation template for medical image filtering",
    )
    parser.add_argument(
        "--split",
        choices=["train", "dev", "test"],
        default="test",
        help="Split to load (default: test)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=0,
        help="Limit to N samples for quick verification (0=all)",
    )
    args = parser.parse_args()

    # Support both: benchmarked_data/image_article/ and image_article/ directly
    benchmark_path = args.output / "benchmarked_data"
    if not benchmark_path.exists():
        image_article = args.output / "image_article"
        if image_article.exists():
            benchmark_path = args.output
        else:
            print(f"Expected benchmark path not found: {benchmark_path}")
            print()
            print("Download Med-MMHL from Dropbox:")
            print("  https://www.dropbox.com/scl/fo/zvud6ta0uaqm2j1liupts/h?rlkey=zhychubvhspdxramyjdqjteqd&dl=0")
            print()
            print("Extract to:", args.output.resolve())
            print()
            print("Expected structure:")
            print(" ", args.output.name + "/")
            print("    benchmarked_data/ or image_article/")
            print("      image_article/")
            print("        train.csv, dev.csv, test.csv")
            print("    images/")
            print("      ...")
            return 1

    try:
        records = load_med_mmhl_dataset(
            benchmark_path=benchmark_path,
            split=args.split,
            base_image_dir=args.output,
        )
    except FileNotFoundError as e:
        print(e)
        return 1
    except ValueError as e:
        print(e)
        return 1

    if args.sample:
        records = records[: args.sample]

    # Count how many have resolvable images
    resolved = sum(1 for r in records if Path(r["image_path"]).exists())
    missing = len(records) - resolved

    print(f"Loaded {len(records)} claim-image pairs from {args.split} split")
    print(f"  Resolvable images: {resolved}")
    if missing > 0:
        print(f"  Missing images: {missing}")
        print("  (Image paths may need adjustment; check base_image_dir)")

    if records:
        fake_count = sum(1 for r in records if r["ground_truth"]["is_fake_claim"])
        print(f"  Fake claims: {fake_count} ({100*fake_count/len(records):.1f}%)")
    else:
        print("  No records with resolvable images.")

    if args.create_template:
        template_path = args.output / "image_type_annotations.json"
        create_annotation_template(records, template_path)
        print()
        print("Next: Edit image_type_annotations.json to mark medical images.")
        print("  Set is_authentic_medical_image: true for radiology, histology, etc.")
        print("  Then run validation with --require-medical to filter.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

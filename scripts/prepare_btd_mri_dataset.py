#!/usr/bin/env python3
"""
Prepare the BTD MRI dataset for validation.

Uses MRI_injection.csv and MRI_removal.csv to identify manipulated images
and pairs each with its authentic counterpart (same slice without suffix).

Output structure:
  <output_dir>/
    authentic/
    manipulated/
"""

import argparse
import csv
import shutil
from pathlib import Path


def _derive_authentic_path(manipulated_path: Path) -> Path:
    name = manipulated_path.name
    if name.startswith("injection_"):
        name = name.replace("injection_", "", 1)
    if name.endswith("_fake.png"):
        name = name.replace("_fake.png", ".png", 1)
    return manipulated_path.with_name(name)


def _read_manipulated_paths(csv_path: Path) -> list[Path]:
    rows: list[Path] = []
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rel_path = row.get("path")
            if not rel_path:
                continue
            rows.append(Path(rel_path))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert BTD MRI dataset into validation format"
    )
    parser.add_argument(
        "--source",
        type=str,
        default="data/BTD",
        help="BTD dataset root (default: data/BTD)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/validation/btd_mri",
        help="Output directory for validation dataset",
    )
    args = parser.parse_args()

    source_root = Path(args.source)
    mri_root = source_root / "MRI"
    output_root = Path(args.output)
    authentic_dir = output_root / "authentic"
    manipulated_dir = output_root / "manipulated"
    authentic_dir.mkdir(parents=True, exist_ok=True)
    manipulated_dir.mkdir(parents=True, exist_ok=True)

    injection_csv = mri_root / "MRI_injection.csv"
    removal_csv = mri_root / "MRI_removal.csv"
    if not injection_csv.exists() or not removal_csv.exists():
        raise SystemExit("Missing MRI_injection.csv or MRI_removal.csv in BTD/MRI.")

    manipulated_rel_paths = (
        _read_manipulated_paths(injection_csv)
        + _read_manipulated_paths(removal_csv)
    )

    copied_authentic = 0
    copied_manipulated = 0
    missing_pairs = 0

    for rel_path in manipulated_rel_paths:
        manipulated_path = source_root / rel_path
        if not manipulated_path.exists():
            continue
        target_manipulated = manipulated_dir / manipulated_path.name
        if not target_manipulated.exists():
            shutil.copy2(manipulated_path, target_manipulated)
            copied_manipulated += 1

        authentic_path = _derive_authentic_path(manipulated_path)
        if not authentic_path.exists():
            missing_pairs += 1
            continue
        target_authentic = authentic_dir / authentic_path.name
        if not target_authentic.exists():
            shutil.copy2(authentic_path, target_authentic)
            copied_authentic += 1

    print("✅ BTD MRI dataset prepared")
    print(f"  Authentic copied: {copied_authentic}")
    print(f"  Manipulated copied: {copied_manipulated}")
    if missing_pairs:
        print(f"  ⚠️ Missing authentic pairs: {missing_pairs}")
    print(f"  Output: {output_root}")
    print("\nNext step:")
    print(
        "  python scripts/validate_forensics.py --dataset "
        f"{output_root} --balance --bootstrap 1000 --output validation_results/btd_mri"
    )


if __name__ == "__main__":
    main()

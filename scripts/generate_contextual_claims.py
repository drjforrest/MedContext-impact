"""Generate contextual claims dataset from existing medical images.

This script samples medical images from your data/ folder and creates
both truthful and exaggerated/false claims for contextual validation.

Usage:
    python scripts/generate_contextual_claims.py \
        --num-images 50 \
        --output data/contextual_claims.csv
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from typing import Any


def get_image_type(path: Path) -> str:
    """Determine image type from path."""
    path_str = str(path).lower()

    if "mri" in path_str:
        if "breast" in path_str:
            return "breast_mri"
        elif "brain" in path_str:
            return "brain_mri"
        else:
            return "mri"
    elif "ct" in path_str:
        return "ct"
    else:
        return "medical"


def is_authentic(path: Path) -> bool:
    """Check if image is authentic (not manipulated)."""
    filename = path.name.lower()
    # Exclude injected/fake images
    if any(x in filename for x in ["fake", "injection_", "removal_"]):
        return False
    return True


def generate_claims_for_image(
    image_path: Path, image_type: str
) -> list[dict[str, Any]]:
    """Generate truthful and false claims for an image.

    Returns 3 variants per image type:
    - 1 aligned (truthful description)
    - 1 misaligned (false/exaggerated claim)
    - 1 partially_aligned (vague or unverifiable claim)
    """

    claims = []

    # Define claim templates by image type
    if image_type == "breast_mri":
        claims = [
            {
                "claim": "MRI scan of breast tissue",
                "alignment": "aligned",
                "plausibility": "high",
                "is_misinformation": False,
                "notes": "Accurate neutral description",
            },
            {
                "claim": "This MRI proves breast implants cause cancer",
                "alignment": "misaligned",
                "plausibility": "low",
                "is_misinformation": True,
                "notes": "False causation claim on authentic image",
            },
            {
                "claim": "Abnormal breast tissue detected",
                "alignment": "partially_aligned",
                "plausibility": "medium",
                "is_misinformation": False,
                "notes": "Vague claim without specific diagnosis",
            },
        ]

    elif image_type == "brain_mri":
        claims = [
            {
                "claim": "Brain MRI scan showing neurological anatomy",
                "alignment": "aligned",
                "plausibility": "high",
                "is_misinformation": False,
                "notes": "Accurate anatomical description",
            },
            {
                "claim": "MRI scan proves vaccines cause autism spectrum disorder",
                "alignment": "misaligned",
                "plausibility": "low",
                "is_misinformation": True,
                "notes": "Debunked anti-vaccine claim on real MRI",
            },
            {
                "claim": "Possible white matter changes visible on scan",
                "alignment": "partially_aligned",
                "plausibility": "medium",
                "is_misinformation": False,
                "notes": "Vague finding that may or may not be present",
            },
        ]

    elif image_type == "ct":
        claims = [
            {
                "claim": "CT scan of thoracic cavity",
                "alignment": "aligned",
                "plausibility": "high",
                "is_misinformation": False,
                "notes": "Accurate anatomical region description",
            },
            {
                "claim": "CT shows lung damage cured by ivermectin treatment",
                "alignment": "misaligned",
                "plausibility": "low",
                "is_misinformation": True,
                "notes": "False treatment claim on real CT scan",
            },
            {
                "claim": "Advanced stage lung cancer visible on scan",
                "alignment": "partially_aligned",
                "plausibility": "medium",
                "is_misinformation": False,
                "notes": "Specific diagnosis without confirming evidence",
            },
        ]

    elif image_type == "mri":
        claims = [
            {
                "claim": "MRI scan showing soft tissue detail",
                "alignment": "aligned",
                "plausibility": "high",
                "is_misinformation": False,
                "notes": "Generic but accurate MRI description",
            },
            {
                "claim": "Rare disease never before documented in medical literature",
                "alignment": "misaligned",
                "plausibility": "low",
                "is_misinformation": True,
                "notes": "Exaggerated extraordinary claim",
            },
            {
                "claim": "Possible abnormality detected in soft tissue",
                "alignment": "partially_aligned",
                "plausibility": "medium",
                "is_misinformation": False,
                "notes": "Vague finding without specific diagnosis",
            },
        ]

    else:  # Generic medical
        claims = [
            {
                "claim": "Medical imaging scan",
                "alignment": "aligned",
                "plausibility": "high",
                "is_misinformation": False,
                "notes": "Basic accurate description",
            },
            {
                "claim": "Proof that chemtrails cause respiratory disease",
                "alignment": "misaligned",
                "plausibility": "low",
                "is_misinformation": True,
                "notes": "Conspiracy theory misapplied to medical image",
            },
            {
                "claim": "Scan may show signs of chronic condition",
                "alignment": "partially_aligned",
                "plausibility": "medium",
                "is_misinformation": False,
                "notes": "Vague claim that could apply to many images",
            },
        ]

    # Add image path to each claim
    for claim in claims:
        claim["image_filename"] = str(image_path)

    return claims


def sample_images(data_dir: Path, num_images: int) -> list[Path]:
    """Sample diverse authentic images from dataset."""

    # Find all authentic images
    all_images = []

    # Sample from BTD MRI
    mri_dir = data_dir / "BTD" / "MRI"
    if mri_dir.exists():
        mri_images = [p for p in mri_dir.rglob("*.png") if is_authentic(p)]
        all_images.extend(mri_images)

    # Sample from BTD CT
    ct_dir = data_dir / "BTD" / "CT"
    if ct_dir.exists():
        ct_images = [
            p
            for p in ct_dir.rglob("*.png")
            if is_authentic(p) and "removal" not in str(p).lower()
        ]
        all_images.extend(ct_images)

    if not all_images:
        raise ValueError(f"No images found in {data_dir}")

    # Sample randomly
    if len(all_images) > num_images:
        sampled = random.sample(all_images, num_images)
    else:
        sampled = all_images[:num_images]

    print(f"Found {len(all_images)} total authentic images")
    print(f"Sampled {len(sampled)} images for claim generation")

    return sampled


def generate_dataset(data_dir: Path, num_images: int, output_path: Path):
    """Generate contextual claims dataset."""

    print(f"Sampling {num_images} images from {data_dir}...")
    images = sample_images(data_dir, num_images)

    print(f"\nGenerating claims for {len(images)} images...")
    all_rows = []

    for img_path in images:
        image_type = get_image_type(img_path)
        claims = generate_claims_for_image(img_path, image_type)
        all_rows.extend(claims)

    # Write to CSV
    print(f"\nWriting {len(all_rows)} claim entries to {output_path}...")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "image_filename",
            "claim",
            "alignment",
            "plausibility",
            "is_misinformation",
            "notes",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n✅ Dataset created: {output_path}")
    print(f"   - Total entries: {len(all_rows)}")
    print(f"   - Unique images: {len(images)}")
    print(f"   - Claims per image: ~{len(all_rows) / len(images):.1f}")

    # Print distribution
    aligned_count = sum(1 for r in all_rows if r["alignment"] == "aligned")
    misaligned_count = sum(1 for r in all_rows if r["alignment"] == "misaligned")
    partial_count = sum(1 for r in all_rows if r["alignment"] == "partially_aligned")

    print("\n   Distribution:")
    print(f"   - Aligned: {aligned_count} ({aligned_count / len(all_rows) * 100:.1f}%)")
    print(
        f"   - Misaligned: {misaligned_count} ({misaligned_count / len(all_rows) * 100:.1f}%)"
    )
    print(
        f"   - Partially aligned: {partial_count} ({partial_count / len(all_rows) * 100:.1f}%)"
    )

    misinformation_count = sum(1 for r in all_rows if r["is_misinformation"] is True)
    print(
        f"   - Misinformation cases: {misinformation_count} ({misinformation_count / len(all_rows) * 100:.1f}%)"
    )

    print("\nNext steps:")
    print(f"1. Review and edit the claims in {output_path}")
    print("2. Add more diverse examples if needed")
    print("3. Run preparation script:")
    print("   python scripts/prepare_contextual_validation_dataset.py \\")
    print(f"     --input-csv {output_path} \\")
    print("     --output data/contextual_validation_v1.json")
    print("4. Run validation:")
    print("   python scripts/validate_contextual_signals.py \\")
    print("     --dataset data/contextual_validation_v1.json \\")
    print("     --output-dir validation_results/contextual_v1")


def main():
    parser = argparse.ArgumentParser(
        description="Generate contextual claims dataset from existing images"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory containing medical images (default: data)",
    )
    parser.add_argument(
        "--num-images",
        type=int,
        default=50,
        help="Number of images to sample (default: 50)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/contextual_claims.csv"),
        help="Output CSV path (default: data/contextual_claims.csv)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    args = parser.parse_args()

    # Set random seed
    random.seed(args.seed)

    generate_dataset(
        data_dir=args.data_dir, num_images=args.num_images, output_path=args.output
    )


if __name__ == "__main__":
    main()

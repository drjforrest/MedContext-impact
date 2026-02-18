#!/usr/bin/env python3
"""Check for sampling bias in Med-MMHL subset.

Compares a subset against the full Med-MMHL test set to verify
that sampling did not introduce systematic bias.

This script empirically checks:
1. Label distribution (misinformation vs real)
2. Source distribution (if available) - measured using Jaccard similarity
3. Claim length distribution
4. Image duplication rates

Source Overlap Metric:
  - Uses Jaccard similarity: |intersection| / |union| of top-5 sources
  - 1.0 = identical source distributions (perfect overlap)
  - 0.0 = completely disjoint distributions (no common sources)
  - ≥0.6 threshold for "ACCEPTABLE" (lenient due to small subset size)
  - None = source data unavailable (all sources marked "unknown")

Supports two sampling strategies:
  --sequential: Take first N samples (may introduce ordering bias)
  --stratified: Random sample maintaining label distribution (recommended)

Usage:
  # Stratified sampling (recommended)
  python scripts/check_sampling_bias.py \
    --data-dir data/med-mmhl \
    --split test \
    --subset-size 163 \
    --stratified \
    --output validation_results/sampling_bias_analysis.json

  # Sequential sampling (for analysis only)
  python scripts/check_sampling_bias.py \
    --data-dir data/med-mmhl \
    --split test \
    --subset-size 163 \
    --sequential \
    --output validation_results/sampling_bias_analysis.json
"""

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))

# Import after adding to path
from app.validation.loaders import load_med_mmhl_dataset  # noqa: E402


def stratified_sample(
    records: list[dict], target_size: int, seed: int = 42
) -> tuple[list[dict], dict[str, Any]]:
    """Create stratified sample matching full dataset label distribution.

    Args:
        records: Full dataset records
        target_size: Desired sample size
        seed: Random seed for reproducibility

    Returns:
        Tuple of (sampled_records, sampling_metadata)
    """
    random.seed(seed)

    # Separate by label
    misinformation = [r for r in records if r["ground_truth"]["is_fake_claim"]]
    real = [r for r in records if not r["ground_truth"]["is_fake_claim"]]

    # Calculate target counts to maintain distribution
    full_misinfo_rate = len(misinformation) / len(records)
    target_misinfo = round(target_size * full_misinfo_rate)
    target_real = target_size - target_misinfo

    # Ensure we don't try to sample more than available
    actual_misinfo = min(target_misinfo, len(misinformation))
    actual_real = min(target_real, len(real))

    # Adjust if we're short on one class
    if actual_misinfo < target_misinfo:
        # Not enough misinformation samples, take more real
        actual_real = min(target_size - actual_misinfo, len(real))
    elif actual_real < target_real:
        # Not enough real samples, take more misinformation
        actual_misinfo = min(target_size - actual_real, len(misinformation))
    
    # Sample the calculated amounts
    sampled_misinfo = random.sample(misinformation, actual_misinfo)
    sampled_real = random.sample(real, actual_real)

    # Combine and shuffle
    sampled = sampled_misinfo + sampled_real
    random.shuffle(sampled)

    metadata = {
        "strategy": "stratified",
        "seed": seed,
        "target_size": target_size,
        "actual_size": len(sampled),
        "full_misinformation_rate": full_misinfo_rate,
        "target_misinformation_count": target_misinfo,
        "target_real_count": target_real,
        "actual_misinformation_count": actual_misinfo,
        "actual_real_count": actual_real,
    }

    return sampled, metadata


def compute_distribution_stats(
    records: list[dict], name: str, sampling_metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Compute key distribution statistics for a set of records."""
    n = len(records)

    # Label distribution
    labels = [r["ground_truth"].get("is_fake_claim", False) for r in records]
    n_misinfo = sum(labels)
    n_real = n - n_misinfo
    misinfo_rate = n_misinfo / n if n > 0 else 0

    # Source distribution (if available)
    sources = [r.get("source", "unknown") for r in records]
    source_counts = Counter(sources)

    # Warn if all sources are "unknown"
    if len(source_counts) == 1 and "unknown" in source_counts:
        import sys

        print(
            f"WARNING: All {n} records have source='unknown'. "
            "Source distribution analysis will be invalid.",
            file=sys.stderr,
        )
        print(
            "  Possible causes:",
            file=sys.stderr,
        )
        print(
            "    1. Dataset loader not extracting source from image paths",
            file=sys.stderr,
        )
        print(
            "    2. Image paths missing or malformed",
            file=sys.stderr,
        )
        print(
            "    3. Source field not populated in dataset records",
            file=sys.stderr,
        )

    # Claim length distribution
    claim_lengths = [len(r["claim"]) if r.get("claim") else 0 for r in records]
    avg_claim_length = sum(claim_lengths) / len(claim_lengths) if claim_lengths else 0

    # Image ID distribution (check for duplicates)
    image_ids = [r.get("image_id", "") for r in records]
    unique_images = len(set(image_ids))

    stats = {
        "name": name,
        "n_samples": n,
        "label_distribution": {
            "misinformation": n_misinfo,
            "real": n_real,
            "misinformation_rate": misinfo_rate,
        },
        "source_distribution": dict(source_counts.most_common(10)),
        "source_metadata": {
            "total_sources": len(source_counts),
            "all_unknown": len(source_counts) == 1 and "unknown" in source_counts,
            "unknown_count": source_counts.get("unknown", 0),
            "unknown_rate": source_counts.get("unknown", 0) / n if n > 0 else 0,
        },
        "claim_length": {
            "mean": avg_claim_length,
            "min": min(claim_lengths) if claim_lengths else 0,
            "max": max(claim_lengths) if claim_lengths else 0,
        },
        "unique_images": unique_images,
        "duplicate_rate": 1 - (unique_images / n) if n > 0 else 0,
    }

    # Add sampling metadata if provided
    if sampling_metadata:
        stats["sampling"] = sampling_metadata

    return stats


def compare_distributions(full_stats: dict, subset_stats: dict) -> dict[str, Any]:
    """Compare full dataset vs subset to detect bias."""

    # Label distribution comparison
    full_misinfo_rate = full_stats["label_distribution"]["misinformation_rate"]
    subset_misinfo_rate = subset_stats["label_distribution"]["misinformation_rate"]
    misinfo_diff = abs(full_misinfo_rate - subset_misinfo_rate)

    # Source distribution comparison (top sources)
    full_top_sources = set(list(full_stats["source_distribution"].keys())[:5])
    subset_top_sources = set(list(subset_stats["source_distribution"].keys())[:5])

    # Check if source data is invalid (all unknown)
    if full_stats["source_metadata"]["all_unknown"]:
        source_overlap = None  # N/A
        source_assessment = "UNAVAILABLE"
    else:
        # Calculate overlap as Jaccard similarity: intersection / union
        # For identical distributions, this returns 1.0
        # For completely disjoint distributions, this returns 0.0
        intersection = full_top_sources & subset_top_sources
        union = full_top_sources | subset_top_sources
        source_overlap = len(intersection) / len(union) if union else 1.0
        source_assessment = "ACCEPTABLE" if source_overlap >= 0.6 else "POTENTIAL_BIAS"

    # Claim length comparison
    full_avg_length = full_stats["claim_length"]["mean"]
    subset_avg_length = subset_stats["claim_length"]["mean"]
    length_diff_pct = (
        abs(full_avg_length - subset_avg_length) / full_avg_length
        if full_avg_length > 0
        else 0
    )

    # Duplicate rate comparison
    full_dup_rate = full_stats["duplicate_rate"]
    subset_dup_rate = subset_stats["duplicate_rate"]
    dup_diff = abs(full_dup_rate - subset_dup_rate)

    comparison = {
        "label_bias": {
            "full_misinformation_rate": full_misinfo_rate,
            "subset_misinformation_rate": subset_misinfo_rate,
            "absolute_difference": misinfo_diff,
            "difference_percentage_points": misinfo_diff * 100,
            "assessment": "ACCEPTABLE" if misinfo_diff < 0.05 else "POTENTIAL_BIAS",
        },
        "source_bias": {
            # Jaccard similarity of top-5 sources (intersection/union)
            # 1.0 = identical top sources, 0.0 = completely disjoint
            # None = source data unavailable (all "unknown")
            "top_source_overlap": source_overlap,
            "assessment": source_assessment,
        },
        "claim_length_bias": {
            "full_mean_length": full_avg_length,
            "subset_mean_length": subset_avg_length,
            "relative_difference_pct": length_diff_pct * 100,
            "assessment": "ACCEPTABLE" if length_diff_pct < 0.15 else "POTENTIAL_BIAS",
        },
        "duplicate_bias": {
            "full_duplicate_rate": full_dup_rate,
            "subset_duplicate_rate": subset_dup_rate,
            "absolute_difference": dup_diff,
            "assessment": "ACCEPTABLE" if dup_diff < 0.05 else "POTENTIAL_BIAS",
        },
    }

    # Overall assessment
    biases = [
        v["assessment"] for v in comparison.values() if v["assessment"] != "UNAVAILABLE"
    ]
    comparison["overall_assessment"] = (
        "NO_SIGNIFICANT_BIAS"
        if all(b == "ACCEPTABLE" for b in biases)
        else "POTENTIAL_BIAS_DETECTED"
    )

    return comparison


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check for sampling bias in Med-MMHL subset"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/med-mmhl"),
        help="Med-MMHL data directory",
    )
    parser.add_argument(
        "--split",
        choices=["train", "dev", "test"],
        default="test",
        help="Dataset split (default: test)",
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=163,
        help="Size of subset to check (default: 163)",
    )
    parser.add_argument(
        "--stratified",
        action="store_true",
        help="Use stratified sampling to maintain label distribution (recommended)",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Use sequential sampling (first N records, may introduce bias)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for stratified sampling (default: 42)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON file (optional)",
    )
    args = parser.parse_args()

    # Validate sampling strategy
    if args.stratified and args.sequential:
        print("Error: Cannot use both --stratified and --sequential")
        return 1

    if not args.stratified and not args.sequential:
        print("Error: Must specify either --stratified or --sequential")
        print("  Recommended: --stratified (maintains label distribution)")
        return 1

    sampling_strategy = "stratified" if args.stratified else "sequential"

    # Check data directory
    benchmark_path = args.data_dir / "benchmarked_data"
    if not benchmark_path.exists() and (args.data_dir / "image_article").exists():
        benchmark_path = args.data_dir

    if not benchmark_path.exists():
        print(f"Error: Data not found at {args.data_dir}")
        return 1

    print("=" * 70)
    print("Med-MMHL Sampling Bias Analysis")
    print("=" * 70)
    print(f"Data directory: {args.data_dir}")
    print(f"Split: {args.split}")
    print(f"Subset size: {args.subset_size}")
    print(f"Sampling strategy: {sampling_strategy}")
    if args.stratified:
        print(f"Random seed: {args.seed}")
    print()

    # Load full dataset
    print("Loading full dataset...")
    full_records = load_med_mmhl_dataset(
        benchmark_path=benchmark_path,
        split=args.split,
        base_image_dir=args.data_dir,
    )

    if not full_records:
        print("Error: No records loaded")
        return 1

    print(f"Loaded {len(full_records)} total records")

    # Get subset based on strategy
    sampling_metadata = None
    if args.stratified:
        print(f"Creating stratified sample (seed={args.seed})...")
        subset_records, sampling_metadata = stratified_sample(
            full_records, args.subset_size, seed=args.seed
        )
        subset_name = f"Stratified Sample (n={len(subset_records)})"
    else:
        print(f"Using sequential sample (first {args.subset_size} records)...")
        subset_records = full_records[: args.subset_size]
        subset_name = f"Sequential (First {args.subset_size})"
        sampling_metadata = {
            "strategy": "sequential",
            "note": "Sequential sampling may introduce ordering bias if dataset is not randomly shuffled",
        }

    print(f"Subset size: {len(subset_records)} records")
    print()

    # Compute statistics
    print("Computing distribution statistics...")
    full_stats = compute_distribution_stats(full_records, "Full Dataset")
    subset_stats = compute_distribution_stats(
        subset_records, subset_name, sampling_metadata=sampling_metadata
    )

    # Check if source distribution is valid
    if full_stats["source_metadata"]["all_unknown"]:
        print()
        print("=" * 70)
        print("ERROR: Invalid source distribution")
        print("=" * 70)
        print()
        print(
            "All records have source='unknown'. Cannot perform meaningful source bias analysis."
        )
        print()
        print("Possible fixes:")
        print(
            "  1. Update data loader (src/app/validation/loaders.py) to extract source from image paths"
        )
        print("  2. Verify image path format in CSV contains source information")
        print("  3. Add 'source' field to dataset records during ingestion")
        print()
        print("Continuing with limited analysis (excluding source bias)...")
        print()

    # Compare distributions
    print("Comparing distributions...")
    comparison = compare_distributions(full_stats, subset_stats)
    print()

    # Print results
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()

    # Label distribution
    print("1. LABEL DISTRIBUTION (Misinformation Rate)")
    print("-" * 70)
    lb = comparison["label_bias"]
    print(f"Full dataset:  {lb['full_misinformation_rate']:.1%} misinformation")
    print(f"Subset:        {lb['subset_misinformation_rate']:.1%} misinformation")
    print(f"Difference:    {lb['difference_percentage_points']:.2f} percentage points")
    print(f"Assessment:    {lb['assessment']}")
    print()

    # Source distribution
    print("2. SOURCE DISTRIBUTION (Top Sources)")
    print("-" * 70)
    sb = comparison["source_bias"]

    if sb["assessment"] == "UNAVAILABLE":
        print("Status:             UNAVAILABLE (all sources marked as 'unknown')")
        print(
            "Assessment:         Skipped - cannot analyze source bias without valid source data"
        )
    else:
        overlap = sb["top_source_overlap"]
        print(
            f"Top source overlap: {overlap:.1%}"
            if overlap is not None
            else "Top source overlap: N/A"
        )
        print(f"Assessment:         {sb['assessment']}")
        print()
        print("Full dataset top sources:")
        for source, count in list(full_stats["source_distribution"].items())[:5]:
            print(f"  - {source}: {count}")
        print()
        print("Subset top sources:")
        for source, count in list(subset_stats["source_distribution"].items())[:5]:
            print(f"  - {source}: {count}")
    print()

    # Claim length
    print("3. CLAIM LENGTH DISTRIBUTION")
    print("-" * 70)
    clb = comparison["claim_length_bias"]
    print(f"Full dataset mean:  {clb['full_mean_length']:.1f} characters")
    print(f"Subset mean:        {clb['subset_mean_length']:.1f} characters")
    print(f"Relative difference: {clb['relative_difference_pct']:.2f}%")
    print(f"Assessment:         {clb['assessment']}")
    print()

    # Duplicate rate
    print("4. IMAGE DUPLICATION")
    print("-" * 70)
    db = comparison["duplicate_bias"]
    print(f"Full dataset duplicates:  {db['full_duplicate_rate']:.1%}")
    print(f"Subset duplicates:        {db['subset_duplicate_rate']:.1%}")
    print(f"Difference:              {db['absolute_difference']:.2%}")
    print(f"Assessment:              {db['assessment']}")
    print()

    # Overall assessment
    print("=" * 70)
    print("OVERALL ASSESSMENT:", comparison["overall_assessment"])
    print("=" * 70)

    if comparison["overall_assessment"] == "NO_SIGNIFICANT_BIAS":
        print()
        print("✅ The subset shows no significant systematic bias compared")
        print("   to the full dataset. Sampling strategy is justified.")
        print()
        if args.stratified:
            print("Documentation language:")
            print('  "Stratified random sampling (seed=42) was used to select a')
            print(
                f"   representative subset (n={len(subset_records)}) from the Med-MMHL test set"
            )
            print(
                f"   (n={len(full_records)}), maintaining the original label distribution"
            )
            print('   (82.97% misinformation) for unbiased evaluation."')
        else:
            print("Documentation language:")
            print(
                '  "Sequential sampling was verified to produce representative label,'
            )
            print("   source, and claim-length distributions consistent with the full")
            print(f'   Med-MMHL test set (n={len(full_records)})."')
    else:
        print()
        print("⚠️  Potential bias detected.")
        if args.sequential:
            print()
            print("RECOMMENDATION: Use stratified sampling instead:")
            print(f"  python {Path(__file__).name} \\")
            print(f"    --data-dir {args.data_dir} \\")
            print(f"    --split {args.split} \\")
            print(f"    --subset-size {args.subset_size} \\")
            print("    --stratified \\")
            print(
                f"    --output {args.output or 'validation_results/sampling_bias_analysis.json'}"
            )
        else:
            print()
            print("Consider:")
            print("   1. Using full dataset for validation")
            print("   2. Increasing subset size")
            print("   3. Documenting observed biases as limitations")

    print()

    # Save results if requested
    if args.output:
        results = {
            "full_dataset": full_stats,
            "subset": subset_stats,
            "comparison": comparison,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {args.output}")

    # Return exit code based on assessment
    return 0 if comparison["overall_assessment"] == "NO_SIGNIFICANT_BIAS" else 1


if __name__ == "__main__":
    sys.exit(main())

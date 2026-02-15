#!/usr/bin/env python3
"""Check for sampling bias in Med-MMHL subset.

Compares the first 163 samples against the full Med-MMHL test set to verify
that sequential sampling did not introduce systematic bias.

This script empirically checks:
1. Label distribution (misinformation vs real)
2. Source distribution (if available)
3. Claim length distribution
4. Image duplication rates

Usage:
  python scripts/check_sampling_bias.py \
    --data-dir data/med-mmhl \
    --split test \
    --subset-size 163 \
    --output validation_results/sampling_bias_analysis.json

Results:
  The script found a 14 percentage point bias toward misinformation cases
  in the first 163 samples (96.9% vs 83.0% in full test set). This bias
  may inflate recall performance but makes precision more conservative.
  
  See docs/SAMPLING_BIAS_ANALYSIS.md for full interpretation.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))

from app.validation.loaders import load_med_mmhl_dataset


def compute_distribution_stats(records: list[dict], name: str) -> dict[str, Any]:
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
        "claim_length": {
            "mean": avg_claim_length,
            "min": min(claim_lengths) if claim_lengths else 0,
            "max": max(claim_lengths) if claim_lengths else 0,
        },
        "unique_images": unique_images,
        "duplicate_rate": 1 - (unique_images / n) if n > 0 else 0,
    }
    
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
    source_overlap = len(full_top_sources & subset_top_sources) / 5 if full_top_sources else 1.0
    
    # Claim length comparison
    full_avg_length = full_stats["claim_length"]["mean"]
    subset_avg_length = subset_stats["claim_length"]["mean"]
    length_diff_pct = abs(full_avg_length - subset_avg_length) / full_avg_length if full_avg_length > 0 else 0
    
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
            "top_source_overlap": source_overlap,
            "assessment": "ACCEPTABLE" if source_overlap >= 0.6 else "POTENTIAL_BIAS",
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
    biases = [v["assessment"] for v in comparison.values()]
    comparison["overall_assessment"] = "NO_SIGNIFICANT_BIAS" if all(b == "ACCEPTABLE" for b in biases) else "POTENTIAL_BIAS_DETECTED"
    
    return comparison


def main() -> int:
    parser = argparse.ArgumentParser(description="Check for sampling bias in Med-MMHL subset")
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
        "--output",
        type=Path,
        default=None,
        help="Output JSON file (optional)",
    )
    args = parser.parse_args()
    
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
    
    # Get subset (first N)
    subset_records = full_records[:args.subset_size]
    print(f"Analyzing first {len(subset_records)} records as subset")
    print()
    
    # Compute statistics
    print("Computing distribution statistics...")
    full_stats = compute_distribution_stats(full_records, "Full Dataset")
    subset_stats = compute_distribution_stats(subset_records, f"First {args.subset_size}")
    
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
    print(f"Top source overlap: {sb['top_source_overlap']:.1%}")
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
        print("✅ The first 163 samples show no significant systematic bias compared")
        print("   to the full dataset. Sequential sampling is justified.")
        print()
        print("Documentation language:")
        print('  "Sequential sampling was verified to produce representative label,')
        print('   source, and claim-length distributions consistent with the full')
        print(f'   Med-MMHL test set (n={len(full_records)})."')
    else:
        print()
        print("⚠️  Potential bias detected. Consider:")
        print("   1. Using randomized sampling instead")
        print("   2. Validating on full dataset")
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

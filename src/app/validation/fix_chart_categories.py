#!/usr/bin/env python3
"""Fix pipe-separated category values in chart_data.json files.

Normalizes entries with pipe-separated strings in "category" field
(e.g., "true|partially_true|false") to single discrete values.
When multiple options indicate uncertainty, resolves to middle category.
"""

import json
import sys
from pathlib import Path


def normalize_category(category: str, middle_option: str) -> str:
    """Normalize pipe-separated category to single discrete value.

    Args:
        category: Category value (may contain pipes)
        middle_option: Default middle/uncertain category to use

    Returns:
        Single discrete category value
    """
    if "|" in category:
        # Multiple options indicate uncertainty - use middle category
        return middle_option
    return category


def fix_distribution(distribution: list, middle_option: str) -> tuple[list, int]:
    """Fix category field in distribution entries.

    Args:
        distribution: List of score distribution entries
        middle_option: Default middle/uncertain category

    Returns:
        Tuple of (fixed_distribution, num_fixed)
    """
    num_fixed = 0
    fixed = []

    for entry in distribution:
        category = entry.get("category", "")

        # Normalize category if it contains pipes
        if "|" in category:
            category = normalize_category(category, middle_option)
            num_fixed += 1

        fixed_entry = {**entry, "category": category}
        fixed.append(fixed_entry)

    return fixed, num_fixed


def fix_chart_data(chart_data_path: Path, dry_run: bool = False) -> dict:
    """Fix pipe-separated categories in chart_data.json.

    Args:
        chart_data_path: Path to chart_data.json file
        dry_run: If True, report changes without writing

    Returns:
        Dictionary with fix statistics
    """
    with open(chart_data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    stats = {
        "veracity_fixed": 0,
        "alignment_fixed": 0,
        "total_veracity": 0,
        "total_alignment": 0,
    }

    # Fix veracity_distribution
    if "veracity_distribution" in data:
        veracity_dist = data["veracity_distribution"]
        stats["total_veracity"] = len(veracity_dist)

        fixed_veracity, num_fixed = fix_distribution(veracity_dist, "partially_true")
        data["veracity_distribution"] = fixed_veracity
        stats["veracity_fixed"] = num_fixed

    # Fix alignment_distribution
    if "alignment_distribution" in data:
        alignment_dist = data["alignment_distribution"]
        stats["total_alignment"] = len(alignment_dist)

        fixed_alignment, num_fixed = fix_distribution(
            alignment_dist, "partially_aligns"
        )
        data["alignment_distribution"] = fixed_alignment
        stats["alignment_fixed"] = num_fixed

    # Write back if not dry run
    if not dry_run:
        with open(chart_data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    return stats


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Fix pipe-separated categories in chart_data.json files"
    )
    parser.add_argument(
        "paths",
        type=Path,
        nargs="+",
        help="Path(s) to chart_data.json file(s) or directories containing them",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Report changes without modifying files"
    )

    args = parser.parse_args()

    # Collect all chart_data.json paths
    chart_data_files = []
    for path in args.paths:
        if path.is_file() and path.name == "chart_data.json":
            chart_data_files.append(path)
        elif path.is_dir():
            # Find chart_data.json in directory
            found = list(path.glob("**/chart_data.json"))
            chart_data_files.extend(found)

    if not chart_data_files:
        print("❌ No chart_data.json files found")
        sys.exit(1)

    print(f"Found {len(chart_data_files)} chart_data.json file(s)")
    if args.dry_run:
        print("🔍 DRY RUN MODE - no files will be modified\n")

    total_stats = {
        "files_processed": 0,
        "files_with_fixes": 0,
        "veracity_fixed": 0,
        "alignment_fixed": 0,
    }

    for chart_path in chart_data_files:
        try:
            relative_path = chart_path.relative_to(Path.cwd())
        except ValueError:
            relative_path = chart_path
        print(f"\n📄 {relative_path}")

        try:
            stats = fix_chart_data(chart_path, dry_run=args.dry_run)

            total_stats["files_processed"] += 1

            if stats["veracity_fixed"] > 0 or stats["alignment_fixed"] > 0:
                total_stats["files_with_fixes"] += 1
                total_stats["veracity_fixed"] += stats["veracity_fixed"]
                total_stats["alignment_fixed"] += stats["alignment_fixed"]

                print(
                    f"  ✏️  Fixed veracity entries: {stats['veracity_fixed']} / {stats['total_veracity']}"
                )
                print(
                    f"  ✏️  Fixed alignment entries: {stats['alignment_fixed']} / {stats['total_alignment']}"
                )

                if not args.dry_run:
                    print("  ✅ File updated")
            else:
                print("  ✓  No fixes needed")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Files with fixes: {total_stats['files_with_fixes']}")
    print(f"Total veracity entries fixed: {total_stats['veracity_fixed']}")
    print(f"Total alignment entries fixed: {total_stats['alignment_fixed']}")

    if args.dry_run:
        print("\n⚠️  DRY RUN - no files were modified")
        print("Run without --dry-run to apply changes")


if __name__ == "__main__":
    main()

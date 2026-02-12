"""Data loaders for validation datasets."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


def load_med_mmhl_dataset(
    benchmark_path: Path,
    split: str = "test",
    base_image_dir: Optional[Path] = None,
    annotations_path: Optional[Path] = None,
    require_medical: bool = False,
) -> List[Dict[str, Any]]:
    """Load Med-MMHL multimodal claim dataset.

    Med-MMHL structure (from Dropbox download):
      benchmarked_data/
        image_article/
          train.csv, dev.csv, test.csv
      images/  (or specified base_image_dir)
        2023-05-09_fakenews/LeadStories/551_32.png
        ...

    CSV columns: content, image, det_fake_label
    - content: claim text
    - image: string like "['/images/.../img.png']" or "['img1.png','img2.png']"
    - det_fake_label: 1=fake, 0=true

    Args:
        benchmark_path: Path to benchmarked_data/ (parent of image_article/)
        split: 'train', 'dev', or 'test'
        base_image_dir: Base directory for resolving image paths. If None, uses
            benchmark_path parent (assumes images/ is sibling of benchmarked_data/)
        annotations_path: Optional JSON with image_type annotations for filtering
            medical images. Format: {"claim_id": {"is_authentic_medical_image": true}}
        require_medical: If True and annotations_path provided, filter to only
            claim-image pairs with is_authentic_medical_image=true

    Returns:
        List of dicts with: image_id, image_path, claim, ground_truth
    """
    # Support both: benchmarked_data/image_article/ and image_article/ directly
    csv_path = benchmark_path / "image_article" / f"{split}.csv"
    if not csv_path.exists():
        alt_path = benchmark_path.parent / "image_article" / f"{split}.csv"
        if alt_path.exists():
            csv_path = alt_path
            benchmark_path = benchmark_path.parent
        else:
            raise FileNotFoundError(
                f"Med-MMHL {split} split not found: {csv_path}\n"
                "Download from: https://www.dropbox.com/scl/fo/zvud6ta0uaqm2j1liupts/h?rlkey=zhychubvhspdxramyjdqjteqd&dl=0"
            )

    df = pd.read_csv(csv_path, header=0, sep=",")
    if (
        "content" not in df.columns
        or "image" not in df.columns
        or "det_fake_label" not in df.columns
    ):
        raise ValueError(
            f"Expected columns content, image, det_fake_label. Got: {list(df.columns)}"
        )

    base = base_image_dir or (
        benchmark_path.parent
        if "benchmarked_data" in str(benchmark_path)
        else benchmark_path
    )
    if not base.exists():
        base = benchmark_path.parent

    annotations: Dict[str, Dict] = {}
    if annotations_path and annotations_path.exists():
        with open(annotations_path, encoding="utf-8") as f:
            annotations = json.load(f)

    records: List[Dict[str, Any]] = []
    for i, row in df.iterrows():
        content = str(row["content"]).strip()
        if not content:
            continue

        image_str = row["image"]
        image_paths = _parse_image_paths(image_str)

        # Defensively parse det_fake_label (handle NaN, None, invalid values)
        label_value = row["det_fake_label"]
        if pd.isna(label_value):
            # Skip rows with missing label
            continue
        try:
            is_fake = int(label_value) == 1
        except (ValueError, TypeError):
            # Invalid label value - skip this row
            continue

        for j, img_path in enumerate(image_paths):
            resolved = _resolve_image_path(img_path, base)
            if resolved is None:
                continue

            claim_id = f"med_mmhl_{split}_{i}_{j}"
            ann = annotations.get(claim_id, {})

            if require_medical and annotations:
                if not ann.get("is_authentic_medical_image", False):
                    continue

            records.append(
                {
                    "image_id": claim_id,
                    "image_path": str(resolved),
                    "claim": content,
                    "ground_truth": {
                        "is_fake_claim": is_fake,
                        "expected_misalignment": is_fake,
                        "is_misinformation": is_fake,
                        "pixel_authentic": True,  # Med-MMHL: most images are authentic
                        "plausibility": "low" if is_fake else "high",
                        "alignment": "misaligned" if is_fake else "aligned",
                    },
                    "annotations": ann,
                }
            )

    return records


def _parse_image_paths(image_str: str) -> List[str]:
    """Parse image column value to list of paths.

    Handles: "['path1', 'path2']", "['path1']", "/images/foo.png"
    Skips placeholder "['..']" which indicates no image.
    """
    s = str(image_str).strip()
    if not s:
        return []

    # Try to parse as Python list literal
    match = re.match(r"^\[(.*)\]$", s)
    if match:
        inner = match.group(1)
        parts = re.findall(r"['\"]([^'\"]+)['\"]", inner)
        if parts:
            # Filter out placeholder ".." (no image)
            return [p for p in parts if p.strip() != ".."]
        if inner.strip() and inner.strip() != "..":
            return [
                p.strip().strip("'\"").strip()
                for p in inner.split(",")
                if p.strip() != ".."
            ]

    if s.startswith("/") or "/" in s or s.endswith((".png", ".jpg", ".jpeg")):
        return [s] if s != ".." else []
    return []


def _resolve_image_path(path_str: str, base: Path) -> Optional[Path]:
    """Resolve image path relative to base directory."""
    if not path_str or path_str.strip() == "..":
        return None
    p = path_str.strip().strip("'\"")

    # Med-MMHL paths: "../images/2023-05-09_fakenews/LeadStories/3545_1.jpg"
    # Zip extracts to base/2023-05-09_fakenews/... (no images/ subfolder)
    if p.startswith("../images/"):
        p = p[10:]  # strip "../images/" (10 chars)
    elif p.startswith("/images/"):
        p = p[8:]
    elif p.startswith("images/"):
        p = p[7:]
    elif p.startswith("/"):
        p = p[1:]

    candidates = [
        base / p,
        base / "images" / p,
        base / "benchmarked_data" / ".." / p,
        Path(p),
    ]
    for c in candidates:
        try:
            resolved = c.resolve()
            if resolved.exists() and resolved.is_file():
                return resolved
        except (OSError, RuntimeError):
            pass
    return None


def create_annotation_template(records: List[Dict], output_path: Path) -> None:
    """Create a template annotations file for manual image-type labeling.

    Use this to annotate which images are truly medical (radiology, histology, etc.)
    vs decorative/screenshots.
    """
    template = {}
    for r in records:
        template[r["image_id"]] = {
            "image_type": "unknown",  # radiology_xray, histology, decorative, screenshot, non_medical
            "is_authentic_medical_image": None,  # True/False for filtering
            "notes": "",
        }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)
    print(f"Created annotation template: {output_path}")
    print("  Edit to set is_authentic_medical_image=True for medical images.")

#!/usr/bin/env python3
"""
Prepare the UCI Medical Image Tamper Detection dataset for validation.

This script converts DICOM slices in the "medical+image+tamper+dataset"
zip file into PNGs and generates a labels.csv compatible with the validation script.

Output structure:
  <output_dir>/
    images/
      exp1_<uuid>_<slice>.png
      exp2_<uuid>_<slice>.png
    labels.csv   # scan_id,is_tampered
"""

import argparse
import csv
import io
from pathlib import Path
from typing import Dict, Iterable, Set, Tuple
import zipfile

import numpy as np
from PIL import Image

try:
    import pydicom
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: pydicom. Install with:\n"
        "  uv run pip install pydicom"
    ) from exc


LABELS = {
    "exp1": "Tampered Scans/labels_exp1.csv",
    "exp2": "Tampered Scans/labels_exp2.csv",
}

EXPERIMENT_DIRS = {
    "exp1": "Tampered Scans/Experiment 1 - Blind/",
    "exp2": "Tampered Scans/Experiment 2 - Open/",
}


def parse_label_rows(csv_bytes: bytes) -> Set[Tuple[str, int]]:
    """Return a set of (uuid, slice_index) for tampered slices."""
    tampered: Set[Tuple[str, int]] = set()
    text = csv_bytes.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        uuid = (row.get("uuid") or "").strip()
        slice_val = row.get("slice")
        if not uuid or slice_val is None:
            continue
        try:
            slice_idx = int(str(slice_val).strip())
        except ValueError:
            continue
        tampered.add((uuid, slice_idx))
    return tampered


def dicom_to_png_bytes(dicom_bytes: bytes) -> bytes:
    dataset = pydicom.dcmread(io.BytesIO(dicom_bytes))
    pixel_array = dataset.pixel_array.astype(np.float32)

    # Normalize to 0-255 for PNG
    min_val = float(pixel_array.min())
    max_val = float(pixel_array.max())
    if max_val <= min_val:
        normalized = np.zeros_like(pixel_array, dtype=np.uint8)
    else:
        normalized = (pixel_array - min_val) / (max_val - min_val) * 255.0
        normalized = normalized.clip(0, 255).astype(np.uint8)

    image = Image.fromarray(normalized)
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def iter_dicom_entries(
    zip_file: zipfile.ZipFile,
    exp_key: str,
) -> Iterable[Tuple[str, str, int, bytes]]:
    prefix = EXPERIMENT_DIRS[exp_key]
    for name in zip_file.namelist():
        if not name.startswith(prefix) or not name.endswith(".dcm"):
            continue
        # Path looks like: Tampered Scans/Experiment X/UUID/SLICE.dcm
        parts = name[len(prefix):].split("/")
        if len(parts) < 2:
            continue
        uuid = parts[0]
        slice_name = Path(parts[1]).stem
        try:
            slice_idx = int(slice_name)
        except ValueError:
            continue
        with zip_file.open(name) as f:
            yield name, uuid, slice_idx, f.read()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert UCI tamper dataset zip to PNGs + labels.csv"
    )
    parser.add_argument(
        "--zip",
        required=True,
        help="Path to medical-image-tamper-detection data.zip",
    )
    parser.add_argument(
        "--output",
        default="data/validation/uci_tamper",
        help="Output directory for images/ and labels.csv",
    )
    parser.add_argument(
        "--experiments",
        default="exp1,exp2",
        help="Comma-separated list: exp1,exp2",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=0,
        help="Optional cap on number of images processed (0 = no cap)",
    )
    args = parser.parse_args()

    zip_path = Path(args.zip)
    output_dir = Path(args.output)
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    exp_list = [e.strip() for e in args.experiments.split(",") if e.strip()]
    for exp in exp_list:
        if exp not in LABELS:
            raise SystemExit(f"Unknown experiment '{exp}'. Use exp1, exp2.")

    labels_rows = []
    processed = 0

    with zipfile.ZipFile(zip_path) as zf:
        tampered_maps: Dict[str, Set[Tuple[str, int]]] = {}
        for exp in exp_list:
            label_bytes = zf.read(LABELS[exp])
            tampered_maps[exp] = parse_label_rows(label_bytes)

        for exp in exp_list:
            for _, uuid, slice_idx, dcm_bytes in iter_dicom_entries(zf, exp):
                scan_id = f"{exp}_{uuid}_{slice_idx}"
                out_path = images_dir / f"{scan_id}.png"

                if not out_path.exists():
                    png_bytes = dicom_to_png_bytes(dcm_bytes)
                    out_path.write_bytes(png_bytes)

                is_tampered = 1 if (uuid, slice_idx) in tampered_maps[exp] else 0
                labels_rows.append({"scan_id": scan_id, "is_tampered": str(is_tampered)})
                processed += 1

                if args.max_images and processed >= args.max_images:
                    break
            if args.max_images and processed >= args.max_images:
                break

    # Write labels.csv
    labels_path = output_dir / "labels.csv"
    with labels_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["scan_id", "is_tampered"])
        writer.writeheader()
        writer.writerows(labels_rows)

    print(f"✅ Wrote {processed} images to {images_dir}")
    print(f"✅ Labels: {labels_path}")
    print("Next step:")
    print(
        "  python scripts/validate_forensics.py --dataset "
        f"{output_dir} --bootstrap 1000 --output validation_results/uci"
    )


if __name__ == "__main__":
    main()

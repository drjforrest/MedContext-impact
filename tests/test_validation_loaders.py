"""Tests for validation loaders."""

import json
from pathlib import Path

import pytest

# Add src to path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.validation.loaders import (
    load_med_mmhl_dataset,
    _parse_image_paths,
    _resolve_image_path,
    create_annotation_template,
)


class TestParseImagePaths:
    def test_list_literal(self):
        assert _parse_image_paths("['/images/foo.png']") == ["/images/foo.png"]
        assert _parse_image_paths("['a.png', 'b.png']") == ["a.png", "b.png"]

    def test_single_path(self):
        assert _parse_image_paths("/images/foo.png") == ["/images/foo.png"]

    def test_empty(self):
        assert _parse_image_paths("") == []
        assert _parse_image_paths("[]") == []


class TestResolveImagePath:
    def test_relative_to_base(self, tmp_path):
        (tmp_path / "images" / "sub").mkdir(parents=True)
        (tmp_path / "images" / "sub" / "img.png").touch()
        resolved = _resolve_image_path("sub/img.png", tmp_path / "images")
        assert resolved is not None
        assert resolved.exists()

    def test_leading_images_stripped(self, tmp_path):
        (tmp_path / "images" / "foo").mkdir(parents=True)
        (tmp_path / "images" / "foo" / "x.png").touch()
        resolved = _resolve_image_path("/images/foo/x.png", tmp_path)
        assert resolved is not None
        assert resolved.exists()


class TestLoadMedMMHL:
    def test_loads_csv(self, tmp_path):
        """Test loader with minimal CSV."""
        benchmark = tmp_path / "benchmarked_data" / "image_article"
        benchmark.mkdir(parents=True)
        img_dir = tmp_path / "images" / "test"
        img_dir.mkdir(parents=True)
        (img_dir / "x.png").touch()

        csv_path = benchmark / "test.csv"
        # Use path format matching Med-MMHL: /images/test/x.png
        # Image column: [/images/path] format (no inner quotes to avoid CSV escaping)
        csv_path.write_text(
            "content,image,det_fake_label\n"
            'Claim one,"[/images/test/x.png]",0\n'
            'Fake claim,"[/images/test/x.png]",1\n'
        )

        records = load_med_mmhl_dataset(
            benchmark_path=tmp_path / "benchmarked_data",
            split="test",
            base_image_dir=tmp_path,
        )
        assert len(records) >= 1, f"Expected records, got {records}"
        assert records[0]["claim"] == "Claim one"
        assert records[0]["ground_truth"]["is_fake_claim"] is False

    def test_raises_when_missing(self):
        with pytest.raises(FileNotFoundError):
            load_med_mmhl_dataset(
                benchmark_path=Path("/nonexistent/benchmarked_data"),
                split="test",
            )


class TestCreateAnnotationTemplate:
    def test_creates_template(self, tmp_path):
        records = [
            {"image_id": "id1", "claim": "c1", "ground_truth": {}},
            {"image_id": "id2", "claim": "c2", "ground_truth": {}},
        ]
        out = tmp_path / "ann.json"
        create_annotation_template(records, out)
        data = json.loads(out.read_text())
        assert "id1" in data
        assert data["id1"]["image_type"] == "unknown"
        assert data["id1"]["is_authentic_medical_image"] is None

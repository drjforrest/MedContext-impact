from app.core.config import settings
from app.forensics.service import run_forensics


def test_run_forensics_skipped_when_disabled(sample_image_bytes):
    original = settings.enable_forensics
    settings.enable_forensics = False
    try:
        result = run_forensics(sample_image_bytes)
    finally:
        settings.enable_forensics = original

    assert result["status"] == "skipped"
    assert "disabled" in result["detail"].lower()


def test_run_forensics_enabled_returns_selected_layers(sample_image_bytes):
    original = settings.enable_forensics
    settings.enable_forensics = True
    try:
        result = run_forensics(sample_image_bytes, layers=["layer_1", "layer_3"])
    finally:
        settings.enable_forensics = original

    assert result["status"] == "completed"
    assert result["selected_layers"] == ["layer_1", "layer_3"]
    layers = result["layers"]
    assert "layer_1" in layers
    assert "layer_3" in layers
    assert "layer_2" not in layers
    assert "copy_move_score" in layers["layer_1"]["details"]
    assert "has_exif" in layers["layer_3"]["details"]

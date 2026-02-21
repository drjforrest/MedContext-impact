"""MedContext validation module.

Provides dataset loaders, metrics, chart generation, threshold optimization,
sampling bias analysis, and the main validation runner for Med-MMHL benchmarking.

Run the main validation with:
    uv run python -m app.validation.run_validation --help
"""

__all__ = [
    "load_med_mmhl_dataset",
    "compute_three_dimensional_metrics",
    "generate_charts",
    "run_validation",
]

from app.validation.chart_generation import generate_charts
from app.validation.loaders import load_med_mmhl_dataset
from app.validation.metrics import compute_three_dimensional_metrics


def __getattr__(name: str):
    if name == "load_med_mmhl_dataset":
        from app.validation.loaders import load_med_mmhl_dataset

        return load_med_mmhl_dataset
    if name == "compute_three_dimensional_metrics":
        from app.validation.metrics import compute_three_dimensional_metrics

        return compute_three_dimensional_metrics
    if name == "generate_charts":
        from app.validation.chart_generation import generate_charts

        return generate_charts
    if name == "run_validation":
        from app.validation.run_validation import run_validation

        return run_validation
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

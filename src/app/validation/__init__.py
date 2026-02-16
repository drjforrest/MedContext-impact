"""MedContext validation module.

Supports validation on Med-MMHL and (future) AMMeBa datasets.
See scripts/validate_med_mmhl.py for the main validation runner.
"""

__all__ = [
    "load_med_mmhl_dataset",
    "compute_three_dimensional_metrics",
]


def __getattr__(name: str):
    if name == "load_med_mmhl_dataset":
        from app.validation.loaders import load_med_mmhl_dataset

        return load_med_mmhl_dataset
    if name == "compute_three_dimensional_metrics":
        from app.validation.metrics import compute_three_dimensional_metrics

        return compute_three_dimensional_metrics
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

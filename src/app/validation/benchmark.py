#!/usr/bin/env python3
"""
Performance benchmark runner for MedContext.

Measures end-to-end latency, per-step timing, throughput, and API call counts.
Defaults to stubbed MedGemma/LLM to avoid external dependencies.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List

import numpy as np

from app.clinical.llm_client import LlmResult
from app.clinical.medgemma_client import MedGemmaResult
from app.core.config import settings
from app.forensics.service import run_forensics
from app.orchestrator.agent import MedContextAgent
from app.provenance.service import build_provenance
from app.reverse_search.service import get_reverse_search_results, run_reverse_search


@dataclass(frozen=True)
class BenchmarkTimings:
    total_ms: float
    triage_ms: float
    reverse_search_ms: float
    forensics_ms: float
    provenance_ms: float
    synthesis_ms: float
    postprocess_ms: float


class StubMedGemma:
    provider = "stub"
    model = "stub-medgemma"

    def analyze_image(
        self, image_bytes: bytes, prompt: str | None = None
    ) -> MedGemmaResult:
        del image_bytes, prompt
        output = {
            "required_investigation": ["reverse_search", "forensics", "provenance"],
            "primary_findings": "Stub triage output for benchmarking.",
            "plausibility": "medium",
            "context_risk": "medium",
            "claim_type": "caption",
        }
        return MedGemmaResult(
            provider=self.provider,
            model=self.model,
            output=output,
            raw_text=json.dumps(output),
        )


class StubLlm:
    provider = "stub"
    model = "stub-llm"

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 900,
    ) -> LlmResult:
        del prompt, system, model, temperature, max_tokens
        output = {
            "part_1": {"image_description": "Stub description for benchmarking."},
            "part_2": {
                "summary": "Stub synthesis summary.",
                "alignment": "unclear",
                "confidence": 0.5,
                "verdict": "uncertain",
                "claim_risk": "medium",
            },
        }
        return LlmResult(
            provider=self.provider,
            model=self.model,
            output=output,
            raw_text=json.dumps(output),
        )


def _iter_image_paths(root: Path) -> Iterable[Path]:
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        for path in root.rglob(ext):
            yield path


def load_images(dataset_path: Path, limit: int) -> list[bytes]:
    if (dataset_path / "images").exists():
        dataset_path = dataset_path / "images"
    images: list[bytes] = []
    for path in _iter_image_paths(dataset_path):
        images.append(path.read_bytes())
        if len(images) >= limit:
            break
    if not images:
        raise ValueError(f"No images found under {dataset_path}")
    return images


def percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    array = np.array(values, dtype=float)
    return float(np.percentile(array, pct))


def benchmark_image(
    agent: MedContextAgent, image_bytes: bytes, context: str
) -> BenchmarkTimings:
    start_total = time.perf_counter()

    start = time.perf_counter()
    triage = agent._triage(image_bytes, context=context)
    triage_ms = (time.perf_counter() - start) * 1000

    tools = agent._extract_required_tools(triage)

    reverse_ms = 0.0
    forensics_ms = 0.0
    provenance_ms = 0.0
    tool_results: dict[str, Any] = {}

    image_id = agent._generate_image_id()

    for tool in tools:
        if tool == "reverse_search":
            start = time.perf_counter()
            tool_results[tool] = run_reverse_search(
                image_id=image_id, image_bytes=image_bytes
            )
            _ = get_reverse_search_results(tool_results[tool].image_id)
            reverse_ms = (time.perf_counter() - start) * 1000
        elif tool == "forensics":
            start = time.perf_counter()
            layers = agent._select_forensics_layers(triage)
            tool_results[tool] = run_forensics(image_bytes=image_bytes, layers=layers)
            forensics_ms = (time.perf_counter() - start) * 1000
        elif tool == "provenance":
            start = time.perf_counter()
            tool_results[tool] = build_provenance(
                image_id=image_id, image_bytes=image_bytes
            )
            provenance_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    synthesis = agent._synthesize(image_bytes, triage, tool_results, context=context)
    synthesis_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    _ = agent._postprocess_synthesis(
        synthesis,
        image_bytes=image_bytes,
        image_id=None,
        context=context,
        triage=triage,
        tool_results=tool_results,
    )
    postprocess_ms = (time.perf_counter() - start) * 1000

    total_ms = (time.perf_counter() - start_total) * 1000

    return BenchmarkTimings(
        total_ms=total_ms,
        triage_ms=triage_ms,
        reverse_search_ms=reverse_ms,
        forensics_ms=forensics_ms,
        provenance_ms=provenance_ms,
        synthesis_ms=synthesis_ms,
        postprocess_ms=postprocess_ms,
    )


def summarize(values: List[float]) -> dict[str, float]:
    if not values:
        print("⚠️  No timing samples available for summary.")
        return {"mean_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0}
    if len(values) < 20:
        print(f"⚠️  Small sample size ({len(values)}); percentiles may be noisy.")

    array = np.array(values, dtype=float)
    mean_ms = float(np.mean(array))
    p50_ms = float(np.percentile(array, 50))
    p95_ms = float(np.percentile(array, 95))

    if p95_ms < p50_ms:
        print(f"⚠️  Unexpected ordering: p95 < p50 ({p95_ms:.6f} < {p50_ms:.6f})")
    if p95_ms < mean_ms:
        print(f"⚠️  Unexpected ordering: p95 < mean ({p95_ms:.6f} < {mean_ms:.6f})")

    return {
        "mean_ms": mean_ms,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run MedContext performance benchmarks."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/validation/uci_tamper",
        help="Path to dataset (defaults to UCI tamper dataset).",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=50,
        help="Number of images to benchmark (default: 50).",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=3,
        help="Warmup iterations before measuring (default: 3).",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["stub", "live"],
        default="stub",
        help="Benchmark mode: stub (no external calls) or live (real providers).",
    )
    parser.add_argument(
        "--fallback-provider",
        type=str,
        default="vertex,huggingface",
        help="Comma-separated fallback MedGemma providers if live warmup fails.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="validation_results/performance",
        help="Output directory for benchmark report.",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    images = load_images(dataset_path, args.samples + args.warmup)
    benchmark_images = images[: args.samples]
    warmup_images = images[args.samples : args.samples + args.warmup]

    original_serp_api_key: str | None = None
    original_medgemma_provider = settings.medgemma_provider
    if args.mode != "live":
        original_serp_api_key = settings.serp_api_key
        settings.serp_api_key = ""

    try:
        if args.mode == "live":
            agent = MedContextAgent()
            mode_detail = "live"
        else:
            agent = MedContextAgent(medgemma=StubMedGemma(), llm=StubLlm())
            mode_detail = "stub"

        context = "Benchmark run for performance metrics."

        timings: list[BenchmarkTimings] = []
        errors: list[str] = []
        fallback_attempts: list[dict[str, str]] = []

        # Warmup
        for image_bytes in warmup_images:
            try:
                _ = benchmark_image(agent, image_bytes, context=context)
            except Exception as exc:
                errors.append(str(exc))
                break

        if errors and args.mode == "live" and settings.medgemma_provider == "vllm":
            candidates = [
                entry.strip().lower()
                for entry in args.fallback_provider.split(",")
                if entry.strip()
            ]
            for fallback in candidates:
                if fallback == "huggingface" and not settings.medgemma_hf_token:
                    continue
                if fallback == "vertex" and not settings.medgemma_vertex_endpoint:
                    continue
                settings.medgemma_provider = fallback
                agent = MedContextAgent()
                mode_detail = f"live_fallback_{fallback}"
                errors.clear()
                for image_bytes in warmup_images:
                    try:
                        _ = benchmark_image(agent, image_bytes, context=context)
                    except Exception as exc:
                        errors.append(str(exc))
                        break
                if not errors:
                    break
                fallback_attempts.append(
                    {"provider": fallback, "error": errors[0] if errors else "unknown"}
                )
        start_total = time.perf_counter()
        for image_bytes in benchmark_images:
            try:
                timings.append(benchmark_image(agent, image_bytes, context=context))
            except Exception as exc:
                errors.append(str(exc))
        elapsed_total = time.perf_counter() - start_total

        totals = [t.total_ms for t in timings]
        triage = [t.triage_ms for t in timings]
        reverse = [t.reverse_search_ms for t in timings]
        forensics = [t.forensics_ms for t in timings]
        provenance = [t.provenance_ms for t in timings]
        synthesis = [t.synthesis_ms for t in timings]
        postprocess = [t.postprocess_ms for t in timings]

        throughput = (len(timings) / elapsed_total) if elapsed_total else 0.0

        serpapi_enabled = bool(settings.serp_api_key)

        report = {
            "benchmark_summary": {
                "dataset": str(dataset_path),
                "samples": len(timings),
                "warmup": len(warmup_images),
                "mode": mode_detail,
                "serpapi_enabled": serpapi_enabled,
                "medgemma_provider": settings.medgemma_provider,
                "llm_provider": settings.llm_provider,
            },
            "errors": {
                "count": len(errors),
                "samples": errors[:5],
            },
            "fallback_attempts": fallback_attempts,
            "latency_ms": {
                "total": summarize(totals),
                "triage": summarize(triage),
                "reverse_search": summarize(reverse),
                "forensics": summarize(forensics),
                "provenance": summarize(provenance),
                "synthesis": summarize(synthesis),
                "postprocess": summarize(postprocess),
            },
            "throughput": {
                "images_per_second": throughput,
                "total_seconds": elapsed_total,
            },
            "cost_drivers": {
                "medgemma_calls_per_image": 1,
                "llm_calls_per_image": 1,
                "reverse_search_calls_per_image": 1,
                "provenance_calls_per_image": 1,
                "forensics_calls_per_image": 1,
            },
        }

        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "performance_benchmark.json"
        output_path.write_text(json.dumps(report, indent=2))

        print("Performance benchmark complete.")
        print(json.dumps(report, indent=2))
        print(f"\nReport saved to: {output_path}")
    finally:
        if original_serp_api_key is not None:
            settings.serp_api_key = original_serp_api_key
        settings.medgemma_provider = original_medgemma_provider


if __name__ == "__main__":
    main()

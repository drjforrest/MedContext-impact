#!/usr/bin/env python3
"""Three-method medical misinformation validation.

Compares:
1. Pixel forensics (tampering detection)
2. Contextual analysis (veracity + alignment)
3. Combined approach
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.clinical.medgemma_client import MedGemmaClient
from app.forensics.service import _run_layer_1


def _read_image_bytes(path: Path) -> bytes:
    """Read image file as raw bytes.

    DICOM files are passed through as-is so that _run_layer_1 can use the
    native DICOM forensics path (header integrity + copy-move on the pixel array).
    Standard image formats (PNG, JPEG, etc.) are also read as-is.
    """
    return path.read_bytes()


class ThreeMethodValidator:
    """Compare pixel forensics vs contextual vs combined misinformation detection."""

    def __init__(self, dataset_path: Path, output_dir: Path):
        self.dataset_path = dataset_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.medgemma = MedGemmaClient()
        self.results = []
        self.skipped_missing = 0
        self.skipped_errors = 0

    def load_dataset(self) -> List[Dict]:
        """Load 3D validation dataset."""
        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Dataset file not found: {self.dataset_path}")
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in dataset file {self.dataset_path}: {str(e)}"
            )
        except (KeyError, TypeError) as e:
            raise ValueError(
                f"Malformed dataset structure in {self.dataset_path}: {str(e)}"
            )

        # Validate that the result is a list of dictionaries
        if not isinstance(data, list):
            raise ValueError(
                f"Dataset file {self.dataset_path} does not contain a list at the top level"
            )

        if not all(isinstance(item, dict) for item in data):
            raise ValueError(
                f"Dataset file {self.dataset_path} does not contain a list of dictionaries"
            )

        return data

    def simple_pixel_forensics(self, image_bytes: bytes) -> Dict[str, Any]:
        """Pixel forensics baseline using copy-move detection.

        DICOM files use native DICOM header + pixel forensics.
        Standard images (PNG/JPEG) use normalized grayscale copy-move detection.
        Verdict MANIPULATED → pixel_authentic=False, AUTHENTIC → True.
        """
        try:
            layer1_result = _run_layer_1(image_bytes)

            pixel_authentic = layer1_result.verdict != "MANIPULATED"

            return {
                "pixel_authentic": pixel_authentic,
                "confidence": layer1_result.confidence,
                "method": "pixel_forensics",
                "layer1_verdict": layer1_result.verdict,
                "layer1_details": layer1_result.details,
            }
        except Exception as e:
            print(f"Pixel forensics error: {e}")
            return {
                "pixel_authentic": False,
                "confidence": 0.0,
                "method": "pixel_forensics",
                "error": str(e),
            }

    def contextual_analysis(self, image_bytes: bytes, claim: str) -> Dict[str, Any]:
        """MedGemma contextual analysis (veracity + alignment only).

        This extracts ONLY:
        - Veracity (plausibility): Is the claim medically sound?
        - Alignment: Does the image support the claim?

        Excludes:
        - Genealogy (reverse image search)
        - Source reputation
        """
        try:
            # Direct MedGemma analysis without agent orchestration
            result = self._direct_medgemma_analysis(image_bytes, claim)

            # Extract veracity and alignment from direct analysis
            veracity_score = result.get("veracity_score", 0.5)
            alignment_score = result.get("alignment_score", 0.5)

            # Check if analysis failed (indicated by default failure scores)
            analysis_failed = veracity_score == 0.0 and alignment_score == 0.0

            # Simple combination: both need to be high to be legitimate
            # If either is low, it's misleading/misinformation
            overall_score = min(veracity_score, alignment_score)
            is_misleading = overall_score < 0.5

            # Get the 3-level semantic variables
            veracity_category = result.get("veracity_category", "partially_true")
            alignment_category = result.get("alignment_category", "partially_aligns")

            # Prepare the return dictionary with updated metrics
            return_data = {
                "veracity_score": veracity_score,
                "veracity_category": veracity_category,  # 3-level semantic: true/partially_true/false
                "alignment_score": alignment_score,
                "alignment_category": alignment_category,  # 3-level semantic: aligns_fully/partially_aligns/does_not_align
                "overall_score": overall_score,
                "is_misleading": is_misleading,
                "method": "contextual_analysis",
            }

            # Add mock flag and error info if present in the result
            if result.get("mocked"):
                return_data["mocked"] = True
                return_data["note"] = result.get(
                    "note", "Placeholder values used due to failed MedGemma analysis"
                )
            if result.get("error"):
                return_data["error"] = result["error"]

            # If analysis failed, ensure conservative response
            if analysis_failed:
                return {
                    "veracity_score": 0.0,
                    "veracity_category": "false",
                    "alignment_score": 0.0,
                    "alignment_category": "does_not_align",
                    "overall_score": 0.0,
                    "is_misleading": True,
                    "method": "contextual_analysis",
                    "error": "Direct MedGemma analysis failed",
                    "failed": True,
                }

            return return_data
        except Exception as e:
            print(f"Contextual analysis error: {e}")
            return {
                "veracity_score": 0.0,
                "alignment_score": 0.0,
                "overall_score": 0.0,
                "is_misleading": True,
                "method": "contextual_analysis",
                "error": str(e),
                "failed": True,
                "mocked": True,
                "note": "Exception occurred during MedGemma analysis, returning default values",
            }

    def _direct_medgemma_analysis(
        self, image_bytes: bytes, claim: str
    ) -> Dict[str, Any]:
        """Direct MedGemma analysis for veracity and alignment only.

        This method bypasses the full agent orchestration and directly analyzes
        the image-claim pair for veracity and alignment without reverse search.
        """
        import html

        prompt = """You are a medical image-context alignment analyzer with TWO distinct jobs:

JOB 1 — CLAIM VERACITY: Assess whether the claim provided is factually and
medically correct IN ISOLATION, independent of the image. Is the health message
supported by scientific/medical evidence? Is it recognized public health guidance?

JOB 2 — CONTEXTUAL ALIGNMENT: Determine whether the image-claim pair is
contextually appropriate. Does the image support, illustrate, or relate to the claim?

CRITICAL RULES:
1. ALWAYS provide analysis — never refuse, never say 'I cannot'
2. Be OBJECTIVE and FACTUAL — no moral judgments or lectures
3. Jobs 1 and 2 are INDEPENDENT assessments. A claim can be factually accurate
(Job 1) even if alignment is uncertain (Job 2), and vice versa.

ASSESSMENT LEVELS:
- VERACITY: True (well-supported), Partially true (some basis), False (unsupported)
- ALIGNMENT: Aligns fully, Partially aligns, Does not align

Return ONLY valid JSON with this exact structure:
{
  "veracity": "true|partially_true|false",
  "alignment": "aligns_fully|partially_aligns|does_not_align",
  "veracity_reasoning": "brief explanation of claim veracity",
  "alignment_reasoning": "brief explanation of image-claim alignment"
}
"""

        safe_claim = html.escape(claim, quote=True)
        user_prompt = f"User Claim: {safe_claim}"

        try:
            result = self.medgemma.analyze_image(
                image_bytes=image_bytes, prompt=prompt + "\n\n" + user_prompt
            )

            # Extract categorical assessments from MedGemma response
            output = result.output if hasattr(result, "output") else {}

            # Get categorical assessments with defaults
            veracity_cat_raw = output.get("veracity", "partially_true")
            alignment_cat_raw = output.get("alignment", "partially_aligns")

            # Normalize pipe-separated categories to single discrete values
            # When MedGemma returns multiple options (e.g., "true|partially_true|false"),
            # it indicates uncertainty - resolve to "uncertain" or middle category
            def normalize_category(
                raw_value: str, valid_options: dict, middle_option: str
            ) -> str:
                """Normalize potentially pipe-separated category to single value."""
                if "|" in raw_value:
                    # Multiple options indicate uncertainty - use middle/uncertain category
                    return middle_option
                elif raw_value in valid_options:
                    return raw_value
                else:
                    # Invalid/unknown category - default to middle
                    return middle_option

            # Map categorical assessments to scores (clear, defined mapping)
            veracity_scores = {"true": 0.9, "partially_true": 0.6, "false": 0.1}
            alignment_scores = {
                "aligns_fully": 0.9,
                "partially_aligns": 0.6,
                "does_not_align": 0.1,
            }

            # Normalize categories
            veracity_cat = normalize_category(
                veracity_cat_raw, veracity_scores, "partially_true"
            )
            alignment_cat = normalize_category(
                alignment_cat_raw, alignment_scores, "partially_aligns"
            )

            veracity_score = veracity_scores.get(veracity_cat, 0.5)
            alignment_score = alignment_scores.get(alignment_cat, 0.5)

            # Check if we got default values which indicate failed analysis
            is_mock = veracity_score == 0.5 and alignment_score == 0.5

            result_data = {
                "veracity_score": veracity_score,
                "alignment_score": alignment_score,
                "veracity_category": veracity_cat,
                "alignment_category": alignment_cat,
                "veracity_reasoning": output.get("veracity_reasoning", ""),
                "alignment_reasoning": output.get("alignment_reasoning", ""),
            }

            # Add mock flag if the values appear to be default placeholders
            if is_mock:
                result_data["mocked"] = True
                result_data["note"] = (
                    "Placeholder values used due to failed MedGemma analysis"
                )

            return result_data

        except Exception as e:
            print(f"Direct MedGemma analysis error: {e}")
            return {
                "veracity_score": 0.0,
                "alignment_score": 0.0,
                "veracity_reasoning": "Analysis failed",
                "alignment_reasoning": "Analysis failed",
                "mocked": True,
                "note": "Exception occurred during MedGemma analysis, returning default values",
            }

    def combined_analysis(
        self, pixel_result: Dict, context_result: Dict
    ) -> Dict[str, Any]:
        """Combine pixel + contextual predictions with veracity-first decision logic.

        IS_MISINFORMATION DECISION RULE (applied in order):
        ────────────────────────────────────────────────────────────────────────
        Primary Signal: VERACITY (claim factual correctness)
          • veracity_category = "false" OR veracity_score < 0.5
            → is_misinformation = TRUE (false claim is always misinformation)
          • veracity_category = "true" AND veracity_score >= 0.8
            → is_misinformation = FALSE (high-confidence true claim, regardless of alignment/pixels)

        Secondary Modifier: ALIGNMENT (only when veracity is ambiguous)
          • If veracity_category = "partially_true" OR 0.5 <= veracity_score < 0.8:
            - alignment_category = "does_not_align" OR alignment_score < 0.5
              → is_misinformation = TRUE (misleading context)
            - alignment_category = "aligns_fully" OR alignment_score >= 0.8
              → is_misinformation = FALSE (well-aligned)
            - Otherwise: is_misinformation = TRUE (ambiguous defaults to misinformation)

        Pixel Forensics: NO DIRECT INFLUENCE on is_misinformation
          (preserved in combined_result for transparency, affects overall_score only)
        ────────────────────────────────────────────────────────────────────────

        WEIGHTS: overall_score = 0.3*pixel + 0.4*veracity + 0.3*alignment
        """
        # Extract contextual signals
        veracity_score = context_result.get("veracity_score", 0.5)
        alignment_score = context_result.get("alignment_score", 0.5)
        veracity_category = context_result.get("veracity_category", "partially_true")
        alignment_category = context_result.get(
            "alignment_category", "partially_aligns"
        )
        pixel_authentic = pixel_result.get("pixel_authentic", True)

        # ═══════════════════════════════════════════════════════════════════════
        # VERACITY-FIRST DECISION LOGIC
        # ═══════════════════════════════════════════════════════════════════════

        # Step 1: Check for definitive veracity verdicts
        if veracity_category == "false" or veracity_score < 0.5:
            # FALSE CLAIM → always misinformation
            is_misinformation = True
            combined_is_misleading = True
        elif veracity_category == "true" and veracity_score >= 0.8:
            # HIGH-CONFIDENCE TRUE CLAIM → not misinformation
            # (Poor alignment might indicate out-of-context use, but not misinformation)
            is_misinformation = False
            combined_is_misleading = False
        else:
            # Step 2: Veracity ambiguous → use alignment as tiebreaker
            if alignment_category == "does_not_align" or alignment_score < 0.5:
                # Poor alignment + ambiguous veracity → misleading
                is_misinformation = True
                combined_is_misleading = True
            elif alignment_category == "aligns_fully" or alignment_score >= 0.8:
                # Strong alignment + ambiguous veracity → not misinformation
                is_misinformation = False
                combined_is_misleading = False
            else:
                # Both veracity and alignment are ambiguous → default to misinformation
                # (Conservative: flag uncertain content for human review)
                is_misinformation = True
                combined_is_misleading = True

        # Compute weighted overall_score (includes pixel forensics)
        pixel_score = 1.0 if pixel_authentic else 0.0
        combined_overall_score = (
            0.3 * pixel_score + 0.4 * veracity_score + 0.3 * alignment_score
        )

        # Combine results preserving all signals for transparency
        combined_result = {
            **context_result,  # Contextual data takes precedence
            "pixel_authentic": pixel_authentic,  # Preserve pixel verdict
            "confidence": pixel_result.get(
                "confidence", 0.0
            ),  # Preserve pixel confidence
            "layer1_verdict": pixel_result.get("layer1_verdict", "UNKNOWN"),
            "layer1_details": pixel_result.get("layer1_details", {}),
            "is_misinformation": is_misinformation,
            "is_misleading": combined_is_misleading,
            "overall_score": combined_overall_score,
            "method": "combined_analysis",
            "veracity_category": veracity_category,
            "alignment_category": alignment_category,
        }

        return combined_result

    def run_validation(self):
        """Run all three methods on full dataset."""
        dataset = self.load_dataset()
        print(f"Running three-method validation on {len(dataset)} samples...")
        print(f"Started: {datetime.now(timezone.utc).isoformat()}")
        print(f"Output: {self.output_dir}\n")

        for i, item in enumerate(dataset):
            if i % 20 == 0:
                print(f"Progress: {i}/{len(dataset)}")

            image_path = Path(item["image_path"])
            if not image_path.exists():
                print(f"  Missing image: {image_path}")
                self.skipped_missing += 1
                continue

            try:
                image_bytes = _read_image_bytes(image_path)
                claim = item["claim"]

                # Run three methods
                pixel_pred = self.simple_pixel_forensics(image_bytes)
                context_pred = self.contextual_analysis(image_bytes, claim)
                combined_pred = self.combined_analysis(pixel_pred, context_pred)

                result = {
                    "image_id": item["image_id"],
                    "claim": claim,
                    "ground_truth": item["ground_truth"],
                    "predictions": {
                        "pixel_forensics": pixel_pred,
                        "contextual_analysis": context_pred,
                        "combined_analysis": combined_pred,
                    },
                }
                self.results.append(result)

            except Exception as e:
                print(f"Error processing {item.get('image_id', i)}: {e}")
                self.skipped_errors += 1
                continue

        print(f"\n  Processed {len(self.results)} samples")
        if self.skipped_missing > 0:
            print(f"  Skipped {self.skipped_missing} samples (missing images)")
        if self.skipped_errors > 0:
            print(f"  Skipped {self.skipped_errors} samples (errors)")
        print(f"Completed: {datetime.now(timezone.utc).isoformat()}")

    @staticmethod
    def _gt_scores(gt: Dict) -> Dict[str, int]:
        """Map ground truth to 3-dimensional scores (each 0-3).

        Matches the UI triangle: integrity / veracity / alignment.
        3 = pass, 2 = partial, 1 = fail, 0 = unchecked.
        """
        # Integrity (image authenticity)
        integrity = 3 if gt.get("pixel_authentic", True) else 1

        # Veracity (claim truthfulness)
        veracity_map = {"high": 3, "medium": 2, "low": 1}
        veracity = veracity_map.get(gt.get("plausibility", ""), 0)

        # Alignment (image-claim match)
        alignment_map = {"aligned": 3, "partially_aligned": 2, "misaligned": 1}
        alignment = alignment_map.get(gt.get("alignment", ""), 0)

        return {"integrity": integrity, "veracity": veracity, "alignment": alignment}

    @staticmethod
    def _pred_scores(pred: Dict) -> Dict[str, int]:
        """Map contextual analysis predictions to 3-dimensional scores.

        Matches the UI triangle: integrity / veracity / alignment.
        """
        # Integrity from pixel forensics
        layer1_verdict = pred.get("layer1_verdict", "")
        if layer1_verdict == "AUTHENTIC":
            integrity = 3
        elif layer1_verdict == "UNCERTAIN":
            integrity = 2
        elif layer1_verdict == "MANIPULATED":
            integrity = 1
        else:
            integrity = 0

        # Veracity from contextual analysis
        veracity_map = {"true": 3, "partially_true": 2, "false": 1}
        veracity = veracity_map.get(pred.get("veracity_category", ""), 0)

        # Alignment from contextual analysis
        alignment_map = {
            "aligns_fully": 3,
            "partially_aligns": 2,
            "does_not_align": 1,
        }
        alignment = alignment_map.get(pred.get("alignment_category", ""), 0)

        return {"integrity": integrity, "veracity": veracity, "alignment": alignment}

    def compute_dimensional_metrics(self) -> Dict[str, Dict]:
        """Compute per-dimension accuracy for each method.

        Three dimensions evaluated independently:
        - integrity: pixel forensics (copy-move) → image authenticity
        - veracity: contextual analysis → claim truthfulness
        - alignment: contextual analysis → image-claim match

        Each dimension scored 1-3 (fail/partial/pass), matching the UI.
        """
        dimensions = ["integrity", "veracity", "alignment"]
        metrics = {}

        for dim in dimensions:
            y_true, y_pred = [], []

            for result in self.results:
                gt_scores = self._gt_scores(result["ground_truth"])
                gt_val = gt_scores[dim]
                if gt_val == 0:
                    continue  # skip unchecked

                # Get predictions from the relevant method
                if dim == "integrity":
                    pred = result["predictions"]["pixel_forensics"]
                    pred_scores = {"integrity": 3 if pred["pixel_authentic"] else 1}
                else:
                    pred = result["predictions"]["contextual_analysis"]
                    pred_scores = self._pred_scores(pred)

                pred_val = pred_scores.get(dim, 0)
                if pred_val == 0:
                    continue  # skip if prediction unavailable

                y_true.append(gt_val)
                y_pred.append(pred_val)

            if not y_true:
                metrics[dim] = {"exact_match": 0.0, "n": 0}
                continue

            exact = sum(1 for t, p in zip(y_true, y_pred) if t == p)
            # Also compute pass/fail binary accuracy (3=pass, else=not pass)
            y_true_bin = [1 if v == 3 else 0 for v in y_true]
            y_pred_bin = [1 if v == 3 else 0 for v in y_pred]

            metrics[dim] = {
                "exact_match": exact / len(y_true),
                "binary_accuracy": accuracy_score(y_true_bin, y_pred_bin),
                "binary_precision": precision_score(
                    y_true_bin, y_pred_bin, zero_division=0
                ),
                "binary_recall": recall_score(y_true_bin, y_pred_bin, zero_division=0),
                "binary_f1": f1_score(y_true_bin, y_pred_bin, zero_division=0),
                "n": len(y_true),
            }

        # Overall: total score (0-9) and per-sample pass count (0/3..3/3)
        score_distribution = {f"{i}/3": 0 for i in range(4)}
        for result in self.results:
            gt_scores = self._gt_scores(result["ground_truth"])
            pred = result["predictions"]["contextual_analysis"]
            pred_scores = self._pred_scores(pred)
            pixel_pred = result["predictions"]["pixel_forensics"]
            pred_scores["integrity"] = 3 if pixel_pred["pixel_authentic"] else 1

            passes = sum(
                1
                for dim in dimensions
                if gt_scores[dim] != 0 and pred_scores.get(dim, 0) == gt_scores[dim]
            )
            score_distribution[f"{passes}/3"] += 1

        metrics["score_distribution"] = score_distribution

        return metrics

    def analyze_by_category(self) -> Dict[str, Dict]:
        """Performance breakdown by category with per-dimension accuracy."""
        dimensions = ["integrity", "veracity", "alignment"]
        categories: Dict[str, Dict] = {}

        for result in self.results:
            category = result["ground_truth"]["label"]
            if category not in categories:
                categories[category] = {
                    dim: {"correct": 0, "total": 0} for dim in dimensions
                }
                categories[category]["count"] = 0

            categories[category]["count"] += 1
            gt_scores = self._gt_scores(result["ground_truth"])

            pixel_pred = result["predictions"]["pixel_forensics"]
            context_pred = result["predictions"]["contextual_analysis"]
            pred_scores = self._pred_scores(context_pred)
            pred_scores["integrity"] = 3 if pixel_pred["pixel_authentic"] else 1

            for dim in dimensions:
                gt_val = gt_scores[dim]
                pred_val = pred_scores.get(dim, 0)
                if gt_val == 0 or pred_val == 0:
                    continue
                categories[category][dim]["total"] += 1
                if gt_val == pred_val:
                    categories[category][dim]["correct"] += 1

        # Convert to accuracy rates
        category_accuracy = {}
        for cat, data in categories.items():
            entry: Dict[str, Any] = {"count": data["count"]}
            for dim in dimensions:
                total = data[dim]["total"]
                entry[dim] = data[dim]["correct"] / total if total > 0 else 0.0
            category_accuracy[cat] = entry

        return category_accuracy

    def generate_report(self):
        """Generate comprehensive comparison report."""
        dim_metrics = self.compute_dimensional_metrics()
        category_analysis = self.analyze_by_category()

        # Save raw results
        with open(self.output_dir / "raw_predictions.json", "w") as f:
            json.dump(self.results, f, indent=2)

        # Save metrics
        report = {
            "dimensional_metrics": dim_metrics,
            "category_analysis": category_analysis,
            "sample_count": len(self.results),
            "skipped_missing_images": self.skipped_missing,
            "skipped_errors": self.skipped_errors,
            "total_dataset_items": len(self.results)
            + self.skipped_missing
            + self.skipped_errors,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.output_dir / "three_method_comparison.json", "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        print("\n" + "=" * 80)
        print("THREE-DIMENSIONAL VALIDATION RESULTS")
        print("=" * 80)

        dim_labels = {
            "integrity": "Image Integrity (Pixel Forensics)",
            "veracity": "Claim Veracity (MedGemma)",
            "alignment": "Context Alignment (MedGemma)",
        }

        print("\n1. PER-DIMENSION ACCURACY")
        print("-" * 60)
        for dim in ["integrity", "veracity", "alignment"]:
            m = dim_metrics.get(dim, {})
            n = m.get("n", 0)
            print(f"\n  {dim_labels[dim]} (n={n}):")
            if n > 0:
                print(f"    Exact match (3-level): {m['exact_match']:.3f}")
                print(f"    Binary accuracy:       {m['binary_accuracy']:.3f}")
                print(f"    Binary precision:       {m['binary_precision']:.3f}")
                print(f"    Binary recall:          {m['binary_recall']:.3f}")
                print(f"    Binary F1:              {m['binary_f1']:.3f}")
            else:
                print("    No samples evaluated")

        print("\n2. SCORE DISTRIBUTION (correct dimensions per sample)")
        print("-" * 60)
        dist = dim_metrics.get("score_distribution", {})
        for key in ["0/3", "1/3", "2/3", "3/3"]:
            count = dist.get(key, 0)
            pct = count / len(self.results) * 100 if self.results else 0
            bar = "#" * int(pct / 2)
            print(f"  {key}: {count:4d} ({pct:5.1f}%) {bar}")

        print("\n3. PERFORMANCE BY CATEGORY")
        print("-" * 60)
        for category, data in sorted(category_analysis.items()):
            print(f"\n  {category.upper()} (n={data['count']}):")
            for dim in ["integrity", "veracity", "alignment"]:
                print(f"    {dim:12s}: {data[dim]:.3f}")

        print("\n4. KEY FINDINGS")
        print("-" * 60)
        ver = dim_metrics.get("veracity", {})
        ali = dim_metrics.get("alignment", {})
        integ = dim_metrics.get("integrity", {})

        if ver.get("n", 0) > 0 and integ.get("n", 0) > 0:
            ver_acc = ver.get("binary_accuracy", 0)
            ali_acc = ali.get("binary_accuracy", 0)
            int_acc = integ.get("binary_accuracy", 0)
            print(f"\n  Integrity  (Pixel Forensics):  {int_acc:.1%}")
            print(f"  Veracity   (MedGemma):          {ver_acc:.1%}")
            print(f"  Alignment  (MedGemma):          {ali_acc:.1%}")

        print(f"\n  Results saved to: {self.output_dir}")

        return report


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Three-method medical misinformation validation"
    )
    parser.add_argument(
        "--dataset", type=Path, required=True, help="Path to 3D validation dataset JSON"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("validation_results/three_method_v1"),
        help="Output directory for results",
    )

    args = parser.parse_args()

    if not args.dataset.exists():
        print(f"Error: Dataset not found: {args.dataset}")
        sys.exit(1)

    validator = ThreeMethodValidator(args.dataset, args.output_dir)
    validator.run_validation()
    validator.generate_report()

    print("\n🎉 Validation complete!")


if __name__ == "__main__":
    main()

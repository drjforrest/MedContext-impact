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


class ThreeMethodValidator:
    """Compare pixel forensics vs contextual vs combined misinformation detection."""

    def __init__(self, dataset_path: Path, output_dir: Path):
        self.dataset_path = dataset_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.medgemma = MedGemmaClient()
        self.results = []

    def load_dataset(self) -> List[Dict]:
        """Load 3D validation dataset."""
        with open(self.dataset_path) as f:
            return json.load(f)

    def simple_pixel_forensics(self, image_path: Path) -> Dict[str, Any]:
        """
        Simple pixel forensics baseline (file-based heuristic).

        NOTE: This is a placeholder. In production, you would:
        - Run Error Level Analysis (ELA)
        - Check EXIF metadata inconsistencies
        - Use deep learning tampering detection

        For now, uses file size as proxy (medical images tend to be larger).
        """
        try:
            file_size = image_path.stat().st_size
            # Simple heuristic: larger files more likely authentic
            # Real implementation would use proper ELA
            pixel_authentic = file_size > 100_000
            confidence = 0.85 if pixel_authentic else 0.75

            return {
                "pixel_authentic": pixel_authentic,
                "confidence": confidence,
                "method": "pixel_forensics",
                "file_size": file_size,
            }
        except Exception as e:
            print(f"Pixel forensics error: {e}")
            return {
                "pixel_authentic": True,
                "confidence": 0.5,
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

            # Simple combination: both need to be high to be legitimate
            # If either is low, it's misleading/misinformation
            overall_score = min(veracity_score, alignment_score)
            is_misleading = overall_score < 0.5

            return {
                "veracity_score": veracity_score,
                "alignment_score": alignment_score,
                "overall_score": overall_score,
                "is_misleading": is_misleading,
                "method": "contextual_analysis",
            }
        except Exception as e:
            print(f"Contextual analysis error: {e}")
            return {
                "veracity_score": 0.5,
                "alignment_score": 0.5,
                "overall_score": 0.5,
                "is_misleading": False,
                "method": "contextual_analysis",
                "error": str(e),
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
            veracity_cat = output.get("veracity", "partially_true")
            alignment_cat = output.get("alignment", "partially_aligns")

            # Map categorical assessments to scores (clear, defined mapping)
            veracity_scores = {"true": 0.9, "partially_true": 0.6, "false": 0.1}

            alignment_scores = {
                "aligns_fully": 0.9,
                "partially_aligns": 0.6,
                "does_not_align": 0.1,
            }

            veracity_score = veracity_scores.get(veracity_cat, 0.5)
            alignment_score = alignment_scores.get(alignment_cat, 0.5)

            return {
                "veracity_score": veracity_score,
                "alignment_score": alignment_score,
                "veracity_category": veracity_cat,
                "alignment_category": alignment_cat,
                "veracity_reasoning": output.get("veracity_reasoning", ""),
                "alignment_reasoning": output.get("alignment_reasoning", ""),
            }

        except Exception as e:
            print(f"Direct MedGemma analysis error: {e}")
            return {
                "veracity_score": 0.5,
                "alignment_score": 0.5,
                "veracity_reasoning": "Analysis failed",
                "alignment_reasoning": "Analysis failed",
            }

    def combined_analysis(
        self, pixel_result: Dict, context_result: Dict
    ) -> Dict[str, Any]:
        """Combine pixel + contextual predictions.

        Misinformation if:
        - Pixels are tampered OR
        - Context is misleading (veracity/alignment fails)
        """
        is_misinformation = (
            not pixel_result["pixel_authentic"] or context_result["is_misleading"]
        )

        return {
            **pixel_result,
            **context_result,
            "is_misinformation": is_misinformation,
            "method": "combined_analysis",
        }

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
                print(f"⚠️  Missing image: {image_path}")
                continue

            try:
                image_bytes = image_path.read_bytes()
                claim = item["claim"]

                # Run three methods
                pixel_pred = self.simple_pixel_forensics(image_path)
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
                continue

        print(f"\n✓ Processed {len(self.results)} samples")
        print(f"Completed: {datetime.now(timezone.utc).isoformat()}")

    def compute_misinformation_metrics(self) -> Dict[str, Dict[str, float]]:
        """Compute misinformation detection metrics for each method."""
        methods = ["pixel_forensics", "contextual_analysis", "combined_analysis"]
        metrics = {}

        for method in methods:
            y_true, y_pred = [], []

            for result in self.results:
                gt = result["ground_truth"]
                pred = result["predictions"][method]

                # Ground truth: any dimension failing = misinformation
                is_misinfo_gt = not (
                    gt["pixel_authentic"]
                    and gt["plausibility"] == "high"
                    and gt["alignment"] == "aligned"
                )
                y_true.append(is_misinfo_gt)

                # Method prediction
                if method == "pixel_forensics":
                    y_pred.append(not pred["pixel_authentic"])
                elif method == "contextual_analysis":
                    y_pred.append(pred["is_misleading"])
                else:  # combined
                    y_pred.append(pred["is_misinformation"])

            metrics[method] = {
                "accuracy": accuracy_score(y_true, y_pred),
                "precision": precision_score(y_true, y_pred, zero_division=0),
                "recall": recall_score(y_true, y_pred, zero_division=0),
                "f1": f1_score(y_true, y_pred, zero_division=0),
            }

        return metrics

    def analyze_by_category(self) -> Dict[str, Dict[str, float]]:
        """Performance breakdown by misinformation type."""
        categories = {}

        for result in self.results:
            category = result["ground_truth"]["label"]
            if category not in categories:
                categories[category] = {
                    "pixel_correct": 0,
                    "contextual_correct": 0,
                    "combined_correct": 0,
                    "count": 0,
                }

            categories[category]["count"] += 1
            gt = result["ground_truth"]

            # Ground truth misinformation status
            gt_misinfo = not (
                gt["pixel_authentic"]
                and gt["plausibility"] == "high"
                and gt["alignment"] == "aligned"
            )

            # Check each method
            for method_key, pred_key in [
                ("pixel_forensics", "pixel_correct"),
                ("contextual_analysis", "contextual_correct"),
                ("combined_analysis", "combined_correct"),
            ]:
                pred = result["predictions"][method_key]

                if method_key == "pixel_forensics":
                    pred_misinfo = not pred["pixel_authentic"]
                elif method_key == "contextual_analysis":
                    pred_misinfo = pred["is_misleading"]
                else:
                    pred_misinfo = pred["is_misinformation"]

                # Correct if prediction matches ground truth
                if pred_misinfo == gt_misinfo:
                    categories[category][pred_key] += 1

        # Convert to accuracy rates
        category_accuracy = {}
        for cat, data in categories.items():
            category_accuracy[cat] = {
                "pixel": data["pixel_correct"] / data["count"],
                "contextual": data["contextual_correct"] / data["count"],
                "combined": data["combined_correct"] / data["count"],
                "count": data["count"],
            }

        return category_accuracy

    def generate_report(self):
        """Generate comprehensive comparison report."""
        metrics = self.compute_misinformation_metrics()
        category_analysis = self.analyze_by_category()

        # Save raw results
        with open(self.output_dir / "raw_predictions.json", "w") as f:
            json.dump(self.results, f, indent=2)

        # Save metrics
        report = {
            "overall_metrics": metrics,
            "category_analysis": category_analysis,
            "sample_count": len(self.results),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.output_dir / "three_method_comparison.json", "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        print("\n" + "=" * 80)
        print("THREE-METHOD COMPARISON RESULTS")
        print("=" * 80)

        print("\n1. OVERALL MISINFORMATION DETECTION")
        print("-" * 50)
        for method, m in metrics.items():
            print(f"\n{method.replace('_', ' ').title():25s}:")
            print(f"  Accuracy:  {m['accuracy']:.3f}")
            print(f"  Precision: {m['precision']:.3f}")
            print(f"  Recall:    {m['recall']:.3f}")
            print(f"  F1 Score:  {m['f1']:.3f}")

        print("\n2. PERFORMANCE BY CATEGORY (Accuracy)")
        print("-" * 50)
        for category, accuracies in sorted(category_analysis.items()):
            print(f"\n{category.upper()} (n={accuracies['count']}):")
            print(f"  Pixel Forensics:     {accuracies['pixel']:.3f}")
            print(f"  Contextual Analysis: {accuracies['contextual']:.3f}")
            print(f"  Combined:            {accuracies['combined']:.3f}")

        print("\n3. KEY FINDINGS")
        print("-" * 50)

        # Calculate improvement
        context_recall = metrics["contextual_analysis"]["recall"]
        pixel_recall = metrics["pixel_forensics"]["recall"]
        improvement = context_recall - pixel_recall

        # Misleading category performance
        if "misleading" in category_analysis:
            misleading = category_analysis["misleading"]
            misleading_gap = misleading["contextual"] - misleading["pixel"]

            print(
                f"\n✓ Contextual analysis improves recall by {improvement:.1%} over pixel forensics"
            )
            print(
                f"✓ On MISLEADING cases (most common): contextual achieves {misleading['contextual']:.1%} vs pixel {misleading['pixel']:.1%}"
            )
            print(f"✓ Improvement on misleading: {misleading_gap:.1%}")

        print(f"\n✓ Results saved to: {self.output_dir}")
        print(f"✓ Raw predictions: {self.output_dir / 'raw_predictions.json'}")
        print(f"✓ Metrics summary: {self.output_dir / 'three_method_comparison.json'}")

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

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from app.clinical.medgemma_client import MedGemmaClient, MedGemmaResult
from app.forensics.service import run_forensics
from app.provenance.service import build_provenance
from app.reverse_search.service import run_reverse_search

ALLOWED_TOOLS = {
    "reverse_search",
    "forensics",
    "provenance",
}


@dataclass
class AgentRunResult:
    triage: Any
    tool_results: dict[str, Any]
    synthesis: Any


class MedContextAgent:
    """
    Deterministic agentic workflow:
    1) Triage (MedGemma) decides required tools.
    2) Dispatch to allowed tools only.
    3) Synthesis (MedGemma) produces final output.
    """

    def __init__(self, medgemma: MedGemmaClient | None = None) -> None:
        self.medgemma = medgemma or MedGemmaClient()

    def run(self, image_bytes: bytes, image_id=None) -> AgentRunResult:
        triage_result = self._triage(image_bytes)
        required_tools = self._extract_required_tools(triage_result)
        tool_results = self._dispatch_tools(
            image_bytes, required_tools, image_id, triage_result
        )
        synthesis_result = self._synthesize(image_bytes, triage_result, tool_results)
        return AgentRunResult(
            triage=triage_result.output,
            tool_results=tool_results,
            synthesis=synthesis_result.output,
        )

    def _triage(self, image_bytes: bytes) -> MedGemmaResult:
        prompt = (
            "You are a clinical investigator. "
            "Return JSON with: required_investigation (list), "
            "primary_findings (string), plausibility (low|medium|high)."
        )
        return self.medgemma.analyze_image(image_bytes=image_bytes, prompt=prompt)

    def _synthesize(
        self,
        image_bytes: bytes,
        triage: MedGemmaResult,
        tool_results: dict[str, Any],
    ) -> MedGemmaResult:
        prompt = (
            "Synthesize a final assessment using triage and tool results. "
            "Return JSON with: verdict, confidence, summary."
        )
        return self.medgemma.analyze_image(image_bytes=image_bytes, prompt=prompt)

    def _extract_required_tools(self, triage: MedGemmaResult) -> list[str]:
        raw = triage.output
        if isinstance(raw, dict):
            tools = raw.get("required_investigation") or raw.get("required_tools")
            if isinstance(tools, list):
                return self._sanitize_tools(tools)
        if isinstance(raw, str):
            return self._sanitize_tools(self._infer_tools_from_text(raw))
        return []

    def _sanitize_tools(self, tools: Iterable[str]) -> list[str]:
        normalized = []
        for tool in tools:
            if not isinstance(tool, str):
                continue
            tool_name = tool.strip().lower()
            if tool_name in ALLOWED_TOOLS:
                normalized.append(tool_name)
        return normalized

    def _infer_tools_from_text(self, text: str) -> list[str]:
        text_lower = text.lower()
        inferred = []
        if "reverse" in text_lower or "tineye" in text_lower:
            inferred.append("reverse_search")
        if "forensic" in text_lower or "deepfake" in text_lower:
            inferred.append("forensics")
        if "provenance" in text_lower or "blockchain" in text_lower:
            inferred.append("provenance")
        return inferred

    def _dispatch_tools(
        self,
        image_bytes: bytes,
        tools: Iterable[str],
        image_id=None,
        triage: MedGemmaResult | None = None,
    ) -> dict[str, Any]:
        results: dict[str, Any] = {}
        resolved_image_id = image_id or self._generate_image_id()
        for tool in tools:
            if tool == "reverse_search":
                results[tool] = run_reverse_search(
                    image_id=resolved_image_id, image_bytes=image_bytes
                )
            elif tool == "forensics":
                layers = self._select_forensics_layers(triage)
                results[tool] = run_forensics(image_bytes=image_bytes, layers=layers)
            elif tool == "provenance":
                results[tool] = build_provenance(
                    image_id=resolved_image_id, image_bytes=image_bytes
                )
        return results

    def _generate_image_id(self):
        from uuid import uuid4

        return uuid4()

    def _select_forensics_layers(self, triage: MedGemmaResult | None) -> list[str]:
        plausibility = None
        if triage is not None and isinstance(triage.output, dict):
            plausibility = triage.output.get("plausibility")
        plausibility_normalized = (
            plausibility.strip().lower() if isinstance(plausibility, str) else None
        )
        if plausibility_normalized == "high":
            return ["layer_2"]
        if plausibility_normalized in {"low", "medium"}:
            return ["layer_1", "layer_2"]
        return ["layer_1", "layer_2"]

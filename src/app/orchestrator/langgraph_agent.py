from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.clinical.medgemma_client import MedGemmaClient, MedGemmaResult
from app.forensics.service import run_forensics
from app.provenance.service import build_provenance
from app.reverse_search.service import run_reverse_search


class AgentState(TypedDict, total=False):
    image_bytes: bytes
    image_id: str | None
    trace_id: str
    triage: Any
    required_tools: list[str]
    tool_results: dict[str, Any]
    synthesis: Any
    trace: list[dict[str, Any]]


@dataclass
class LangGraphRunResult:
    triage: Any
    tool_results: dict[str, Any]
    synthesis: Any


class MedContextLangGraphAgent:
    def __init__(self, medgemma: MedGemmaClient | None = None) -> None:
        self.medgemma = medgemma or MedGemmaClient()
        self.graph = self._build_graph()

    def run(
        self, image_bytes: bytes, image_id: str | None = None
    ) -> LangGraphRunResult:
        state: AgentState = {
            "image_bytes": image_bytes,
            "image_id": image_id,
            "trace_id": self._generate_trace_id(),
            "trace": [],
        }
        final_state = self.graph.invoke(state)
        return LangGraphRunResult(
            triage=final_state.get("triage"),
            tool_results=final_state.get("tool_results", {}),
            synthesis=final_state.get("synthesis"),
        )

    def run_with_trace(
        self, image_bytes: bytes, image_id: str | None = None
    ) -> AgentState:
        state: AgentState = {
            "image_bytes": image_bytes,
            "image_id": image_id,
            "trace_id": self._generate_trace_id(),
            "trace": [],
        }
        return self.graph.invoke(state)

    def get_graph_mermaid(self) -> str:
        graph = self.graph.get_graph()
        return graph.draw_mermaid()

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("triage", self._triage_node)
        graph.add_node("dispatch_tools", self._dispatch_node)
        graph.add_node("synthesize", self._synthesize_node)

        graph.set_entry_point("triage")
        graph.add_edge("triage", "dispatch_tools")
        graph.add_edge("dispatch_tools", "synthesize")
        graph.add_edge("synthesize", END)

        return graph.compile()

    def _triage_node(self, state: AgentState) -> AgentState:
        start = perf_counter()
        image_bytes = state["image_bytes"]
        triage = self._triage(image_bytes)
        required = self._extract_required_tools(triage)
        state.update({"triage": triage.output, "required_tools": required})
        duration_ms = int((perf_counter() - start) * 1000)
        self._append_trace(
            state,
            node="triage",
            data={"required_tools": required},
            duration_ms=duration_ms,
        )
        return state

    def _dispatch_node(self, state: AgentState) -> AgentState:
        start = perf_counter()
        image_bytes = state["image_bytes"]
        image_id = state.get("image_id")
        required = state.get("required_tools", [])
        state["tool_results"] = self._dispatch_tools(image_bytes, required, image_id)
        duration_ms = int((perf_counter() - start) * 1000)
        self._append_trace(
            state,
            node="dispatch_tools",
            data=state["tool_results"],
            duration_ms=duration_ms,
        )
        return state

    def _synthesize_node(self, state: AgentState) -> AgentState:
        start = perf_counter()
        image_bytes = state["image_bytes"]
        triage_output = state.get("triage")
        tool_results = state.get("tool_results", {})
        synth = self._synthesize(image_bytes, triage_output, tool_results)
        state["synthesis"] = synth.output
        duration_ms = int((perf_counter() - start) * 1000)
        self._append_trace(
            state,
            node="synthesize",
            data={"status": "complete"},
            duration_ms=duration_ms,
        )
        return state

    def _triage(self, image_bytes: bytes) -> MedGemmaResult:
        prompt = (
            "You are a clinical investigator. "
            "Return JSON with: required_investigation (list), "
            "primary_findings (string), plausibility (low|medium|high)."
        )
        return self.medgemma.analyze_image(image_bytes=image_bytes, prompt=prompt)

    def _synthesize(
        self, image_bytes: bytes, triage: Any, tool_results: dict[str, Any]
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

    def _sanitize_tools(self, tools: list[str]) -> list[str]:
        allowed = {"reverse_search", "forensics", "provenance"}
        normalized = []
        for tool in tools:
            if not isinstance(tool, str):
                continue
            tool_name = tool.strip().lower()
            if tool_name in allowed:
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
        self, image_bytes: bytes, tools: list[str], image_id: str | None
    ) -> dict[str, Any]:
        results: dict[str, Any] = {}
        resolved_image_id = image_id or self._generate_image_id()
        for tool in tools:
            if tool == "reverse_search":
                results[tool] = run_reverse_search(
                    image_id=resolved_image_id, image_bytes=image_bytes
                )
            elif tool == "forensics":
                results[tool] = run_forensics(image_bytes=image_bytes)
            elif tool == "provenance":
                results[tool] = build_provenance(
                    image_id=resolved_image_id, image_bytes=image_bytes
                )
        return results

    def _generate_image_id(self) -> str:
        from uuid import uuid4

        return str(uuid4())

    def _generate_trace_id(self) -> str:
        from uuid import uuid4

        return str(uuid4())

    def _append_trace(
        self,
        state: AgentState,
        node: str,
        data: dict[str, Any],
        duration_ms: int,
    ) -> None:
        trace = state.get("trace")
        if trace is None:
            trace = []
            state["trace"] = trace
        trace.append(
            {
                "trace_id": state.get("trace_id"),
                "node": node,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "duration_ms": duration_ms,
                "data": data,
            }
        )

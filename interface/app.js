const output = document.getElementById("output");
const traceTableBody = document.querySelector("#traceTable tbody");
const traceSummary = document.getElementById("traceSummary");
const graphContainer = document.getElementById("graphContainer");
const integrityOutput = document.getElementById("integrityOutput");
const claimExtractionOutput = document.getElementById("claimExtractionOutput");
const claimClusterOutput = document.getElementById("claimClusterOutput");
const consensusOutput = document.getElementById("consensusOutput");
const decisionSupportOutput = document.getElementById("decisionSupportOutput");
let lastTracePayload = null;
let lastClaims = null;
let lastConsensus = null;
let lastIntegrityScore = null;

function getApiBase() {
  return document.getElementById("apiBase").value.trim().replace(/\/$/, "");
}

function getImageId() {
  const value = document.getElementById("imageId").value.trim();
  return value.length ? value : null;
}

function getFile() {
  return document.getElementById("fileInput").files[0];
}

function getContext() {
  return document.getElementById("contextInput").value.trim();
}

function setOutput(data) {
  output.textContent = JSON.stringify(data, null, 2);
}

function setIntegrityOutput(data) {
  integrityOutput.textContent = JSON.stringify(data, null, 2);
}

function setClaimOutput(data) {
  claimExtractionOutput.textContent = JSON.stringify(data, null, 2);
}

function setClusterOutput(data) {
  claimClusterOutput.textContent = JSON.stringify(data, null, 2);
}

function setConsensusOutput(data) {
  consensusOutput.textContent = JSON.stringify(data, null, 2);
}

function setDecisionSupportOutput(data) {
  decisionSupportOutput.textContent = JSON.stringify(data, null, 2);
}

function clearTrace() {
  traceTableBody.innerHTML = "";
  traceSummary.textContent = "No trace yet.";
  lastTracePayload = null;
}

function renderTrace(payload) {
  traceTableBody.innerHTML = "";
  if (!payload || !Array.isArray(payload.trace) || !payload.trace.length) {
    traceSummary.textContent = "Trace is empty.";
    return;
  }
  const trace = payload.trace;
  const traceId = payload.trace_id || "unknown";
  const durations = trace
    .map((entry) => (typeof entry.duration_ms === "number" ? entry.duration_ms : 0))
    .filter((value) => Number.isFinite(value));
  const totalDuration =
    typeof payload.total_duration_ms === "number"
      ? payload.total_duration_ms
      : durations.reduce((acc, value) => acc + value, 0);
  const maxDuration = durations.length ? Math.max(...durations) : 0;
  const timestamps = trace
    .map((entry) => Date.parse(entry.timestamp))
    .filter((value) => Number.isFinite(value));
  const baseTime = timestamps.length ? Math.min(...timestamps) : null;

  traceSummary.textContent = `Trace ID: ${traceId} | Nodes: ${trace.length} | Total: ${totalDuration} ms | Max: ${maxDuration} ms`;
  trace.forEach((entry) => {
    const row = document.createElement("tr");
    const nodeCell = document.createElement("td");
    nodeCell.textContent = entry.node ?? "";
    const timestampCell = document.createElement("td");
    timestampCell.textContent = entry.timestamp ?? "";
    const elapsedCell = document.createElement("td");
    const timestampMs = Date.parse(entry.timestamp);
    if (baseTime !== null && Number.isFinite(timestampMs)) {
      elapsedCell.textContent = String(timestampMs - baseTime);
    } else {
      elapsedCell.textContent = "-";
    }
    const durationCell = document.createElement("td");
    durationCell.textContent =
      typeof entry.duration_ms === "number" ? String(entry.duration_ms) : "-";
    const dataCell = document.createElement("td");
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(entry.data ?? {}, null, 2);
    dataCell.appendChild(pre);

    row.appendChild(nodeCell);
    row.appendChild(timestampCell);
    row.appendChild(elapsedCell);
    row.appendChild(durationCell);
    row.appendChild(dataCell);
    traceTableBody.appendChild(row);
  });
}

async function postMultipart(path, includeContext = false) {
  const apiBase = getApiBase();
  const file = getFile();
  if (!file) {
    alert("Please select an image file.");
    return null;
  }
  const form = new FormData();
  form.append("file", file);
  const imageId = getImageId();
  if (imageId) {
    form.append("image_id", imageId);
  }
  if (includeContext) {
    const context = getContext();
    if (context) {
      form.append("context", context);
    }
  }
  const response = await fetch(`${apiBase}${path}`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText);
  }
  return response.json();
}

async function postJson(path, payload) {
  const apiBase = getApiBase();
  const response = await fetch(`${apiBase}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

async function fetchGraph() {
  const apiBase = getApiBase();
  const response = await fetch(`${apiBase}/api/v1/orchestrator/graph`);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  const diagram = await response.text();
  graphContainer.innerHTML = `<pre class="mermaid">${diagram}</pre>`;
  mermaid.initialize({ startOnLoad: false, theme: "dark" });
  mermaid.run({ nodes: graphContainer.querySelectorAll(".mermaid") });
}

function getNumberInput(id) {
  const el = document.getElementById(id);
  if (!el) {
    return null;
  }
  const value = el.value.trim();
  if (!value) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function updateIntegrityVisuals(data) {
  if (!data || typeof data.score !== "number") {
    return;
  }
  lastIntegrityScore = data.score;
  const scoreValue = document.getElementById("integrityScoreValue");
  const scoreLabel = document.getElementById("integrityScoreLabel");
  const gaugeFill = document.getElementById("integrityGaugeFill");
  const barPlausibility = document.getElementById("barPlausibility");
  const barGenealogy = document.getElementById("barGenealogy");
  const barSource = document.getElementById("barSource");
  const valuePlausibility = document.getElementById("valuePlausibility");
  const valueGenealogy = document.getElementById("valueGenealogy");
  const valueSource = document.getElementById("valueSource");

  const scorePercent = Math.max(0, Math.min(1, data.score)) * 100;
  scoreValue.textContent = data.score.toFixed(2);
  gaugeFill.style.width = `${scorePercent}%`;

  const labelClass = scoreLabel.classList;
  labelClass.remove("status-high", "status-medium", "status-low");
  if (data.score > 0.8) {
    scoreLabel.textContent = "High Integrity";
    labelClass.add("status-high");
  } else if (data.score >= 0.5) {
    scoreLabel.textContent = "Moderate Integrity";
    labelClass.add("status-medium");
  } else {
    scoreLabel.textContent = "Low Integrity";
    labelClass.add("status-low");
  }

  const plausibility = data.plausibility ?? 0;
  const genealogy = data.genealogy_consistency ?? 0;
  const sourceRep = data.source_reputation ?? 0;
  barPlausibility.style.width = `${plausibility * 100}%`;
  barGenealogy.style.width = `${genealogy * 100}%`;
  barSource.style.width = `${sourceRep * 100}%`;
  valuePlausibility.textContent = plausibility.toFixed(2);
  valueGenealogy.textContent = genealogy.toFixed(2);
  valueSource.textContent = sourceRep.toFixed(2);
}

async function fetchIntegrityScore() {
  const apiBase = getApiBase();
  const params = new URLSearchParams();
  const plausibility = getNumberInput("plausibilityInput");
  const genealogy = getNumberInput("genealogyInput");
  const sourceRep = getNumberInput("sourceRepInput");
  const weightPlausibility = getNumberInput("weightPlausibilityInput");
  const weightGenealogy = getNumberInput("weightGenealogyInput");
  const weightSource = getNumberInput("weightSourceInput");

  if (plausibility !== null) params.set("plausibility", plausibility);
  if (genealogy !== null) params.set("genealogy_consistency", genealogy);
  if (sourceRep !== null) params.set("source_reputation", sourceRep);
  if (weightPlausibility !== null)
    params.set("weight_plausibility", weightPlausibility);
  if (weightGenealogy !== null)
    params.set("weight_genealogy", weightGenealogy);
  if (weightSource !== null) params.set("weight_source", weightSource);

  const response = await fetch(
    `${apiBase}/api/v1/decision-support/integrity-score?${params.toString()}`
  );
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

document.getElementById("btnRun").addEventListener("click", async () => {
  clearTrace();
  try {
    const data = await postMultipart("/api/v1/orchestrator/run");
    setOutput(data);
  } catch (err) {
    alert(err.message);
  }
});

document
  .getElementById("btnRunLangGraph")
  .addEventListener("click", async () => {
    clearTrace();
    try {
      const data = await postMultipart("/api/v1/orchestrator/run-langgraph");
      setOutput(data);
    } catch (err) {
      alert(err.message);
    }
  });

document.getElementById("btnTrace").addEventListener("click", async () => {
  try {
    const data = await postMultipart("/api/v1/orchestrator/trace");
    lastTracePayload = data;
    setOutput(data);
    renderTrace(data);
  } catch (err) {
    alert(err.message);
  }
});

document.getElementById("btnGraph").addEventListener("click", async () => {
  try {
    await fetchGraph();
  } catch (err) {
    alert(err.message);
  }
});

document
  .getElementById("btnIntegrityScore")
  .addEventListener("click", async () => {
    try {
      const data = await fetchIntegrityScore();
      setIntegrityOutput(data);
      updateIntegrityVisuals(data);
    } catch (err) {
      alert(err.message);
    }
  });

document.getElementById("btnExtractClaims").addEventListener("click", async () => {
  try {
    const text = document.getElementById("claimTextInput").value.trim();
    if (!text) {
      alert("Please enter claim text.");
      return;
    }
    const payload = {
      text,
      image_id: getImageId(),
      language: document.getElementById("claimLanguageInput").value.trim() || null,
    };
    const data = await postJson("/api/v1/semantic/claims", payload);
    lastClaims = data.claims || null;
    setClaimOutput(data);
  } catch (err) {
    alert(err.message);
  }
});

document.getElementById("btnClusterClaims").addEventListener("click", async () => {
  try {
    const raw = document.getElementById("clusterClaimsInput").value.trim();
    let claims = null;
    if (raw) {
      claims = JSON.parse(raw);
    } else if (lastClaims) {
      claims = lastClaims;
    }
    if (!claims) {
      alert("Provide claims JSON or run claim extraction first.");
      return;
    }
    const data = await postJson("/api/v1/semantic/clusters", { claims });
    setClusterOutput(data);
  } catch (err) {
    alert(err.message);
  }
});

document.getElementById("btnConsensusScore").addEventListener("click", async () => {
  try {
    const raw = document.getElementById("consensusClaimsInput").value.trim();
    let claims = null;
    if (raw) {
      claims = JSON.parse(raw);
    } else if (lastClaims) {
      claims = lastClaims.map((claim) => ({
        claim_text: claim.claim_text,
        confidence_this_is_claim: claim.confidence_this_is_claim,
      }));
    }
    if (!claims) {
      alert("Provide consensus claims JSON or run claim extraction first.");
      return;
    }
    const payload = { image_id: getImageId(), claims };
    const data = await postJson("/api/v1/decision-support/consensus", payload);
    lastConsensus = data;
    setConsensusOutput(data);
  } catch (err) {
    alert(err.message);
  }
});

document.getElementById("btnDecisionSupport").addEventListener("click", async () => {
  try {
    const audience = document.getElementById("audienceSelect").value;
    const consensusOverride = document
      .getElementById("consensusOverrideInput")
      .value.trim();
    const integrityOverride = getNumberInput("integrityOverrideInput");
    const keyFindingsRaw = document
      .getElementById("decisionKeyFindingsInput")
      .value.trim();
    const key_findings = keyFindingsRaw
      ? keyFindingsRaw.split(",").map((entry) => entry.trim()).filter(Boolean)
      : null;

    const payload = {
      image_id: getImageId(),
      audience,
      consensus:
        consensusOverride || (lastConsensus ? lastConsensus.consensus : null),
      integrity_score:
        integrityOverride !== null ? integrityOverride : lastIntegrityScore,
      key_findings,
    };
    const data = await postJson("/api/v1/decision-support/audience-output", payload);
    setDecisionSupportOutput(data);
  } catch (err) {
    alert(err.message);
  }
});

document
  .getElementById("btnDownloadTrace")
  .addEventListener("click", () => {
    if (!lastTracePayload) {
      alert("No trace data to download yet.");
      return;
    }
    const filename = lastTracePayload.trace_id
      ? `trace-${lastTracePayload.trace_id}.json`
      : "trace.json";
    const blob = new Blob([JSON.stringify(lastTracePayload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  });

document.getElementById("btnClearTrace").addEventListener("click", () => {
  clearTrace();
});

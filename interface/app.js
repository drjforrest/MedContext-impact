const output = document.getElementById("output");
const traceTableBody = document.querySelector("#traceTable tbody");
const traceSummary = document.getElementById("traceSummary");
const graphContainer = document.getElementById("graphContainer");
const integrityOutput = document.getElementById("integrityOutput");
const claimExtractionOutput = document.getElementById("claimExtractionOutput");
const claimClusterOutput = document.getElementById("claimClusterOutput");
const consensusOutput = document.getElementById("consensusOutput");
const decisionSupportOutput = document.getElementById("decisionSupportOutput");
const consensusBars = document.getElementById("consensusBars");
const consensusMeta = document.getElementById("consensusMeta");
const factualAnswer = document.getElementById("factualAnswer");
const contextAppropriatenessValue = document.getElementById(
  "contextAppropriatenessValue"
);
const contextAppropriatenessBadge = document.getElementById(
  "contextAppropriatenessBadge"
);
const contextAppropriatenessMeta = document.getElementById(
  "contextAppropriatenessMeta"
);
const urlResolution = document.getElementById("urlResolution");
const urlResolutionMeta = document.getElementById("urlResolutionMeta");
const urlResolutionContext = document.getElementById("urlResolutionContext");
const urlCandidates = document.getElementById("urlCandidates");
const btnUseContext = document.getElementById("btnUseContext");
const selectedImageMeta = document.getElementById("selectedImageMeta");
let lastTracePayload = null;
let lastClaims = null;
let lastConsensus = null;
let lastIntegrityScore = null;
let outputFlashTimeout = null;
let lastResolvedContext = null;
let selectedResolvedImage = null;

function setButtonLoading(button, isLoading, loadingText) {
  if (!button) {
    return;
  }
  if (isLoading) {
    button.dataset.originalText = button.textContent;
    button.textContent = loadingText || "Working...";
    button.disabled = true;
  } else {
    button.textContent = button.dataset.originalText || button.textContent;
    button.disabled = false;
    delete button.dataset.originalText;
  }
}

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

function getImageUrl() {
  return document.getElementById("imageUrlInput").value.trim();
}

function getContext() {
  return document.getElementById("contextInput").value.trim();
}

function setOutput(data) {
  output.textContent = JSON.stringify(data, null, 2);
  output.classList.add("flash");
  output.scrollIntoView({ behavior: "smooth", block: "start" });
  if (outputFlashTimeout) {
    clearTimeout(outputFlashTimeout);
  }
  outputFlashTimeout = setTimeout(() => {
    output.classList.remove("flash");
  }, 1200);
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

function extractJsonFromText(text) {
  if (typeof text !== "string" || !text.trim()) {
    return null;
  }
  const blockMatch = text.match(/```json\s*([\s\S]*?)```/i);
  const candidates = [];
  if (blockMatch && blockMatch[1]) {
    candidates.push(blockMatch[1]);
  }
  const braceMatch = text.match(/\{[\s\S]*\}/);
  if (braceMatch && braceMatch[0]) {
    candidates.push(braceMatch[0]);
  }
  for (const candidate of candidates) {
    try {
      return JSON.parse(candidate);
    } catch (err) {
      continue;
    }
  }
  return null;
}

function parseTriageText(text) {
  const parsed = extractJsonFromText(text);
  if (parsed && typeof parsed === "object") {
    return parsed;
  }
  if (typeof text !== "string") {
    return null;
  }
  const findingsMatch = text.match(
    /primary_findings\s*:\s*["']?(.+?)(?:\n|$)/i
  );
  const plausibilityMatch = text.match(
    /plausibility\s*:\s*["']?(low|medium|high)["']?/i
  );
  const result = {};
  if (findingsMatch && findingsMatch[1]) {
    result.primary_findings = findingsMatch[1].trim().replace(/^"+|"+$/g, "");
  }
  if (plausibilityMatch && plausibilityMatch[1]) {
    result.plausibility = plausibilityMatch[1].toLowerCase();
  }
  return Object.keys(result).length ? result : null;
}

function setContextBadge(level, label) {
  if (!contextAppropriatenessBadge) {
    return;
  }
  contextAppropriatenessBadge.classList.remove(
    "badge-high",
    "badge-medium",
    "badge-low",
    "badge-neutral"
  );
  contextAppropriatenessBadge.classList.add(level);
  contextAppropriatenessBadge.textContent = label;
}

function updateImmediateAnswer(data) {
  if (!factualAnswer || !contextAppropriatenessValue || !contextAppropriatenessMeta) {
    return;
  }
  const triageText = data?.triage?.text ?? data?.triage ?? "";
  const synthesisText = data?.synthesis?.text ?? data?.synthesis ?? "";
  const triage = parseTriageText(triageText);
  const synthesis = extractJsonFromText(synthesisText);
  const factual =
    triage?.primary_findings ||
    synthesis?.summary ||
    (typeof triageText === "string" ? triageText : "");
  factualAnswer.textContent = factual || "--";

  const context = data?.context_used || getContext();
  if (!context) {
    contextAppropriatenessValue.textContent = "No context provided";
    setContextBadge("badge-neutral", "Not evaluated");
    contextAppropriatenessMeta.textContent =
      "Add optional context above to evaluate appropriateness.";
    return;
  }

  const plausibility = triage?.plausibility;
  if (plausibility === "high") {
    contextAppropriatenessValue.textContent = "Consistent with context";
    setContextBadge("badge-high", "High fit");
    contextAppropriatenessMeta.textContent =
      `The medical content appears aligned with the ${
        data?.context_source || "provided"
      } usage context.`;
  } else if (plausibility === "medium") {
    contextAppropriatenessValue.textContent = "Needs review";
    setContextBadge("badge-medium", "Medium fit");
    contextAppropriatenessMeta.textContent =
      `The content may be loosely related to the ${
        data?.context_source || "stated"
      } usage context.`;
  } else if (plausibility === "low") {
    contextAppropriatenessValue.textContent = "Likely inconsistent";
    setContextBadge("badge-low", "Low fit");
    contextAppropriatenessMeta.textContent =
      `The content appears inconsistent with the ${
        data?.context_source || "stated"
      } usage context.`;
  } else {
    contextAppropriatenessValue.textContent = "Unknown";
    setContextBadge("badge-neutral", "Unknown");
    contextAppropriatenessMeta.textContent =
      "The model did not provide a plausibility signal.";
  }
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

async function postMultipart(path) {
  const apiBase = getApiBase();
  const file = getFile();
  const imageUrl = getImageUrl();
  if (!file && !imageUrl) {
    alert("Please select an image file or provide an image URL.");
    return null;
  }
  const form = new FormData();
  if (file) {
    form.append("file", file);
  }
  if (imageUrl) {
    form.append("image_url", imageUrl);
  }
  const imageId = getImageId();
  if (imageId) {
    form.append("image_id", imageId);
  }
  const context = getContext();
  if (context) {
    form.append("context", context);
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

async function resolveUrlCandidates(imageUrl) {
  const apiBase = getApiBase();
  const response = await fetch(`${apiBase}/api/v1/orchestrator/resolve-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_url: imageUrl }),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

function renderUrlCandidates(data) {
  if (!urlResolution || !urlCandidates || !urlResolutionMeta || !urlResolutionContext) {
    return;
  }
  urlCandidates.innerHTML = "";
  urlResolution.classList.remove("hidden");
  const images = Array.isArray(data?.images) ? data.images : [];
  lastResolvedContext = data?.context || null;
  selectedResolvedImage = null;
  urlResolutionContext.textContent = lastResolvedContext
    ? `Suggested context: ${lastResolvedContext}`
    : "No context found on the page.";
  if (selectedImageMeta) {
    selectedImageMeta.textContent = "Select an image to continue.";
  }
  urlResolutionMeta.textContent = images.length
    ? `Found ${images.length} image candidate${images.length === 1 ? "" : "s"}.`
    : "No images found at this URL.";
  if (btnUseContext) {
    btnUseContext.disabled = !lastResolvedContext;
  }
  images.forEach((url) => {
    const card = document.createElement("div");
    card.className = "url-card";
    const img = document.createElement("img");
    img.src = url;
    img.alt = "Candidate image";
    img.loading = "lazy";
    const body = document.createElement("div");
    body.className = "url-card-body";
    const urlText = document.createElement("div");
    urlText.className = "url-card-url";
    urlText.textContent = url;
    const useButton = document.createElement("button");
    useButton.className = "secondary";
    useButton.textContent = "Use this image";
    useButton.addEventListener("click", () => {
      document.getElementById("imageUrlInput").value = url;
      document.querySelectorAll(".url-card").forEach((el) => {
        el.classList.remove("selected");
      });
      card.classList.add("selected");
      selectedResolvedImage = url;
      if (selectedImageMeta) {
        selectedImageMeta.textContent = "Selected image is ready to run.";
      }
      if (!getContext() && lastResolvedContext) {
        document.getElementById("contextInput").value = lastResolvedContext;
      }
    });
    const useAndRunButton = document.createElement("button");
    useAndRunButton.textContent = "Use & run";
    useAndRunButton.addEventListener("click", async () => {
      useButton.click();
      document.getElementById("btnRun").click();
    });
    body.appendChild(urlText);
    body.appendChild(useButton);
    body.appendChild(useAndRunButton);
    card.appendChild(img);
    card.appendChild(body);
    urlCandidates.appendChild(card);
  });
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

  if (!scoreValue || !scoreLabel || !gaugeFill) {
    return;
  }

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
  if (barPlausibility) {
    barPlausibility.style.width = `${plausibility * 100}%`;
  }
  if (barGenealogy) {
    barGenealogy.style.width = `${genealogy * 100}%`;
  }
  if (barSource) {
    barSource.style.width = `${sourceRep * 100}%`;
  }
  if (valuePlausibility) {
    valuePlausibility.textContent = plausibility.toFixed(2);
  }
  if (valueGenealogy) {
    valueGenealogy.textContent = genealogy.toFixed(2);
  }
  if (valueSource) {
    valueSource.textContent = sourceRep.toFixed(2);
  }
}

function updateConsensusVisuals(data) {
  if (!data || !data.distribution) {
    consensusBars.innerHTML = "";
    consensusMeta.textContent = "No consensus yet.";
    return;
  }
  consensusBars.innerHTML = "";
  const distribution = data.distribution;
  const entries = Object.entries(distribution);
  if (!entries.length) {
    consensusMeta.textContent = "No consensus yet.";
    return;
  }
  consensusMeta.textContent = `Consensus: ${data.consensus || "unknown"} | Confidence: ${
    typeof data.confidence_in_consensus === "number"
      ? data.confidence_in_consensus.toFixed(2)
      : "--"
  }`;
  entries
    .sort((a, b) => b[1].percentage - a[1].percentage)
    .forEach(([label, entry]) => {
      const row = document.createElement("div");
      row.className = "consensus-row";
      const labelEl = document.createElement("div");
      labelEl.className = "consensus-label";
      labelEl.textContent = label.replace(/_/g, " ");
      const bar = document.createElement("div");
      bar.className = "consensus-bar";
      const fill = document.createElement("div");
      fill.className = "consensus-fill";
      fill.style.width = `${entry.percentage}%`;
      bar.appendChild(fill);
      const value = document.createElement("div");
      value.className = "consensus-value";
      value.textContent = `${entry.percentage.toFixed(1)}%`;
      row.appendChild(labelEl);
      row.appendChild(bar);
      row.appendChild(value);
      consensusBars.appendChild(row);
    });
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

function buildConsensusPayload(silent = false) {
  const raw = document.getElementById("consensusClaimsInput").value.trim();
  let claims = null;
  if (raw) {
    try {
      claims = JSON.parse(raw);
    } catch (err) {
      if (!silent) {
        alert("Consensus claims JSON is invalid.");
      }
      return null;
    }
  } else if (lastClaims) {
    claims = lastClaims.map((claim) => ({
      claim_text: claim.claim_text,
      confidence_this_is_claim: claim.confidence_this_is_claim,
    }));
  }
  if (!claims) {
    if (!silent) {
      alert("Provide consensus claims JSON or run claim extraction first.");
    }
    return null;
  }
  return { image_id: getImageId(), claims };
}

async function computeConsensusScore({ silent = false } = {}) {
  const payload = buildConsensusPayload(silent);
  if (!payload) {
    return null;
  }
  const data = await postJson("/api/v1/decision-support/consensus", payload);
  lastConsensus = data;
  setConsensusOutput(data);
  updateConsensusVisuals(data);
  return data;
}

document.getElementById("btnRun").addEventListener("click", async () => {
  clearTrace();
  try {
    const data = await postMultipart("/api/v1/orchestrator/run");
    setOutput(data);
    updateImmediateAnswer(data);
    await computeConsensusScore({ silent: true });
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
      updateImmediateAnswer(data);
      await computeConsensusScore({ silent: true });
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

document.getElementById("btnResolveUrl").addEventListener("click", async () => {
  const button = document.getElementById("btnResolveUrl");
  try {
    const imageUrl = getImageUrl();
    if (!imageUrl) {
      alert("Please provide a URL to resolve.");
      return;
    }
    setButtonLoading(button, true, "Resolving...");
    const data = await resolveUrlCandidates(imageUrl);
    renderUrlCandidates(data);
  } catch (err) {
    alert(err.message);
  } finally {
    setButtonLoading(button, false);
  }
});

btnUseContext?.addEventListener("click", () => {
  if (lastResolvedContext) {
    document.getElementById("contextInput").value = lastResolvedContext;
    if (selectedImageMeta && selectedResolvedImage) {
      selectedImageMeta.textContent = "Selected image and context are ready to run.";
    }
  } else {
    alert("No suggested context available yet.");
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
    await computeConsensusScore();
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

const output = document.getElementById("output");
const traceTableBody = document.querySelector("#traceTable tbody");
const traceSummary = document.getElementById("traceSummary");
const graphContainer = document.getElementById("graphContainer");
const integrityOutput = document.getElementById("integrityOutput");
let lastTracePayload = null;

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
  const value = document.getElementById(id).value.trim();
  if (!value) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
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

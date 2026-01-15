const output = document.getElementById("output");
const traceTableBody = document.querySelector("#traceTable tbody");
const traceSummary = document.getElementById("traceSummary");
const graphContainer = document.getElementById("graphContainer");

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

function clearTrace() {
  traceTableBody.innerHTML = "";
  traceSummary.textContent = "No trace yet.";
}

function renderTrace(traceId, trace) {
  traceTableBody.innerHTML = "";
  if (!trace || !trace.length) {
    traceSummary.textContent = "Trace is empty.";
    return;
  }
  traceSummary.textContent = `Trace ID: ${traceId}`;
  trace.forEach((entry) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${entry.node}</td>
      <td>${entry.timestamp}</td>
      <td>${entry.duration_ms}</td>
      <td><pre>${JSON.stringify(entry.data, null, 2)}</pre></td>
    `;
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
    setOutput(data);
    renderTrace(data.trace_id, data.trace);
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

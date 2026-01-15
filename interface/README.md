# MedContext Debug Interface

This is a lightweight, static debug console focused on observability.

## Run Locally

From the project root:

```
cd interface
python -m http.server 5173
```

Then open `http://localhost:5173` and point the API base URL to your FastAPI server.

## What It Does

- Runs the deterministic orchestrator
- Runs the LangGraph orchestrator
- Runs the LangGraph trace endpoint with timestamps and durations
- Renders the LangGraph as a Mermaid diagram

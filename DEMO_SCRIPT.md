# NetCoop AI Hackathon Demo Script

Target length: 4 minutes. Use only the synthetic fixtures under `backend/tests/fixtures/`; they are for tests and demonstrations and are never loaded automatically by the production application.

## 0:00–0:30 — Problem and scope

- Open the NetCoop AI dashboard.
- Explain that the prototype accepts submitted JSON telemetry and does not connect to or change the campus network.
- Point out the five locally implemented rule agents and clarify that no LLM is configured.

## 0:30–1:40 — End-to-end congestion diagnosis

- Open **New Diagnosis** and upload `backend/tests/fixtures/link_congestion.json`.
- Validate and start the diagnosis.
- Show the performance and infrastructure findings in the message timeline, including utilization, latency, packet loss, and queue drops.
- Open the report and point out the root cause, evidence values, source agents, alternatives, and recommended actions.

## 1:40–2:30 — Conflicting evidence

- Start a second run with `backend/tests/fixtures/conflicting_signals.json`.
- Show that congestion and weak wireless signals score closely and the report is marked **inconclusive** instead of asserting a definitive cause.

## 2:30–3:00 — Insufficient evidence

- Start a run with `backend/tests/fixtures/sparse_input.json`.
- Show that a small set of measurements from one specialist does not produce a confident diagnosis.

## 3:00–3:35 — Validation and unit handling

- In the API docs at `/docs`, show the telemetry validation endpoint.
- Explain that unsupported units and malformed schema fields are rejected, while supported strings such as `1 s` or `2.5 Gbps` are normalized to canonical units.

## 3:35–4:00 — Reproducibility and close

- Show the test command `python -m unittest discover -s backend/tests -v` and the test-only fixture directory.
- Close by stating the prototype’s boundary: it analyzes only submitted telemetry, uses transparent fixed rules, and provides recommendations for an engineer to verify.

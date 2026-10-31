# NetCoop AI --- Product, Technical, UI/UX, Workflow & Web Architecture

> **Project:** NetCoop AI --- Multi-Agent Network Fault Diagnosis and
> Interoperability\
> **Source:** *Agentic AI Grand Finale Problem Statement* (7 pages)\
> **Document type:** Product Requirements Document (PRD), Technical
> Requirements Document (TRD), UI/UX specification, workflow and web
> architecture\
> **Target build:** 24-hour hackathon prototype\
> **Status:** Implementation blueprint

------------------------------------------------------------------------

## 1. Project Overview

### 1.1 Product summary

NetCoop AI is a multi-agent network fault diagnosis system designed to
help network operators investigate intermittent connectivity and
performance issues. It coordinates specialized agents that analyze
network telemetry, infrastructure health, connectivity and topology,
correlate evidence, and produce one explainable diagnostic report.

The system should identify a **probable** root cause rather than claim
certainty when the available evidence is insufficient. It should show
affected devices or network segments where identifiable, supporting
evidence, alternative explanations, confidence, limitations, and
practical corrective actions.

### 1.2 Problem statement

Campus network information can be distributed across routers, switches,
Wi-Fi zones, Ethernet connections, lecture halls, and monitoring
systems. Data may be incomplete, inconsistent, outdated, noisy, or
expressed using different formats and terminology. Diagnosing a fault
therefore requires correlating multiple signals rather than relying on a
single metric.

NetCoop AI addresses this by enabling specialized agents to exchange
structured findings and collaboratively build a unified diagnosis.

### 1.3 Product vision

Make network troubleshooting more efficient, explainable, and
interoperable by combining independent diagnostic agents into one
coordinated workflow.

### 1.4 Goals

-   Analyze supplied or authorized network telemetry.
-   Run at least two functional agents with distinct responsibilities;
    target four to five.
-   Define a documented, structured agent communication protocol.
-   Orchestrate agents and consolidate their findings.
-   Identify probable root causes and affected devices or segments where
    possible.
-   Show evidence, alternative causes, uncertainty, confidence, and
    corrective recommendations.
-   Validate malformed, missing, and incompatible inputs and report
    failures clearly.
-   Produce a structured JSON diagnostic report.
-   Provide reproducible sample scenarios, setup instructions, tests,
    and a working demonstration.

### 1.5 Non-goals for the hackathon prototype

-   Direct modification of production campus network infrastructure.
-   Guaranteed identification of a root cause from insufficient
    evidence.
-   Building a complete enterprise network-monitoring platform.
-   Requiring MCP, human approval workflows, or durable pause/resume
    state.
-   Requiring access to the production campus network.

Automated remediation, MCP, HITL, and persistent workflow state are
optional enhancements in the challenge brief. Any remediation in the
prototype should be simulated unless explicit authorization exists.

------------------------------------------------------------------------

# Part A --- Product Requirements Document (PRD)

## 2. Users and Use Cases

### 2.1 Primary users

  -----------------------------------------------------------------------
  User                    Need                    Expected value
  ----------------------- ----------------------- -----------------------
  Network administrator   Diagnose network        Faster, evidence-based
                          incidents using         troubleshooting
                          multiple telemetry      
                          signals                 

  Network operations      Understand affected     Clearer fault isolation
  engineer                devices, links, and     
                          competing explanations  

  Technical evaluator /   Verify agent            Transparent,
  demo reviewer           collaboration and       reproducible
                          diagnostic reasoning    demonstration
  -----------------------------------------------------------------------

These are proposed user roles for the application; the challenge brief
does not prescribe a specific role or access-control model.

### 2.2 Core use cases

1.  Upload or select a telemetry dataset.
2.  Choose a diagnostic scenario or incident.
3.  Validate the input and identify missing or incompatible fields.
4.  Start a multi-agent diagnostic run.
5.  Inspect each agent's findings and exchanged messages.
6.  Review the correlated probable root cause.
7.  Inspect evidence, affected devices, alternatives, confidence, and
    limitations.
8.  Export or view the final JSON and human-readable report.
9.  Repeat the run using another test scenario.

## 3. Functional Requirements

### FR-01 --- Telemetry ingestion

The system shall accept documented synthetic telemetry,
organizer-provided scenarios, or data from an authorized test
environment.

Supported data may include:

-   Latency, jitter, packet loss, throughput, bandwidth, and link
    utilization.
-   Device ID and device status.
-   CPU and memory utilization.
-   Egress queue drops and interface errors.
-   Wireless signal measurements where available.
-   Timestamps and network topology information.

**Acceptance criteria** - A user can provide a supported sample
dataset. - The application reports whether parsing and validation
succeeded. - Invalid records or unsupported fields produce
understandable validation messages.

### FR-02 --- Input normalization and validation

The system shall normalize supported field names, units, and schema
versions before analysis where a safe mapping is known.

**Acceptance criteria** - Missing required fields are reported. -
Malformed values are rejected or marked invalid rather than silently
trusted. - Unit mismatches and unsupported schema versions are
surfaced. - Validation errors do not crash the complete application.

### FR-03 --- Multi-agent analysis

The system shall execute at least two agents with distinct
responsibilities. The recommended implementation uses five agents:

1.  Telemetry and Performance Agent.
2.  Infrastructure Health Agent.
3.  Connectivity Analysis Agent.
4.  Fault Correlation Agent.
5.  Recommendation and Reporting Agent.

**Acceptance criteria** - At least two agents execute and return
structured findings. - Findings from multiple agents contribute to the
final diagnosis. - Each finding identifies its source agent.

### FR-04 --- Agent interoperability

The system shall define and document message formats, field meanings,
units, and a mechanism for exchanging findings.

**Acceptance criteria** - Agent messages use a documented structured
schema. - Messages include identifiers, schema version, source,
timestamp, and payload. - The receiver validates messages and handles
missing or incompatible fields. - Agents can interpret findings produced
by other agents.

### FR-05 --- Orchestration

The system shall coordinate agent execution and consolidate results into
one diagnostic outcome.

**Acceptance criteria** - A diagnostic run has a unique incident or run
ID. - The orchestrator tracks agent status and results. - The
correlation stage receives findings from relevant agents. - Partial
failures are reported instead of being hidden.

### FR-06 --- Fault diagnosis and evidence

The system shall identify probable root causes using telemetry and agent
findings.

**Acceptance criteria** - The report includes a probable cause or an
explicit insufficient-evidence outcome. - Supporting evidence identifies
metric, value, unit where applicable, and interpretation. - Affected
devices or segments are included when identifiable. - Alternative
explanations and limitations are included where appropriate.

### FR-07 --- Confidence

The system shall provide a confidence estimate or clearly defined
confidence category.

**Acceptance criteria** - The confidence method is documented. -
Confidence is based on available evidence and agent findings. - The
system does not present confidence as certainty. - Insufficient evidence
can result in an inconclusive status.

### FR-08 --- Recommendations and reporting

The system shall generate practical corrective actions and a structured
JSON report. A Markdown report or dashboard may supplement the JSON.

**Acceptance criteria** - The report contains probable cause,
confidence, affected devices, evidence, alternative causes,
recommendations, evidence sources, and limitations. - The JSON output
conforms to the documented report schema. - A human-readable view is
available in the web application.

### FR-09 --- Test scenarios

The prototype shall include reproducible scenarios covering:

-   Normal network operation.
-   Link congestion.
-   Weak Wi-Fi signal.
-   Ethernet or interface fault.
-   DNS or DHCP failure.
-   Interoperability failure caused by incompatible field names, units,
    schema versions, or missing message information.

### FR-10 --- Run history and observability

The prototype should expose the current run's agent statuses, findings,
and message flow. A simple in-memory run history is sufficient for the
initial hackathon build; durable persistence is optional.

## 4. Non-functional Requirements

  -----------------------------------------------------------------------
  ID                      Requirement             Target for prototype
  ----------------------- ----------------------- -----------------------
  NFR-01                  Reliability             Invalid input should
                                                  return a controlled
                                                  error, not crash the
                                                  service

  NFR-02                  Explainability          Diagnosis must be
                                                  traceable to evidence
                                                  and agent findings

  NFR-03                  Interoperability        Documented, versioned
                                                  structured messages

  NFR-04                  Usability               A user can run a
                                                  scenario and understand
                                                  the result without
                                                  reading logs

  NFR-05                  Reproducibility         Sample datasets, setup
                                                  instructions, and test
                                                  scripts are included

  NFR-06                  Extensibility           Agents and telemetry
                                                  adapters can be added
                                                  independently

  NFR-07                  Safety                  No production network
                                                  changes without
                                                  explicit authorization

  NFR-08                  Maintainability         Separate ingestion,
                                                  agents, orchestration,
                                                  correlation, and
                                                  reporting modules
  -----------------------------------------------------------------------

The challenge brief does not define numerical latency, throughput,
availability, or security service-level targets. These should be
measured and specified if the project moves beyond the hackathon
prototype.

## 5. MVP Scope and Priorities

### Must have

-   Telemetry ingestion and validation.
-   At least two collaborating functional agents.
-   Structured agent messages and documented field meanings/units.
-   Orchestration and shared diagnosis.
-   Evidence-based probable root cause.
-   Confidence or confidence category, including insufficient-evidence
    handling.
-   JSON diagnostic report.
-   Malformed, missing, or incompatible input handling.
-   Sample scenarios, tests, setup documentation, and runnable demo.

### Should have

-   Four or five specialized agents.
-   Interactive dashboard for telemetry, agent messages, and results.
-   Human-readable Markdown report.
-   Scenario selector and run history for the demo session.

### Could have

-   MCP integration.
-   Human-in-the-loop review.
-   Durable workflow state and pause/resume.
-   Simulated remediation actions.

### Out of scope

-   Unauthorized changes to live campus infrastructure.
-   Claims of guaranteed diagnosis.
-   Production-grade monitoring integrations not supplied or authorized
    for the hackathon.

## 6. User Stories

-   As a network administrator, I want to submit telemetry so that the
    system can analyze a network incident.
-   As an operator, I want to see which agents ran and what each one
    found so that I can understand how the diagnosis was formed.
-   As an operator, I want evidence attached to the probable root cause
    so that I can verify the recommendation.
-   As an operator, I want alternative causes and limitations so that I
    do not mistake a hypothesis for certainty.
-   As an evaluator, I want to run known scenarios so that I can
    reproduce and assess the system's behavior.
-   As a developer, I want versioned message schemas so that agents can
    interoperate even when their implementations differ.

## 7. Success Metrics

The following are proposed project metrics, not numerical targets
mandated by the brief:

-   All mandatory acceptance scenarios can be run reproducibly.
-   At least two agents contribute evidence to a single diagnosis.
-   Every final diagnosis can be traced to one or more agent findings.
-   The malformed/missing/incompatible input tests return clear errors
    or warnings.
-   The report always includes a confidence value/category and
    limitations.
-   The demo clearly shows inter-agent communication and the final
    report.

------------------------------------------------------------------------

# Part B --- Technical Requirements Document (TRD)

## 8. Proposed Technology Stack

The challenge brief allows rule-based logic, existing AI models, LLMs,
or hybrid approaches. It does not mandate a particular framework or
language. The following is a practical proposed stack for a 24-hour
prototype.

  -----------------------------------------------------------------------
  Layer                   Proposed technology     Responsibility
  ----------------------- ----------------------- -----------------------
  Frontend                React + TypeScript      Dashboard and user
                                                  interaction

  UI styling              Tailwind CSS            Consistent responsive
                                                  interface

  Charts                  Recharts or Chart.js    Telemetry visualization

  Backend API             Python + FastAPI        REST endpoints and
                                                  validation

  Data validation         Pydantic                Request and message
                                                  schemas

  Agent implementation    Python modules with     Specialized analysis
                          distinct interfaces     

  Orchestration           Custom Python           Agent execution and
                          orchestrator            result aggregation

  AI reasoning            Rules first; optional   Evidence interpretation
                          LLM for explanation     and readable summaries

  Data exchange           Versioned JSON messages Inter-agent
                                                  interoperability

  Persistence             SQLite or JSON files    Optional run and report
                          for prototype           history

  Testing                 Pytest                  Unit and integration
                                                  tests

  API documentation       FastAPI OpenAPI/Swagger Endpoint inspection
  -----------------------------------------------------------------------

**Implementation guidance:** prioritize deterministic rules for
measurable signals and confidence calculation. Use an LLM only where it
adds value, such as converting validated findings into readable
explanations. Do not allow an LLM to invent telemetry values or
unsupported evidence.

## 9. High-level System Architecture

``` mermaid
flowchart TD
    U[Network Operator] --> W[Web Dashboard]
    W --> API[Backend API]
    API --> V[Input Validation and Normalization]
    V --> O[Agent Orchestrator]
    O --> P[Telemetry and Performance Agent]
    O --> I[Infrastructure Health Agent]
    O --> C[Connectivity Analysis Agent]
    P --> M[Structured Agent Message Bus]
    I --> M
    C --> M
    M --> F[Fault Correlation Agent]
    F --> R[Recommendation and Reporting Agent]
    R --> J[Unified JSON Diagnostic Report]
    J --> API
    API --> W
    O -.-> L[Run and Agent Logs]
```

The message bus in this prototype can be a simple in-process message
exchange or a documented REST/JSON interface. A separate message broker
is not required by the challenge brief.

## 10. Component Responsibilities

### 10.1 Frontend

-   Upload/select telemetry dataset.
-   Select a test scenario.
-   Start a diagnostic run.
-   Display validation status.
-   Show agent execution states.
-   Display agent findings and message exchange.
-   Display final diagnosis, confidence, affected devices, evidence,
    alternatives, and recommendations.
-   Show or download the JSON report.

### 10.2 Backend API

-   Accept diagnostic requests.
-   Validate request structure and file format.
-   Normalize supported telemetry fields and units.
-   Create a run/incident identifier.
-   Invoke the orchestrator.
-   Return agent progress and final report.
-   Provide controlled error responses.

### 10.3 Agent Orchestrator

-   Create the diagnostic context.
-   Dispatch tasks to specialized agents.
-   Collect and validate agent messages.
-   Track success, failure, or skipped states.
-   Pass findings to the correlation agent.
-   Pass the consolidated diagnosis to the reporting agent.

### 10.4 Telemetry and Performance Agent

Analyzes:

-   Latency.
-   Jitter.
-   Packet loss.
-   Throughput.
-   Bandwidth.
-   Link utilization.

Produces performance findings with metric values, units, interpretation,
severity, and relevant device/link references.

### 10.5 Infrastructure Health Agent

Examines:

-   Device status.
-   CPU and memory utilization.
-   Interface errors.
-   Egress queue drops.
-   Other available infrastructure metrics.

Produces infrastructure findings and flags possible device or interface
health problems.

### 10.6 Connectivity Analysis Agent

Examines:

-   Network topology.
-   Device and link relationships.
-   Affected devices.
-   Scope of connectivity failures.

Produces a connectivity impact summary and identifies relevant paths or
segments when topology data is available.

### 10.7 Fault Correlation Agent

-   Receives findings from the specialist agents.
-   Groups evidence that may indicate the same incident.
-   Compares competing explanations.
-   Identifies the most likely root cause.
-   Records contradictory or missing evidence.
-   Returns an inconclusive result when evidence is inadequate.

### 10.8 Recommendation and Reporting Agent

-   Converts the correlated diagnosis into the required report
    structure.
-   Includes supporting evidence and source agents.
-   Lists alternative explanations and limitations.
-   Recommends practical corrective actions.
-   Produces structured JSON and, optionally, a human-readable summary.

## 11. Inter-agent Communication Contract

Use a versioned JSON envelope for all agent messages. This is a proposed
protocol design; the challenge requires a documented interoperable
format but does not prescribe this exact schema.

### 11.1 Message envelope

``` json
{
  "schema_version": "1.0",
  "message_id": "MSG-0001",
  "incident_id": "INC-8832",
  "timestamp": "2026-10-31T10:00:00Z",
  "source_agent": "performance_agent",
  "target_agent": "fault_correlation_agent",
  "message_type": "agent_finding",
  "status": "success",
  "payload": {
    "finding_id": "FIND-001",
    "category": "performance",
    "metric": "link_utilization_pct",
    "value": 94,
    "unit": "%",
    "severity": "high",
    "device_id": "HOSTEL_CORE_SW_01",
    "interpretation": "High link utilization may indicate congestion."
  },
  "warnings": []
}
```

### 11.2 Required envelope fields

  Field              Meaning
  ------------------ ------------------------------------------
  `schema_version`   Version of the message contract
  `message_id`       Unique message identifier
  `incident_id`      Diagnostic run/incident identifier
  `timestamp`        Message creation time in ISO 8601 format
  `source_agent`     Agent producing the message
  `target_agent`     Intended recipient or orchestrator
  `message_type`     Finding, task, status, error, or result
  `status`           Success, partial, failed, or skipped
  `payload`          Structured message body
  `warnings`         Validation or interpretation warnings

### 11.3 Interoperability rules

-   Metric names must be documented.
-   Every numeric metric must specify its unit.
-   Timestamps must use a consistent timezone convention; ISO 8601 UTC
    is recommended.
-   Device identifiers must be treated consistently across agents.
-   Unknown fields should not silently overwrite known fields.
-   Missing required fields must produce validation errors.
-   Schema versions must be checked before processing.
-   Unit conversions must be explicit and logged.
-   A receiver must report unsupported message types or incompatible
    versions.
-   Agents should not interpret a missing value as zero.

## 12. Suggested Telemetry Data Contract

A normalized telemetry record may use the following shape. Adapt it to
the actual organizer dataset once that dataset is available.

``` json
{
  "timestamp": "2026-10-31T10:00:00Z",
  "device_id": "HOSTEL_CORE_SW_01",
  "device_type": "switch",
  "status": "up",
  "latency_ms": 280,
  "jitter_ms": 18,
  "packet_loss_pct": 3.2,
  "throughput_mbps": 120,
  "bandwidth_mbps": 150,
  "link_utilization_pct": 94,
  "cpu_utilization_pct": 68,
  "memory_utilization_pct": 72,
  "queue_drops": 160,
  "interface_errors": 4,
  "wireless_signal_dbm": null,
  "topology": {
    "connected_to": ["UPSTREAM_CORE_01"]
  }
}
```

This is an illustrative proposed schema, not a claim about the exact
organizer-provided dataset. The ingestion layer should map the actual
input fields into this normalized model.

## 13. Diagnostic Report Contract

The final application output must be structured JSON. The following
shape follows the fields illustrated in the challenge brief.

``` json
{
  "incident_id": "INC-8832",
  "status": "diagnosed",
  "suspected_root_cause": "Likely link congestion causing egress queue drops",
  "confidence": 0.86,
  "affected_devices": ["HOSTEL_CORE_SW_01"],
  "supporting_evidence": [
    {
      "metric": "link_utilization_pct",
      "value": 94,
      "interpretation": "High link utilization"
    },
    {
      "metric": "queue_drops",
      "value": 160,
      "interpretation": "Elevated packet drops"
    },
    {
      "metric": "latency_ms",
      "value": 280,
      "interpretation": "Elevated network latency"
    }
  ],
  "alternative_causes": ["Upstream link congestion"],
  "recommended_actions": [
    "Inspect upstream and egress link utilization",
    "Review queue configuration and traffic distribution"
  ],
  "evidence_sources": [
    "performance_agent",
    "infrastructure_agent"
  ],
  "limitations": [
    "Root cause requires further verification"
  ]
}
```

The values above are illustrative only. The challenge brief explicitly
says they do not represent actual campus network measurements.

### 13.1 Inconclusive report behavior

When evidence is insufficient, use a status such as
`insufficient_evidence`, describe what is missing, and avoid asserting
an exact root cause. The precise status enum is a proposed
implementation choice and should be documented.

## 14. Confidence and Evidence Strategy

The challenge requires a documented scoring method or calibrated model,
but does not prescribe one. For the prototype, implement a transparent
evidence-based scoring method.

Suggested approach:

1.  Define rules for each supported fault pattern.
2.  Assign evidence strength to each matching signal.
3.  Group corroborating signals by candidate cause.
4.  Account for contradictory, missing, stale, or low-quality data.
5.  Normalize the resulting score to a documented confidence range.
6.  Return `insufficient_evidence` if minimum evidence requirements are
    not met.

Do not present a score as a statistically calibrated probability unless
it has actually been calibrated against suitable labeled data. In the
UI, label it **confidence score** or use categories such as Low, Medium,
and High, and provide a short explanation.

## 15. API Design

The following REST endpoints are proposed for the web implementation.

  -------------------------------------------------------------------------------------------
  Method                  Endpoint                                    Purpose
  ----------------------- ------------------------------------------- -----------------------
  `GET`                   `/api/health`                               Backend health check

  `GET`                   `/api/scenarios`                            List available sample
                                                                      scenarios

  `POST`                  `/api/telemetry/validate`                   Validate and normalize
                                                                      telemetry

  `POST`                  `/api/diagnostics`                          Start a diagnostic run

  `GET`                   `/api/diagnostics/{incident_id}`            Retrieve run status and
                                                                      result

  `GET`                   `/api/diagnostics/{incident_id}/agents`     Retrieve agent
                                                                      statuses/findings

  `GET`                   `/api/diagnostics/{incident_id}/messages`   Retrieve inter-agent
                                                                      messages

  `GET`                   `/api/diagnostics/{incident_id}/report`     Retrieve final JSON
                                                                      report
  -------------------------------------------------------------------------------------------

For a short hackathon build, the diagnostic endpoint may run
synchronously. If execution becomes long-running, use a background task
and polling or server-sent events. Real-time streaming is an
enhancement, not a mandatory requirement.

## 16. Error Handling

  -----------------------------------------------------------------------
  Condition                           Expected behavior
  ----------------------------------- -----------------------------------
  Invalid JSON or unreadable file     Reject input with a clear
                                      validation response

  Missing required metric             Mark field missing; continue only
                                      if remaining evidence is sufficient

  Unknown metric name                 Warn or reject according to the
                                      documented mapping policy

  Unsupported unit                    Flag incompatibility; do not
                                      compare as if units match

  Unsupported schema version          Return a clear compatibility error

  Agent timeout/failure               Record agent failure and continue
                                      only if diagnosis remains
                                      meaningful

  Conflicting agent findings          Preserve both findings and ask
                                      correlation stage to compare them

  Insufficient telemetry              Return inconclusive diagnosis with
                                      limitations

  No topology data                    Omit unsupported path claims and
                                      state the limitation
  -----------------------------------------------------------------------

## 17. Testing Strategy

### Unit tests

-   Telemetry parsing and normalization.
-   Required field and unit validation.
-   Each agent's rule evaluation.
-   Message schema validation.
-   Confidence calculation.
-   Final report serialization.

### Integration tests

-   Performance and infrastructure agents contribute to one diagnosis.
-   Orchestrator handles a failed agent.
-   Correlation agent handles conflicting findings.
-   Reporting agent emits the required JSON fields.
-   API returns clear validation errors.

### Scenario tests

  --------------------------------------------------------------------------
  Scenario                Signals to represent    Expected system behavior
  ----------------------- ----------------------- --------------------------
  Normal operation        Metrics within expected Report normal/ no clear
                          ranges                  fault; avoid inventing a
                                                  cause

  Link congestion         High utilization, queue Consider congestion and
                          drops, increased        show supporting metrics
                          latency                 

  Weak Wi-Fi signal       Poor signal quality,    Identify wireless quality
                          increased               as a candidate cause
                          retransmissions         

  Ethernet/interface      Rising interface        Identify interface/link
  fault                   errors, link            fault as a candidate
                          instability, packet     
                          loss                    

  DNS/DHCP failure        Service-specific        Identify service-level
                          connectivity symptoms   failure as a candidate if
                                                  data supports it

  Interoperability        Missing fields,         Show
  failure                 incompatible names,     validation/compatibility
                          units, or schema        errors clearly
  --------------------------------------------------------------------------

### Reproducibility checklist

-   Include sample inputs for each scenario.
-   Include exact setup and run commands in the repository README.
-   Pin or document dependencies.
-   Provide automated test commands.
-   Demonstrate at least one complete end-to-end diagnosis.
-   Demonstrate at least one malformed, missing, or incompatible input.

------------------------------------------------------------------------

# Part C --- UI/UX Design Specification

## 18. Design Direction

### 18.1 Experience principles

-   **Clarity first:** prioritize the diagnosis and its evidence.
-   **Explainability:** never show a root-cause label without supporting
    signals.
-   **Progress visibility:** make agent execution and communication
    visible.
-   **Progressive disclosure:** show a concise summary first, then
    detailed metrics and messages.
-   **Honest uncertainty:** distinguish confirmed observations from
    probable explanations.
-   **Operational usability:** use clear labels, readable charts, and
    actionable recommendations.

### 18.2 Proposed visual language

A restrained network-operations dashboard is recommended:

-   Dark navy or charcoal application shell.
-   Neutral light content surfaces for readability.
-   One restrained accent color for primary actions.
-   Semantic status colors: green for healthy, amber for warning, red
    for critical, gray for unavailable.
-   Clear typography and consistent spacing.
-   Avoid decorative effects that compete with telemetry and diagnostic
    evidence.

These are design recommendations, not visual requirements from the
challenge brief.

## 19. Information Architecture

``` text
NetCoop AI
├── Overview
├── New Diagnosis
│   ├── Upload Telemetry
│   ├── Select Scenario
│   └── Validate Input
├── Diagnostic Run
│   ├── Run Summary
│   ├── Agent Activity
│   ├── Inter-agent Messages
│   └── Telemetry Overview
├── Diagnostic Report
│   ├── Probable Root Cause
│   ├── Confidence and Limitations
│   ├── Affected Devices
│   ├── Supporting Evidence
│   ├── Alternative Causes
│   └── Recommended Actions
├── Reports / Run History
└── Documentation
```

## 20. Screens and Page Requirements

### 20.1 Overview dashboard

**Purpose:** give the operator a quick view of the prototype and provide
a clear starting point.

Components: - Header with NetCoop AI identity. - Primary action: **Start
Diagnosis**. - Summary cards: recent runs, diagnosed incidents,
inconclusive runs, agent availability. - Recent diagnostic runs table. -
Scenario quick-start section. - Short system status indicator.

Only show metrics that are actually available from the backend; do not
fabricate dashboard statistics.

### 20.2 New diagnosis page

**Purpose:** provide telemetry input and scenario selection.

Components: - Drag-and-drop file upload. - Supported format and schema
guidance. - Sample scenario selector. - Optional incident
name/description. - Validate button. - Validation result panel with
errors and warnings. - Start Diagnosis button, enabled only when input
is acceptable.

States: - Empty. - File selected. - Validating. - Validation
successful. - Validation warnings. - Validation failed.

### 20.3 Diagnostic run page

**Purpose:** communicate progress and demonstrate agent
interoperability.

Components: - Incident/run ID and run status. - Step-by-step agent
execution list. - Agent cards showing name, responsibility, status, and
short finding. - Inter-agent message timeline with source and target
agent. - Telemetry snapshot with key metrics. - Error/warning panel. -
Link to final report when available.

Suggested agent states: - Pending. - Running. - Completed. - Partial. -
Failed. - Skipped.

Do not display simulated live progress as real execution. If the backend
runs synchronously, show a clear loading state and update after the
response.

### 20.4 Diagnostic report page

**Purpose:** make the outcome understandable and verifiable.

Recommended order:

1.  **Diagnosis summary** --- probable cause and status.
2.  **Confidence** --- score/category with explanation.
3.  **Affected devices** --- list of identifiable devices or segments.
4.  **Supporting evidence** --- metric, observed value, unit,
    interpretation, source agent.
5.  **Alternative causes** --- competing explanations.
6.  **Recommended actions** --- practical troubleshooting steps.
7.  **Limitations** --- missing data and required verification.
8.  **Agent contributions** --- findings that informed the report.
9.  **Raw JSON** --- expandable structured output with copy/download
    action.

### 20.5 Run history page

Components: - Incident ID. - Date/time. - Input scenario or dataset
name. - Final status. - Suspected cause, if available. - Open report
action.

For the MVP, history can be session-based or stored locally in SQLite.
Persistent workflow recovery is optional.

### 20.6 Documentation page

Include: - Agent responsibilities. - Message protocol and field
meanings. - Supported telemetry fields and units. - Confidence method. -
Scenario descriptions. - Known limitations. - Setup and test
instructions.

## 21. Key Interaction Flow

``` mermaid
flowchart TD
    A[Open Dashboard] --> B[Start Diagnosis]
    B --> C[Upload Telemetry or Select Scenario]
    C --> D[Validate Input]
    D --> E{Input usable?}
    E -- No --> F[Show Errors and Guidance]
    F --> C
    E -- Yes --> G[Start Diagnostic Run]
    G --> H[Orchestrator Dispatches Agent Tasks]
    H --> I[Agents Analyze Telemetry]
    I --> J[Agents Exchange Structured Findings]
    J --> K[Fault Correlation]
    K --> L{Evidence sufficient?}
    L -- No --> M[Inconclusive Result and Limitations]
    L -- Yes --> N[Probable Root Cause and Confidence]
    M --> O[Generate Unified JSON Report]
    N --> O
    O --> P[Display Report and Agent Evidence]
    P --> Q[Inspect or Export JSON]
```

## 22. UI Components

  -----------------------------------------------------------------------
  Component               Purpose                 Important states
  ----------------------- ----------------------- -----------------------
  `MetricCard`            Show a telemetry metric Normal, warning,
                                                  critical, unavailable

  `AgentStatusCard`       Show agent progress and Pending, running,
                          finding                 completed, failed

  `MessageTimeline`       Show agent-to-agent     Empty, populated, error
                          communication           

  `EvidenceTable`         Show metric evidence    Populated, no evidence
                          and interpretation      

  `ConfidenceIndicator`   Show documented         Low, medium, high,
                          confidence              insufficient
                          score/category          

  `DeviceList`            Show affected devices   Populated, unknown

  `RecommendationList`    Show corrective actions Populated, empty

  `ValidationSummary`     Show input issues       Valid, warning, invalid

  `JsonViewer`            Show final structured   Collapsed, expanded
                          report                  
  -----------------------------------------------------------------------

## 23. Accessibility and Responsive Behavior

-   Use semantic headings and form labels.
-   Ensure keyboard access for upload, scenario selection, and report
    actions.
-   Do not communicate status through color alone; include text and
    icons/labels.
-   Maintain readable contrast.
-   Use tables for detailed evidence and cards for summaries.
-   On smaller screens, stack summary cards and allow wide evidence
    tables to scroll horizontally.
-   Provide clear loading, empty, success, warning, and error states.

------------------------------------------------------------------------

# Part D --- Workflow Architecture

## 24. End-to-end System Workflow

1.  **Input:** operator uploads telemetry or chooses a sample scenario.
2.  **Validation:** backend parses the input and checks schema, required
    fields, types, and units.
3.  **Normalization:** supported aliases and units are mapped to a
    common internal representation.
4.  **Incident creation:** orchestrator creates an incident ID and
    diagnostic context.
5.  **Task dispatch:** orchestrator sends relevant telemetry/context to
    specialist agents.
6.  **Specialist analysis:** performance, infrastructure, and
    connectivity agents independently analyze their domains.
7.  **Message exchange:** agents publish structured findings using the
    documented message contract.
8.  **Correlation:** fault correlation agent compares findings and
    candidate explanations.
9.  **Confidence assessment:** scoring logic evaluates evidence
    strength, agreement, contradictions, and missing data.
10. **Recommendation:** reporting agent prepares corrective actions and
    limitations.
11. **Report generation:** backend creates the unified JSON report.
12. **Presentation:** dashboard displays the diagnosis, evidence, agent
    contributions, and report.

## 25. Agent Workflow Sequence

``` mermaid
sequenceDiagram
    participant UI as Web Dashboard
    participant API as Backend API
    participant OR as Orchestrator
    participant PA as Performance Agent
    participant IA as Infrastructure Agent
    participant CA as Connectivity Agent
    participant FC as Fault Correlation Agent
    participant RR as Reporting Agent

    UI->>API: Submit telemetry
    API->>API: Validate and normalize
    API->>OR: Create diagnostic context
    OR->>PA: Analyze performance metrics
    OR->>IA: Analyze device health
    OR->>CA: Analyze topology/connectivity
    PA-->>OR: Structured performance findings
    IA-->>OR: Structured infrastructure findings
    CA-->>OR: Structured connectivity findings
    OR->>FC: Consolidated agent findings
    FC->>FC: Compare causes and evidence
    FC-->>OR: Probable cause / insufficient evidence
    OR->>RR: Diagnosis + evidence + limitations
    RR-->>OR: Unified JSON report
    OR-->>API: Diagnostic result
    API-->>UI: Report and run details
```

## 26. Example Rule Correlation

Illustrative link-congestion pattern:

-   High link utilization is observed.
-   Egress queue drops are elevated.
-   Latency is elevated.
-   Multiple findings refer to the same device or connected link.

The correlation agent may rank link congestion as a probable cause,
while retaining upstream congestion as an alternative explanation. It
should recommend inspecting upstream and egress utilization and
reviewing queue configuration and traffic distribution. This pattern is
based on the illustrative example in the challenge brief; actual
thresholds must be defined using the supplied or documented test data.

------------------------------------------------------------------------

# Part E --- Web Architecture

## 27. Web Application Architecture

The web application should use a simple client-server architecture:

-   **Client:** React application for data input, run visibility, and
    report exploration.
-   **API layer:** FastAPI endpoints for validation, diagnosis, run
    retrieval, and report retrieval.
-   **Application layer:** orchestration and diagnostic services.
-   **Agent layer:** independently implemented specialist agents
    communicating through versioned structured messages.
-   **Data layer:** sample telemetry files and optional SQLite/JSON
    storage for run records.

``` mermaid
flowchart TB
    subgraph Browser[Browser]
        UI[React + TypeScript UI]
        STATE[Client State]
        UI <--> STATE
    end

    subgraph Server[Python Backend]
        ROUTES[FastAPI Routes]
        SCHEMA[Pydantic Schemas]
        SERVICE[Diagnostic Service]
        ORCH[Agent Orchestrator]
        CORR[Fault Correlation]
        REPORT[Report Generator]
        ROUTES --> SCHEMA --> SERVICE --> ORCH
        ORCH --> CORR --> REPORT
    end

    subgraph Agents[Specialist Agents]
        PERF[Performance Agent]
        INFRA[Infrastructure Agent]
        CONN[Connectivity Agent]
    end

    subgraph Storage[Prototype Storage]
        DATA[Sample Telemetry]
        DB[(SQLite / JSON Run Store)]
    end

    UI <-->|HTTPS / JSON| ROUTES
    ORCH <--> PERF
    ORCH <--> INFRA
    ORCH <--> CONN
    SERVICE <--> DATA
    REPORT --> DB
    SERVICE --> DB
```

## 28. Suggested Repository Structure

``` text
netcoop-ai/
├── README.md
├── docs/
│   ├── PRD-TRD-UIUX-Architecture.md
│   ├── agent-protocol.md
│   └── test-scenarios.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── App.tsx
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── agents/
│   │   │   ├── performance_agent.py
│   │   │   ├── infrastructure_agent.py
│   │   │   ├── connectivity_agent.py
│   │   │   ├── correlation_agent.py
│   │   │   └── reporting_agent.py
│   │   ├── orchestration/
│   │   ├── telemetry/
│   │   └── storage/
│   ├── tests/
│   └── requirements.txt
├── data/
│   ├── normal.json
│   ├── link_congestion.json
│   ├── weak_wifi.json
│   ├── interface_fault.json
│   ├── dns_dhcp_failure.json
│   └── incompatible_schema.json
└── scripts/
    └── run_demo.sh
```

This is a proposed organization; it can be simplified to fit the team's
language and framework choices.

## 29. Suggested Build and Deployment Layout

For the hackathon prototype:

-   Run the frontend and backend as separate development services.
-   Configure the frontend API base URL through an environment variable.
-   Keep secrets and model API keys on the backend, never in browser
    code.
-   Enable CORS only for the intended frontend origin.
-   Validate all incoming files and payloads.
-   Set upload size limits.
-   Log incident IDs, agent statuses, validation failures, and report
    generation.
-   Use synthetic or authorized telemetry only.
-   Do not expose credentials, private network configuration, or
    sensitive telemetry in public demo logs.

Production hosting provider and infrastructure are not specified by the
challenge brief. Select them based on the team's available accounts and
deployment constraints.

## 30. Security and Operational Considerations

-   Treat uploaded telemetry as untrusted input.
-   Validate file type, size, schema, and values.
-   Avoid executing uploaded content.
-   Keep credentials in backend environment variables.
-   Avoid logging secrets or unnecessarily sensitive network details.
-   Restrict any future remediation feature behind explicit
    authorization.
-   Use read-only analysis for the hackathon demo.
-   Clearly label synthetic/demo data.
-   Preserve enough logs to reproduce a diagnostic run.

------------------------------------------------------------------------

# Part F --- 24-hour Implementation Plan

## 31. Suggested Team Execution Plan

This is a proposed schedule, not a schedule mandated by the challenge.

  ------------------------------------------------------------------------
  Phase                              Time allocation Deliverable
  --------------------- ---------------------------- ---------------------
  Scope and data                              1 hour Agreed schema,
  contract                                           scenario list, agent
                                                     responsibilities

  Backend and                                3 hours API, telemetry
  validation                                         parser, normalized
                                                     model

  Specialist agents                          4 hours At least three
                                                     working analysis
                                                     agents

  Orchestration and                          3 hours Structured messages
  protocol                                           and shared diagnosis

  Correlation and                            3 hours Evidence-based result
  report                                             and JSON report

  Frontend dashboard                         4 hours Upload, run status,
                                                     agent activity,
                                                     report

  Testing and                                3 hours Scenario tests and
  integration                                        malformed-input
                                                     handling

  Demo and                                   2 hours Setup guide,
  documentation                                      architecture, 3--5
                                                     minute demo
  ------------------------------------------------------------------------

If time becomes constrained, prioritize mandatory acceptance criteria
over optional integrations and visual polish.

## 32. Demo Walkthrough

A focused three-to-five-minute demo can follow this sequence:

1.  Introduce the campus network diagnosis problem.
2.  Select a synthetic link-congestion scenario.
3.  Submit the telemetry and show validation.
4.  Start a diagnostic run.
5.  Show at least two specialist agents analyzing the same incident from
    different perspectives.
6.  Show structured messages and how findings reach the correlation
    agent.
7.  Display the probable root cause, confidence, evidence, affected
    device, alternative cause, and recommended actions.
8.  Open the final JSON report.
9.  Run an incompatible or malformed input example and show the
    validation/error behavior.

## 33. Challenge Compliance Checklist

  -----------------------------------------------------------------------
  Challenge requirement   Planned implementation  Priority
  ----------------------- ----------------------- -----------------------
  Multiple collaborating  At least two; target    Mandatory
  agents                  four to five            

  Agent interoperability  Versioned structured    Mandatory
                          JSON protocol           

  Agent orchestration     Central orchestrator    Mandatory

  Network fault diagnosis Specialist analysis and Mandatory
                          correlation             

  Unified diagnostic      JSON with cause,        Mandatory
  report                  evidence, uncertainty,  
                          actions                 

  Validation and error    Schema, missing-field,  Mandatory
  handling                and unit checks         

  Reproducible testing    Scenarios, tests, setup Mandatory
  and documentation       guide, demo             

  MCP                     Optional integration    Optional

  HITL                    Human review of         Optional
                          recommendations         

  Persistent workflow     Optional run            Optional
  state                   persistence             

  Interactive dashboard   React dashboard; CLI is Optional, encouraged
                          also acceptable         

  Automated remediation   Simulated only unless   Optional
                          authorized              
  -----------------------------------------------------------------------

## 34. Evaluation Alignment

The challenge evaluation gives the highest weight to interoperability
and protocol design, followed by diagnostic accuracy and evidence
quality, orchestration/conflict resolution, and robustness.

  --------------------------------------------------------------------------------------
  Evaluation criterion                                      Weight Design response
  ----------------------------------- ---------------------------- ---------------------
  Agent interoperability and protocol                          30% Versioned message
  design                                                           envelope, documented
                                                                   fields/units,
                                                                   validation

  Diagnostic accuracy and evidence                             25% Rule-backed findings,
  quality                                                          evidence references,
                                                                   alternatives,
                                                                   uncertainty

  Agent orchestration and conflict                             15% Orchestrator,
  resolution                                                       correlation stage,
                                                                   contradiction
                                                                   handling

  Robustness to                                                15% Normalization, schema
  missing/inconsistent/incompatible                                checks, controlled
  data                                                             errors

  Code quality, documentation, and                              5% Modular code, README,
  demonstration                                                    tests, reproducible
                                                                   demo

  Innovation, usability, and                                   10% Agent activity
  extensibility                                                    dashboard,
                                                                   explainable report,
                                                                   extensible modules
  --------------------------------------------------------------------------------------

## 35. Minimum Acceptance Checklist

Before calling the prototype complete, verify:

-   [ ] At least two functional agents with distinct responsibilities
    collaborate.
-   [ ] Agents exchange structured messages.
-   [ ] Message formats, fields, and units are documented.
-   [ ] Findings from multiple agents contribute to one diagnosis.
-   [ ] At least one malformed, missing, or incompatible input is
    handled.
-   [ ] The report contains probable root cause or insufficient-evidence
    status.
-   [ ] Supporting evidence and recommended actions are present.
-   [ ] Confidence and limitations are included.
-   [ ] A reproducible run uses supplied or documented test data.
-   [ ] The demo shows end-to-end diagnosis and inter-agent
    communication.
-   [ ] The repository includes setup instructions and test scripts.

------------------------------------------------------------------------

## 36. Assumptions, Open Decisions, and Source Boundaries

### Requirements explicitly stated in the challenge brief

-   The project is a 24-hour hackathon challenge in AI and computer
    networks.
-   The target is a multi-agent system for network fault diagnosis and
    interoperability.
-   At least two functional agents must collaborate; four to five are
    encouraged.
-   Agent interoperability, orchestration, diagnosis, unified reporting,
    validation/error handling, and reproducible documentation/testing
    are mandatory.
-   MCP, HITL, durable workflow state, and automated remediation are
    optional.
-   An interactive dashboard is encouraged; a CLI is acceptable.
-   Synthetic telemetry, organizer-provided scenarios, or authorized
    test-environment data may be used.
-   A structured JSON report is required.
-   The demo video should be three to five minutes.
-   The system must not claim an exact root cause when evidence is
    insufficient.

### Proposed design decisions in this document

-   React + TypeScript frontend and Python + FastAPI backend.
-   Five-agent logical architecture.
-   Versioned JSON message envelope.
-   Suggested telemetry normalization schema and REST endpoints.
-   Dashboard page structure and visual design direction.
-   Example repository structure, test plan, confidence strategy, and
    24-hour build schedule.

These are implementation recommendations and may be changed by the team.

### Open decisions to resolve during implementation

1.  What exact format and fields are present in the organizer's sample
    telemetry generator output?
2.  Which metrics have known healthy ranges or thresholds in the
    supplied scenarios?
3.  Will the team use a rule-based system, an LLM, or a hybrid approach?
4.  Will agents run sequentially or concurrently?
5.  Is run history needed beyond the current browser session?
6.  Which hosting environment is available to the team?
7.  What evidence threshold should trigger an inconclusive result?

------------------------------------------------------------------------

## 37. Reference

Primary source:

**NetCoop AI --- Multi-Agent Network Fault Diagnosis and
Interoperability.** *Agentic AI Grand Finale Problem Statement*, 7-page
hackathon challenge brief supplied with this request.

All mandatory requirements, suggested agent roles, telemetry categories,
test scenarios, output fields, deliverables, evaluation weights, and
minimum acceptance criteria in this document are derived from that
brief. Technology choices, endpoint designs, UI structure, repository
layout, and implementation schedule are proposed recommendations.

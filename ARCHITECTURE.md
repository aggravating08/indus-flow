# Indus Flow — System Architecture
**Open Agent Hackathon 2026** | **Team Indus**

---

## 1. High-Level Architecture Overview

Indus Flow is an autonomous supply chain resilience agent designed to shift enterprise operations from reactive fire-fighting to predictive, counterfactual mitigation.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA VIRTUALIZATION LAYER                       │
│  Zetaris Cloud Gateway (Lightning SQL / Federated Relational Views)    │
│  - ERP Master Inventory Records                                        │
│  - Active Shipment AIS Telemetry & Port Congestion Feeds               │
│  - Tier 1 & Tier 2 Supplier Operational Statuses                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      DISRUPTION DETECTION ENGINE                       │
│  - Anomaly Detection over Lead Times, Buffer Burn Rates, Port Delays   │
│  - Severity Scoring (CRITICAL / HIGH / MEDIUM / LOW)                   │
│  - Emits Structured DisruptionAlert Entities                           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    METERLESS WORLD MODEL ENGINE                        │
│  - Multi-Branch Counterfactual Rollout Simulation                      │
│  - N-Step State Trajectory Modeling (Inventory x Delays x Congestion)  │
│  - Quantified Stockout Probability & Dynamic Risk Index Scoring        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   NVIDIA NIM REASONING ENGINE                          │
│  - Model: meta/llama-3.1-70b-instruct                                  │
│  - Multi-Criteria Trade-off Analysis (Cost vs Delay vs SLA Penalties)  │
│  - Structured Action Recommendations & Executive Rationale             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 GOVERNANCE & HUMAN APPROVAL GATE                       │
│  - Micro-budget Threshold ($1,000 USD Rule)                            │
│  - Consequential Actions: Gated to PENDING_APPROVAL                    │
│  - Operator Review, Confirmation, Rejection, or Parameter Override     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 EXECUTION DISPATCH & AUDIT TRAIL                       │
│  - State Mutation (Inventory Adjustment, Carrier Rerouting)            │
│  - Immutable Cryptographic-Ready Audit Log                             │
│  - Live Web Observability Dashboard (FastAPI / SSE / REST)             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Modules Breakdown

### 2.1 Data Virtualization (Zetaris Semantic Layer)
* **File:** [`src/connectors/zetaris_connector.py`](file:///Users/asiyaali/Downloads/indus-open-agent/src/connectors/zetaris_connector.py)
* **Function:** Queries disparate internal databases and external logistics APIs through a unified virtual schema (`virtual_supply_chain_catalog`). Eliminates physical ETL latency.
* **Modes:**
  * `LIVE_ZETARIS_GATEWAY`: Connects over port 10000 via PostgreSQL wire protocol to a running Zetaris cluster.
  * `MOCK_SEMANTIC_ADAPTER`: Built-in local relational mock providing zero-dependency developer and evaluator execution.

### 2.2 Cognitive Engine (Meterless World Model)
* **File:** [`src/engines/world_model.py`](file:///Users/asiyaali/Downloads/indus-open-agent/src/engines/world_model.py)
* **Function:** Simulates the physical progression of the supply network across candidate policies (Status Quo vs. Port Reroute vs. Air Freight Buffer vs. Alternate Supplier PO).
* **Key Output:** Yields step-by-step state trajectories (`StepTrajectory`), projected risk indices, and calibrated confidence bounds ($[R_{\min}, R_{\max}]$).

### 2.3 Reasoning Engine (NVIDIA NIM)
* **File:** [`src/connectors/nvidia_nim.py`](file:///Users/asiyaali/Downloads/indus-open-agent/src/connectors/nvidia_nim.py)
* **Function:** Ingests the top-ranked simulation branches and produces structured decision traces. Computes cost-benefit justification (e.g. evaluating whether $2,550 air freight expense is justified to protect $32,500 in downtime penalties).
* **Modes:**
  * `LIVE_NVIDIA_NIM`: Authenticated calls to `https://integrate.api.nvidia.com/v1/chat/completions` with exponential backoff retry.
  * `MOCK_ADAPTER`: Deterministic trade-off rationale emulator for offline benchmarking.

### 2.4 Human-in-the-Loop Governance
* **File:** [`src/data/repository.py`](file:///Users/asiyaali/Downloads/indus-open-agent/src/data/repository.py) & [`src/api/routes.py`](file:///Users/asiyaali/Downloads/indus-open-agent/src/api/routes.py)
* **Function:** Gating mechanism ensuring high-risk or high-cost actions cannot execute automatically without human sign-off.
* **States:** `PENDING_APPROVAL` $\to$ `APPROVED` or `REJECTED`.
* **Auditability:** Every transition records operator identity, timestamp, and justification.

---

## 3. API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health, model, and engine metadata |
| `GET` | `/api/v1/overview` | High-level KPI metrics & integration modes |
| `GET` | `/api/v1/inventory` | Real-time stock levels, burn rates, days-of-supply |
| `GET` | `/api/v1/shipments` | In-transit tracking, delay days, status |
| `GET` | `/api/v1/suppliers` | Supplier directory, tiers, reliability scores |
| `GET` | `/api/v1/alerts` | Active supply chain disruption alerts |
| `GET` | `/api/v1/decisions` | All generated mitigation decisions |
| `POST` | `/api/v1/agent/run` | Triggers full sense $\to$ simulate $\to$ decide cycle |
| `POST` | `/api/v1/decisions/{id}/approve` | Human approval gate confirmation |
| `POST` | `/api/v1/decisions/{id}/reject` | Human rejection gate with audit reasoning |
| `POST` | `/api/v1/simulation/simulate` | Custom on-demand Meterless World Model run |
| `GET` | `/api/v1/audit-log` | Immutable operational audit trail |
| `POST` | `/api/v1/reset` | Resets state to clean initial baseline seeds |

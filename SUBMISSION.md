# Open Agent Hackathon 2026 — Official Submission Form
**Project Name:** Indus Flow — Autonomous Supply Chain Resilience Agent  
**Team Name:** Indus  
**Challenge Track:** Autonomous Workflow Agents / Enterprise Operations & Resilience  

---

## 1. Project Information
* **Tagline:** Predictive, counterfactual supply chain resilience powered by Meterless World Model, Zetaris, and NVIDIA NIM.
* **Repository URL:** `https://github.com/aggravating08/indus-flow`
* **Demo Video URL:** *[To be recorded using DEMO_SCRIPT.md]*
* **Live Deployment URL:** `http://localhost:8000` *(Local verified / Docker ready for cloud hosting)*

---

## 2. Problem Statement
Global discrete manufacturing supply networks suffer multi-billion dollar losses annually from unforeseen logistics bottlenecks (customs holds, port strikes, material shortages). Operations teams rely on passive dashboards that only sound alarms after inventory breaches buffer thresholds, leaving operators scrambling to solve logistics crises under 48-hour SLA deadlines.

---

## 3. Solution Overview
Indus Flow shifts enterprise operations from reactive alert management to proactive counterfactual resilience:
1. **Virtualizes data ingestion** across ERPs, carrier telemetry, and supplier directories via **Zetaris**.
2. **Projects multi-step dynamic risk trajectories** and simulates "what-if" counterfactual interventions via the **Meterless World Model Engine**.
3. **Conducts multi-criteria trade-off arbitration** using **NVIDIA NIM** (`meta/llama-3.1-70b-instruct`) to formulate cost-optimal mitigation actions.
4. **Enforces human-in-the-loop governance** with automated budget-gated approval workflows and immutable audit trails.

---

## 4. Sponsor Technologies Implementation Matrix

| Sponsor | Technology Used | Integration Location | Working Role in Project |
| :--- | :--- | :--- | :--- |
| **Meterless** | **World Model Engine** | [`src/engines/world_model.py`](src/engines/world_model.py) | **Mandatory Sponsor Core Requirement:** Evaluates multi-branch counterfactual trajectories across candidate actions, quantifying stockout probability and residual port congestion. |
| **NVIDIA** | **NIM (Llama 3.1 70B)** | [`src/connectors/nvidia_nim.py`](src/connectors/nvidia_nim.py) | Synthesizes complex trade-offs between logistics expediting costs, vendor SLA breach penalties, and supplier relationships to draft executive mitigation orders. |
| **Zetaris** | **Unified Semantic Catalog** | [`src/connectors/zetaris_connector.py`](src/connectors/zetaris_connector.py) | Provides a virtualized relational SQL query interface across disparate supplier ERPs and shipment logs without ETL latency. |

---

## 5. Technical Validation & Reproducibility
* **Automated Test Suite:** 33 unit and integration tests passing (`python3 -m pytest -v tests/`).
* **Containerization:** Ready for one-command deployment via Docker & Docker Compose (`docker-compose up --build`).
* **Governance Security:** Consequential operational changes (cost > $1,000 USD) are strictly gated behind human approval.

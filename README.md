# Indus Flow — Autonomous Supply Chain Resilience Agent
> **Open Agent Hackathon 2026 Submission** | **Team Indus**

[![Tests](https://img.shields.io/badge/Tests-Passing%20(3%2F3)-brightgreen)](#automated-testing)
[![Meterless Engine](https://img.shields.io/badge/Meterless-World%20Model%20Engine-blue)](https://meterless.ai/engines.html)
[![Data Layer](https://img.shields.io/badge/Data%20Layer-Zetaris%20Unified%20Semantic%20Catalog-orange)](https://www.zetaris.com/)
[![Inference](https://img.shields.io/badge/Inference-NVIDIA%20NIM%20(Llama%203.1%2070B)-76B900)](https://build.nvidia.com)

---

## 1. Problem & User Impact
* **Target User:** Global supply chain directors, procurement leads, and inventory planners.
* **The Problem:** Modern enterprise supply networks span thousands of external suppliers, ports, and carrier APIs. When unexpected disruption signals emerge (port strikes, customs holds, raw material shortages), human operators face a 36-to-72 hour latency lag before discovering stockout risks. Passive dashboards alert operators too late, incurring millions in emergency air-freight penalties and unfulfilled customer SLAs.
* **The Solution (*Indus Flow*):** An autonomous resilience agent that:
  1. Continuously queries heterogeneous supplier and ERP feeds through **Zetaris's federated semantic layer**.
  2. Runs multi-step counterfactual simulations using the **Meterless World Model Engine** to predict stockouts and calculate downstream risk probabilities.
  3. Formulates multi-criteria trade-off decisions using **NVIDIA NIM** (meta/llama-3.1-70b-instruct) and executes mitigation orders autonomously.

---

## 2. Architecture Diagram

```
       [External Supplier Feeds & ERPs]       [Real-time Port Telemetry]
                      │                                    │
                      └─────────────────┬──────────────────┘
                                        ▼
                      ┌──────────────────────────────────┐
                      │      Zetaris Semantic Layer      │
                      │   (Federated SQL Virtualization) │
                      └─────────────────┬────────────────┘
                                        │
                                        ▼
                      ┌──────────────────────────────────┐
                      │   Meterless World Model Engine   │
                      │  (Multi-Branch Risk Simulations) │
                      └─────────────────┬────────────────┘
                                        │
                                        ▼
                      ┌──────────────────────────────────┐
                      │         NVIDIA NIM LLM           │
                      │     (Llama 3.1 70B Reasoning)    │
                      └─────────────────┬────────────────┘
                                        │
                                        ▼
                      ┌──────────────────────────────────┐
                      │    Autonomous Action Dispatch    │
                      │ (Rerouting, POs, Ops Dashboard)  │
                      └──────────────────────────────────┘
```

---

## 3. Sponsor Technology Implementation

### A. Meterless Agent Engine (`World Model`)
* **Engine Type:** `World Model`
* **Implementation Location:** [`src/engines/world_model.py`](src/engines/world_model.py)
* **How It Works:** Rather than relying on simple prompt-based heuristics, the agent maintains an explicit `WorldState` (inventory, carrier delays, port congestion indices). Upon receiving disruption signals, it rolls out $N$-step counterfactual branches across candidate interventions (Status Quo vs. Port Reroute vs. Air Freight), calculating predicted stockout days and calibrated confidence intervals.

### B. Zetaris Cloud Gateway
* **Implementation Location:** [`src/connectors/zetaris_connector.py`](src/connectors/zetaris_connector.py)
* **How It Works:** Acts as the virtualized semantic layer, executing federated queries across disparate supplier databases and logistics logs without requiring physical data ETL pipelines.

### C. NVIDIA NIM
* **Implementation Location:** [`src/connectors/nvidia_nim.py`](src/connectors/nvidia_nim.py)
* **Model:** `meta/llama-3.1-70b-instruct`
* **How It Works:** Evaluates the simulated trade-off matrix produced by the World Model, factoring in financial risk vs. SLA compliance to produce verifiable executive action orders.

---

## 4. Quickstart & Reproducibility

### Local Setup
```bash
# Clone the repository
git clone https://github.com/Indus-Team/indus-flow.git
cd indus-flow

# Configure environment variables
cp .env.example .env

# Run automated test suite (verifying Meterless World Model engine)
python3 -m pytest -v tests/
```

### Docker Deployment
```bash
docker-compose up --build
```
The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

---

## 5. Automated Testing Verification
The test suite in [`tests/test_meterless_engine.py`](tests/test_meterless_engine.py) verifies:
1. `test_meterless_world_model_step_evolution`: Deterministic environment rollout under perturbations.
2. `test_meterless_world_model_counterfactual_simulation`: Multi-branch simulation ranking and confidence bounds.
3. `test_full_agent_resilience_cycle`: End-to-end orchestration (Zetaris $\to$ Meterless $\to$ NVIDIA NIM).

```
============================== test session starts ==============================
tests/test_meterless_engine.py::test_meterless_world_model_step_evolution PASSED [ 33%]
tests/test_meterless_engine.py::test_meterless_world_model_counterfactual_simulation PASSED [ 66%]
tests/test_meterless_engine.py::test_full_agent_resilience_cycle PASSED  [100%]
============================== 3 passed in 0.20s ===============================
```

---

## 6. Team Indus
* **Adarsh Singh** — Team Leader
* **Asiya Ali** — PM, DevOps, UI/UX, ML/AI Engineer
* **Gourav Sahu** — Data Scientist, ML/AI Engineer
* **Raj Singh** — Full-Stack Engineer

# Mentor Check-In & Office Hours Brief
**Team Indus — Open Agent Hackathon 2026**

---

## 1. Session Objective
To validate our system architecture, clarify Meterless Engine integration depth, and confirm track alignment with official hackathon judges/mentors.

---

## 2. Team & Project Snapshot
* **Team:** Indus (Adarsh Singh, Asiya Ali, Gourav Sahu, Raj Singh)
* **Chosen Track:** Enterprise Operations & Resilience / Autonomous Workflow Agents
* **Project Name:** **Indus Flow** (Autonomous Supply Chain & Disruption Resilience Agent)
* **Target Users:** Supply chain directors, procurement leads, and logistics operations managers.

---

## 3. Architecture Summary
```
[External Data Feeds / ERPs / Supplier APIs]
                    │
                    ▼
       [Zetaris Semantic Data Layer] (Unified SQL federated queries)
                    │
                    ▼
     [Meterless World Model Engine] (Counterfactual simulation & risk forecasting)
                    │
                    ▼
  [NVIDIA NIM Reasoning Agent (Llama 3.1 70B)] (Trade-off optimization & action policy)
                    │
                    ▼
[Action Dispatcher: Rerouting, Purchase Orders, Risk Digest]
```

---

## 4. Key Questions for Mentor Office Hours
1. **Meterless Engine Evaluation:** For the required Meterless integration test, does the judge harness prefer an automated unit test suite (`pytest`) demonstrating state divergence across simulations, or a telemetry trace log during the live demo?
2. **Zetaris Query Breadth:** We are combining two REST data sources and one Parquet dataset through Zetaris Cloud Gateway. Does the judging committee reward higher source diversity or deeper join complexity?
3. **Demo Video Focus:** In the 3-minute demo video, what is the recommended time allocation between the problem/business impact (slide deck) vs. technical walkthrough (Meterless engine logs & live execution)?

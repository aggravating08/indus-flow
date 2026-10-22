# Indus Flow — 2-to-3 Minute Demo Video Script
**Open Agent Hackathon 2026** | **Team Indus**

---

## Video Specifications
* **Duration:** 2 Minutes 45 Seconds (Target: < 3:00)
* **Presenters:** Adarsh Singh (Narrator / Intro & Pitch) & Asiya Ali (Technical Walkthrough)
* **Screen Display:** Browser tab open at `http://localhost:8000/` alongside terminal or code view.

---

## Minute-by-Minute Breakdown

### 0:00 – 0:35 | The Enterprise Crisis (Adarsh Singh)
* **Visual:** Slide showing supply chain disruption headline + transition to Indus Flow Dashboard.
* **Spoken Audio:**
  > "Every year, manufacturing supply chains lose billions to unexpected logistics shocks—from port bottlenecks and customs holds to supplier outages. Today, operations teams operate on passive dashboards. By the time an alert reaches an operator, the factory is already 48 hours away from halting assembly lines.
  > 
  > We built **Indus Flow**—an autonomous resilience agent that doesn't just display alerts, but simulates future counterfactuals and formulates optimal mitigation decisions."

---

### 0:35 – 1:15 | Sponsor Integrations in Action (Asiya Ali)
* **Visual:** Point to top header badges showing **Meterless**, **NVIDIA NIM**, and **Zetaris**.
* **Spoken Audio:**
  > "Indus Flow unifies three cutting-edge sponsor technologies:
  > 
  > 1. **Zetaris Unified Semantic Catalog:** At the data layer, Zetaris federates live ERP inventory records, shipment telemetry, and supplier directories into a single virtual schema without requiring slow ETL jobs.
  > 2. **Meterless World Model Engine:** Unlike simple reactive agents, Indus Flow uses the Meterless World Model to model multi-step physical state rollouts across candidate actions—projecting stockout days and risk curves.
  > 3. **NVIDIA NIM:** We leverage Llama-3.1-70B running on NVIDIA NIM to perform multi-criteria trade-off arbitration between freight expenses, SLA breach penalties, and supplier relationships."

---

### 1:15 – 2:05 | Live Demo Walkthrough (Asiya Ali)
* **Visual:** Click **"Run Autonomous Cycle"** on the dashboard.
* **Spoken Audio:**
  > "Let's watch Indus Flow in action. Right now, our inventory shows a critical buffer deficit on automotive microcontrollers (`SKU-9921-MCU`) because ocean shipment `TRK-US-9821` is stuck in a 7-day customs hold at Long Beach.
  > 
  > When I click 'Run Autonomous Cycle', the agent:
  > - Ingests the telemetry via Zetaris.
  > - Spawns four simulation branches in the Meterless World Model: Status Quo, Port Diversion, Emergency Air Freight, and Secondary Supplier PO.
  > - As we can see on the simulation workbench, Status Quo leads to 1 stockout day and extreme downtime risk ($32,500 penalty). The World Model determines that an Emergency Air Freight buffer reduces stockout days to zero with a minimal 0.02 risk score.
  > - NVIDIA NIM evaluates the trade-off and formulates the executive action order."

---

### 2:05 – 2:35 | Governance & Human-in-the-Loop Approval (Asiya Ali / Adarsh Singh)
* **Visual:** Show the decision card in **PENDING_APPROVAL** state. Click **"✓ Approve Action"** and type operational notes.
* **Spoken Audio:**
  > "Because this air freight contingency costs $2,550—exceeding our pre-approved $1,000 threshold—Indus Flow does NOT execute blindly. It gates the decision in `PENDING_APPROVAL`.
  > 
  > As the operations lead, I review the reasoning trace, click 'Approve Action', and submit my confirmation. The action executes immediately, restoring our safe buffer level and appending an immutable audit record."

---

### 2:35 – 2:50 | Summary & Submission Wrap-Up (Adarsh Singh)
* **Visual:** Switch to Architecture slide and GitHub repo.
* **Spoken Audio:**
  > "Indus Flow is fully dockerized, backed by a 33-test automated suite verifying the Meterless engine and agent workflows, and ready for deployment.
  > 
  > Thank you to GenAI.Works, Meterless, NVIDIA, and Zetaris for powering Team Indus!"

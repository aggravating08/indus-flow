/* ============================================================
   Indus Flow — Dashboard App Logic
   Open Agent Hackathon 2026 | Team Indus
   ============================================================ */

const API = '/api/v1';
let pendingModalDecisionId = null;
let pendingModalMode = null; // 'approve' | 'reject'
let lastSimResult = null;

// ─── Utility ─────────────────────────────────────────────────

async function apiFetch(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${txt}`);
  }
  return res.json();
}

function showLoading(msg = 'Processing…') {
  document.getElementById('loading-overlay').classList.remove('hidden');
  document.getElementById('loading-label').textContent = msg;
}
function hideLoading() {
  document.getElementById('loading-overlay').classList.add('hidden');
}

function showError(containerId, msg) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `<div class="error-banner">⚠️ ${msg}</div>`;
}

function severityBadge(sev) {
  const cls = { CRITICAL: 'badge-danger', HIGH: 'badge-warning', MEDIUM: 'badge-info', LOW: 'badge-muted' };
  return `<span class="badge ${cls[sev] || 'badge-muted'}">${sev}</span>`;
}

function statusBadge(status) {
  const map = {
    ON_SCHEDULE: 'badge-success', IN_TRANSIT: 'badge-info',
    CUSTOMS_HOLD: 'badge-danger', PORT_BOTTLENECK: 'badge-warning',
    WEATHER_DELAY: 'badge-warning', DELIVERED: 'badge-muted',
    NO_TRANSIT: 'badge-muted'
  };
  return `<span class="badge ${map[status] || 'badge-muted'}">${status.replace(/_/g,' ')}</span>`;
}

function approvalBadge(status) {
  const map = {
    PENDING_APPROVAL: 'badge-pending', APPROVED: 'badge-success',
    REJECTED: 'badge-danger', AUTO_EXECUTED: 'badge-info'
  };
  return `<span class="badge ${map[status] || 'badge-muted'}">${status.replace(/_/g,' ')}</span>`;
}

function riskClass(score) {
  if (score < 0.35) return 'risk-low';
  if (score < 0.65) return 'risk-medium';
  return 'risk-high';
}

function stockClass(current, safety) {
  if (current <= 0) return 'stock-crit';
  if (current <= safety) return 'stock-warn';
  return 'stock-ok';
}

function fmt(n) { return typeof n === 'number' ? n.toLocaleString() : n; }
function fmtUsd(n) { return `$${(+n).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}` }
function fmtPct(n) { return `${(+n * 100).toFixed(1)}%`; }

// ─── Header Integration Badges ───────────────────────────────

function updateIntegrationBadges(integrations) {
  if (!integrations) return;
  const m = integrations.meterless || {};
  const n = integrations.nvidia_nim || {};
  const z = integrations.zetaris || {};

  const mEl = document.getElementById('meterless-mode');
  const nEl = document.getElementById('nvidia-mode');
  const zEl = document.getElementById('zetaris-mode');
  const mBadge = document.getElementById('badge-meterless');
  const nBadge = document.getElementById('badge-nvidia');
  const zBadge = document.getElementById('badge-zetaris');

  if (mEl) mEl.textContent = m.is_live ? 'Live API' : 'Local Engine';
  if (nEl) nEl.textContent = n.is_live ? 'Live NIM' : 'Mock Adapter';
  if (zEl) zEl.textContent = z.is_live ? 'Live Gateway' : 'Mock Catalog';

  [mBadge, nBadge, zBadge].forEach((b, i) => {
    const isLive = [m.is_live, n.is_live, z.is_live][i];
    b.classList.toggle('live-mode', !!isLive);
    b.classList.toggle('mock-mode', !isLive);
    b.querySelector('.dot').classList.toggle('warning', !isLive);
  });
}

// ─── KPI Cards ───────────────────────────────────────────────

function updateKPIs(overview) {
  const m = overview.metrics || {};
  document.getElementById('kpi-skus').textContent = fmt(m.total_skus_tracked ?? '—');
  document.getElementById('kpi-critical').textContent = fmt(m.critical_stock_count ?? '—');
  document.getElementById('kpi-critical-sub').textContent =
    m.critical_stock_count > 0 ? 'Buffer breach imminent' : 'All within safe thresholds';
  document.getElementById('kpi-shipments').textContent = fmt(m.total_shipments ?? '—');
  document.getElementById('kpi-shipments-sub').textContent =
    m.delayed_shipments_count > 0 ? `${m.delayed_shipments_count} delayed at port` : 'All on schedule';
  document.getElementById('kpi-approvals').textContent = fmt(m.pending_approvals_count ?? '—');
  updateIntegrationBadges(overview.integrations);
}

// ─── Alerts Panel ────────────────────────────────────────────

function renderAlerts(alerts) {
  const list = document.getElementById('alerts-list');
  const badge = document.getElementById('alerts-count-badge');
  badge.textContent = `${alerts.length} Alert${alerts.length !== 1 ? 's' : ''}`;

  if (!alerts.length) {
    list.innerHTML = '<div class="empty-state">✅ No active disruptions detected.</div>';
    return;
  }
  list.innerHTML = alerts.map(a => `
    <div class="alert-card-item sev-${a.severity}">
      <div>
        <span class="alert-sev-badge sev-badge-${a.severity}">${a.severity}</span>
      </div>
      <div class="alert-meta">
        <div class="alert-summary">${a.summary}</div>
        <div class="alert-cause">${a.underlying_cause || ''}</div>
        <div class="risk-bar-wrap ${riskClass(a.projected_stockout_risk)} alert-risk-bar">
          <div class="risk-bar"><div class="risk-bar-fill" style="width:${(a.projected_stockout_risk*100).toFixed(0)}%"></div></div>
          <span class="risk-label">${fmtPct(a.projected_stockout_risk)} risk</span>
        </div>
      </div>
      <div class="text-muted text-sm mono">${a.sku_id}</div>
    </div>
  `).join('');
}

// ─── Decisions Panel ─────────────────────────────────────────

function renderDecisions(decisions) {
  const container = document.getElementById('decision-content');
  const badge = document.getElementById('decision-status-badge');

  if (!decisions.length) {
    container.innerHTML = '<div class="empty-state">No decisions generated yet. Run the autonomous cycle.</div>';
    badge.textContent = 'No Decisions';
    badge.className = 'badge badge-muted';
    return;
  }

  const pending = decisions.filter(d => d.status === 'PENDING_APPROVAL').length;
  badge.textContent = pending > 0 ? `${pending} Pending Approval` : `${decisions.length} Decisions`;
  badge.className = `badge ${pending > 0 ? 'badge-pending' : 'badge-success'}`;

  container.innerHTML = decisions.map(d => {
    const c = d.selected_candidate || {};
    const nim = d.nvidia_nim_reasoning || 'Reasoning unavailable.';
    const showApprove = d.status === 'PENDING_APPROVAL';

    return `
      <div class="decision-card">
        <div class="decision-card-header">
          <div>
            <div class="decision-title">${c.title || 'Mitigation Action'}</div>
            <div class="decision-sku">${d.sku_id} &bull; ${fmtUsd(c.cost_usd || 0)}</div>
          </div>
          ${approvalBadge(d.status)}
        </div>
        <div class="nim-reasoning-box">${nim}</div>
        <div class="risk-bar-wrap ${riskClass(1 - (c.risk_reduction_pct || 0) / 100)}">
          <span class="text-sub text-sm">Risk Reduction:</span>
          <div class="risk-bar"><div class="risk-bar-fill" style="width:${c.risk_reduction_pct || 0}%"></div></div>
          <span class="risk-label">${c.risk_reduction_pct || 0}%</span>
        </div>
        ${showApprove ? `
          <div class="decision-actions">
            <button class="btn btn-sm btn-danger" onclick="openModal('${d.decision_id}', 'reject')">✕ Reject</button>
            <button class="btn btn-sm btn-primary" onclick="openModal('${d.decision_id}', 'approve')">✓ Approve Action</button>
          </div>
        ` : ''}
      </div>
    `;
  }).join('');
}

// ─── Simulation Panel ─────────────────────────────────────────

function renderSimulations(outcomes) {
  const container = document.getElementById('simulation-content');
  if (!outcomes || !outcomes.length) {
    container.innerHTML = '<div class="empty-state">No simulation results yet.</div>';
    return;
  }
  container.innerHTML = `
    <div class="text-sub text-sm" style="margin-bottom:12px">
      Meterless World Model evaluated ${outcomes.length} counterfactual branches.
      Ranked by projected risk score (lowest = optimal).
    </div>
    <div class="sim-grid">
      ${outcomes.map((o, i) => {
        const rank = i + 1;
        const rankCls = rank <= 3 ? `rank-${rank}` : 'rank-other';
        const rankLabel = rank === 1 ? '★ Optimal' : rank === 2 ? '▲ Viable' : rank === 3 ? '▼ Risky' : `#${rank}`;
        return `
          <div class="sim-card ${rankCls}">
            <span class="sim-rank-badge">${rankLabel}</span>
            <div class="sim-name">${o.scenario_name}</div>
            <div class="sim-metrics">
              <div class="sim-metric">
                <div class="sim-metric-label">Risk Score</div>
                <div class="sim-metric-value ${o.projected_risk_score < 0.35 ? 'text-accent' : o.projected_risk_score < 0.65 ? 'text-warning' : 'text-danger'}">${fmtPct(o.projected_risk_score)}</div>
              </div>
              <div class="sim-metric">
                <div class="sim-metric-label">Stockout Days</div>
                <div class="sim-metric-value ${o.predicted_stockout_days === 0 ? 'text-accent' : 'text-danger'}">${o.predicted_stockout_days}d</div>
              </div>
              <div class="sim-metric">
                <div class="sim-metric-label">Cost</div>
                <div class="sim-metric-value">${fmtUsd(o.estimated_mitigation_cost)}</div>
              </div>
            </div>
            <div class="risk-bar-wrap ${riskClass(o.projected_risk_score)}" style="margin-top:10px">
              <div class="risk-bar"><div class="risk-bar-fill" style="width:${(o.projected_risk_score*100).toFixed(0)}%"></div></div>
              <span class="risk-label">${(o.projected_risk_score*100).toFixed(0)}%</span>
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

// ─── Data Tables ──────────────────────────────────────────────

function renderInventory(items) {
  const tbody = document.querySelector('#inventory-table tbody');
  if (!items.length) { tbody.innerHTML = '<tr><td colspan="8" class="empty-state">No inventory data.</td></tr>'; return; }
  const safetyMax = Math.max(...items.map(i => i.safety_stock || 1));
  tbody.innerHTML = items.map(i => {
    const dos = typeof i.days_of_supply === 'number' ? i.days_of_supply.toFixed(1) : '—';
    const ratio = Math.min(1, (i.current_stock || 0) / Math.max(1, (i.safety_stock || 1) * 2));
    const sc = stockClass(i.current_stock, i.safety_stock);
    const sevMap = { CRITICAL: 'badge-danger', HIGH: 'badge-warning', MEDIUM: 'badge-info', LOW: 'badge-muted' };
    return `
      <tr>
        <td class="mono">${i.sku_id}</td>
        <td>${i.name}</td>
        <td class="text-sub">${i.category}</td>
        <td>
          <div class="stock-bar-wrap ${sc}">
            <div class="stock-bar"><div class="stock-bar-fill" style="width:${(ratio*100).toFixed(0)}%"></div></div>
            <span class="mono">${fmt(i.current_stock)}</span>
          </div>
        </td>
        <td class="mono text-sub">${fmt(i.safety_stock)}</td>
        <td class="mono text-sub">${fmt(i.daily_burn_rate)}/day</td>
        <td class="mono ${+dos < 7 ? 'text-danger' : +dos < 14 ? 'text-warning' : 'text-accent'}">${dos}d</td>
        <td><span class="badge ${sevMap[i.criticality] || 'badge-muted'}">${i.criticality}</span></td>
      </tr>`;
  }).join('');
}

function renderShipments(shipments) {
  const tbody = document.querySelector('#shipments-table tbody');
  if (!shipments.length) { tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No shipments.</td></tr>'; return; }
  tbody.innerHTML = shipments.map(s => `
    <tr>
      <td class="mono">${s.tracking_id}</td>
      <td class="mono text-accent">${s.sku_id}</td>
      <td>${s.carrier_name}</td>
      <td class="text-sub" style="font-size:11px">${s.origin_port} → ${s.destination_port}</td>
      <td class="mono">${fmt(s.units)}</td>
      <td class="mono ${s.reported_delay_days > 0 ? 'text-danger' : 'text-accent'}">${s.reported_delay_days > 0 ? `+${s.reported_delay_days}d` : '—'}</td>
      <td>${statusBadge(s.status)}</td>
    </tr>`).join('');
}

function renderSuppliers(suppliers) {
  const tbody = document.querySelector('#suppliers-table tbody');
  if (!suppliers.length) { tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No suppliers.</td></tr>'; return; }
  tbody.innerHTML = suppliers.map(s => `
    <tr>
      <td class="mono">${s.id}</td>
      <td><strong>${s.name}</strong></td>
      <td>${s.country}</td>
      <td class="text-sub">Tier ${s.tier}</td>
      <td>
        <div class="rel-bar-wrap">
          <div class="rel-bar"><div class="rel-bar-fill" style="width:${(s.reliability_score*100).toFixed(0)}%"></div></div>
          <span class="rel-score">${(s.reliability_score*100).toFixed(0)}%</span>
        </div>
      </td>
      <td class="mono text-sub">${s.lead_time_days}d</td>
      <td>${s.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-danger">Offline</span>'}</td>
    </tr>`).join('');
}

function renderHistory(log) {
  const feed = document.getElementById('history-feed');
  if (!log.length) { feed.innerHTML = '<div class="empty-state">No audit events yet.</div>'; return; }
  feed.innerHTML = [...log].reverse().map(e => {
    const t = e.timestamp ? new Date(e.timestamp + 'Z').toLocaleString() : '—';
    const details = Object.entries(e.details || {}).map(([k,v]) => `${k}: ${v}`).join(' | ');
    return `
      <div class="history-item">
        <div class="history-time">${t}</div>
        <div>
          <div class="history-action">${e.action}</div>
          <div class="history-actor">by ${e.actor}</div>
          <div class="history-detail">${details}</div>
        </div>
      </div>`;
  }).join('');
}

// ─── Main Data Refresh ────────────────────────────────────────

async function refreshAllData() {
  try {
    const [overview, inventory, shipments, suppliers, alerts, decisions, auditLog] = await Promise.all([
      apiFetch('/overview'),
      apiFetch('/inventory'),
      apiFetch('/shipments'),
      apiFetch('/suppliers'),
      apiFetch('/alerts'),
      apiFetch('/decisions'),
      apiFetch('/audit-log?limit=60')
    ]);

    updateKPIs(overview);
    renderAlerts(alerts);
    renderDecisions(decisions);
    renderInventory(inventory);
    renderShipments(shipments);
    renderSuppliers(suppliers);
    renderHistory(auditLog);
    document.getElementById('table-timestamp').textContent = 'Updated ' + new Date().toLocaleTimeString();
  } catch (err) {
    console.error('Refresh error:', err);
  }
}

// ─── Run Agent Cycle ──────────────────────────────────────────

async function runAgentCycle() {
  const btn = document.getElementById('btn-run-agent');
  btn.disabled = true;
  showLoading('Running Autonomous Resilience Cycle…');
  try {
    const result = await apiFetch('/agent/run', { method: 'POST' });

    // Extract simulation outcomes from decisions
    const decisions = result.decisions_generated || [];
    if (decisions.length > 0) {
      const simData = decisions[0]?.meterless_simulation_ref?.all_scenarios;
      if (simData) renderSimulations(simData);
    }

    await refreshAllData();
  } catch (err) {
    showError('decision-content', 'Agent cycle failed: ' + err.message);
  } finally {
    hideLoading();
    btn.disabled = false;
  }
}

// ─── Re-Simulate ──────────────────────────────────────────────

async function reSimulate() {
  const horizon = parseInt(document.getElementById('sim-horizon').value, 10);
  showLoading('Running Meterless World Model Simulations…');
  try {
    const result = await apiFetch('/simulation/simulate', {
      method: 'POST',
      body: JSON.stringify({ sku_id: 'SKU-9921-MCU', initial_stock: 140, daily_demand: 25, port_congestion: 0.70, horizon_steps: horizon })
    });
    renderSimulations(result.outcomes || []);
  } catch (err) {
    showError('simulation-content', 'Simulation error: ' + err.message);
  } finally {
    hideLoading();
  }
}

// ─── Human Approval Modal ─────────────────────────────────────

function openModal(decisionId, mode) {
  pendingModalDecisionId = decisionId;
  pendingModalMode = mode;
  const modal = document.getElementById('approval-modal');
  const title = document.getElementById('modal-title');
  const desc = document.getElementById('modal-description');
  const confirmBtn = document.getElementById('modal-btn-confirm');
  const notesEl = document.getElementById('operator-notes');

  if (mode === 'approve') {
    title.textContent = 'Approve Mitigation Action';
    desc.textContent = 'You are approving this action for immediate operational execution. This is a consequential decision — a purchase order, shipment reroute, or air freight contract may be issued.';
    confirmBtn.textContent = '✓ Confirm & Approve';
    confirmBtn.className = 'btn btn-primary';
    notesEl.placeholder = 'Approval justification (e.g. "Expedite approved: SLA risk outweighs air freight cost")';
  } else {
    title.textContent = 'Reject Mitigation Action';
    desc.textContent = 'Provide a reason for rejection. The decision will be logged to audit trail. No action will be executed.';
    confirmBtn.textContent = '✕ Confirm Rejection';
    confirmBtn.className = 'btn btn-danger';
    notesEl.placeholder = 'Rejection reason (e.g. "Cost threshold exceeded; explore rail intermodal alternative")';
  }

  modal.classList.add('open');
}

function closeModal() {
  document.getElementById('approval-modal').classList.remove('open');
  pendingModalDecisionId = null;
  pendingModalMode = null;
}

async function confirmModal() {
  if (!pendingModalDecisionId || !pendingModalMode) return;
  const operator = document.getElementById('operator-name').value.trim() || 'Operator';
  const notes = document.getElementById('operator-notes').value.trim();

  showLoading(pendingModalMode === 'approve' ? 'Approving action…' : 'Rejecting action…');
  try {
    const path = `/decisions/${pendingModalDecisionId}/${pendingModalMode}`;
    const body = pendingModalMode === 'approve'
      ? { approver: operator, notes: notes || 'Approved for execution' }
      : { rejecter: operator, reason: notes || 'Rejected by operator' };

    await apiFetch(path, { method: 'POST', body: JSON.stringify(body) });
    closeModal();
    await refreshAllData();
  } catch (err) {
    closeModal();
    alert('Action failed: ' + err.message);
  } finally {
    hideLoading();
  }
}

// ─── Tab Navigation ───────────────────────────────────────────

function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.dataset.tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(tabId)?.classList.add('active');
      if (tabId === 'tab-history') {
        apiFetch('/audit-log?limit=60').then(renderHistory).catch(console.error);
      }
    });
  });
}

// ─── Reset ────────────────────────────────────────────────────

async function resetSystem() {
  if (!confirm('Reset all supply chain state to initial seed data?')) return;
  showLoading('Resetting system state…');
  try {
    await apiFetch('/reset', { method: 'POST' });
    document.getElementById('simulation-content').innerHTML = '<div class="empty-state">Reset complete. Run the cycle to start fresh.</div>';
    await refreshAllData();
  } catch (err) {
    alert('Reset failed: ' + err.message);
  } finally {
    hideLoading();
  }
}

// ─── Bootstrap ───────────────────────────────────────────────

function injectLoadingOverlay() {
  const div = document.createElement('div');
  div.id = 'loading-overlay';
  div.className = 'loading-overlay hidden';
  div.innerHTML = `
    <div style="display:flex;flex-direction:column;align-items:center;gap:16px">
      <div class="spinner"></div>
      <div class="loading-label" id="loading-label">Loading…</div>
    </div>`;
  document.body.appendChild(div);
}

document.addEventListener('DOMContentLoaded', () => {
  injectLoadingOverlay();
  initTabs();

  document.getElementById('btn-run-agent').addEventListener('click', runAgentCycle);
  document.getElementById('btn-reset').addEventListener('click', resetSystem);
  document.getElementById('btn-re-simulate').addEventListener('click', reSimulate);
  document.getElementById('modal-close').addEventListener('click', closeModal);
  document.getElementById('modal-btn-cancel').addEventListener('click', closeModal);
  document.getElementById('modal-btn-confirm').addEventListener('click', confirmModal);
  document.getElementById('approval-modal').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeModal();
  });

  // Initial data load
  refreshAllData();

  // Auto-refresh overview every 30s
  setInterval(refreshAllData, 30000);
});

/**
 * Auyvra Lead Research Dashboard - Client Controller
 */

let allLeads = [];
let currentLead = null;
let parsedCandidate = null;
let industryChartInstance = null;
let countryChartInstance = null;
let scoreChartInstance = null;
let searchDebounceTimer = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    initEventListeners();
    loadDashboardStats();
    loadLeads();
});

function initEventListeners() {
    // Filter change listeners
    document.getElementById('filter-search').addEventListener('input', (e) => {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            loadLeads();
        }, 300);
    });

    ['filter-status', 'filter-industry', 'filter-country', 'filter-service', 'filter-min-score'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', () => loadLeads());
    });

    // Close modals on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay').forEach(modal => {
                modal.classList.add('hidden');
            });
        }
    });
}

// ==========================================
// API Operations: Stats & Charts
// ==========================================
async function loadDashboardStats() {
    try {
        const res = await fetch('/api/stats');
        if (!res.ok) throw new Error('Failed to fetch dashboard metrics');
        const stats = await res.json();

        // Update KPI cards
        document.getElementById('kpi-total-leads').textContent = stats.total_leads;
        document.getElementById('kpi-qualified-leads').textContent = stats.qualified_leads;
        document.getElementById('kpi-review-leads').textContent = stats.awaiting_review;
        document.getElementById('kpi-avg-score').textContent = stats.average_score.toFixed(1);

        // Update Daily Target Tracker
        if (stats.daily_target) {
            document.getElementById('target-date-display').textContent = `Target Date: ${stats.daily_target.date_str} (Asia/Kolkata)`;
            document.getElementById('target-reviewed-txt').textContent = `${stats.daily_target.reviewed_count} / ${stats.daily_target.reviewed_target}`;
            document.getElementById('target-reviewed-bar').style.width = `${stats.daily_target.reviewed_progress_pct}%`;

            document.getElementById('target-qualified-txt').textContent = `${stats.daily_target.qualified_count} / ${stats.daily_target.qualified_target}`;
            document.getElementById('target-qualified-bar').style.width = `${stats.daily_target.qualified_progress_pct}%`;
        }

        // Update Header Statuses
        const sheetsNav = document.getElementById('nav-sheets-status');
        if (sheetsNav) {
            sheetsNav.textContent = `Google Sheets: ${stats.sheets_status}`;
        }
        const sheetsModalStatus = document.getElementById('sheets-modal-status');
        if (sheetsModalStatus) {
            sheetsModalStatus.textContent = `Status: ${stats.sheets_status}`;
        }

        renderCharts(stats);
    } catch (err) {
        console.error('Error loading stats:', err);
        showToast('Error loading stats: ' + err.message, 'error');
    }
}

function renderCharts(stats) {
    const chartDefaults = {
        color: '#94A3B8',
        font: { size: 10 }
    };

    // 1. Industry / Verticals Chart
    const indCtx = document.getElementById('industryChart')?.getContext('2d');
    if (indCtx) {
        if (industryChartInstance) industryChartInstance.destroy();
        const labels = Object.keys(stats.industry_breakdown || {});
        const data = Object.values(stats.industry_breakdown || {});
        
        industryChartInstance = new Chart(indCtx, {
            type: 'bar',
            data: {
                labels: labels.length ? labels.map(l => l.replace(' / ', '/').substring(0, 14)) : ['No Data'],
                datasets: [{
                    data: data.length ? data : [0],
                    backgroundColor: 'rgba(56, 189, 248, 0.7)',
                    borderColor: '#38BDF8',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: chartDefaults, grid: { color: 'rgba(30, 41, 59, 0.3)' } },
                    y: { ticks: { ...chartDefaults, stepSize: 1 }, grid: { color: 'rgba(30, 41, 59, 0.3)' } }
                }
            }
        });
    }

    // 2. Country Breakdown Chart
    const cntryCtx = document.getElementById('countryChart')?.getContext('2d');
    if (cntryCtx) {
        if (countryChartInstance) countryChartInstance.destroy();
        const labels = Object.keys(stats.country_breakdown || {});
        const data = Object.values(stats.country_breakdown || {});

        countryChartInstance = new Chart(cntryCtx, {
            type: 'doughnut',
            data: {
                labels: labels.length ? labels : ['No Data'],
                datasets: [{
                    data: data.length ? data : [1],
                    backgroundColor: [
                        '#38BDF8', '#2DD4BF', '#6366F1', '#10B981', '#F59E0B', '#EC4899', '#64748B'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#94A3B8', boxWidth: 10, font: { size: 10 } }
                    }
                }
            }
        });
    }

    // 3. Score Distribution Chart
    const scoreCtx = document.getElementById('scoreChart')?.getContext('2d');
    if (scoreCtx) {
        if (scoreChartInstance) scoreChartInstance.destroy();
        const dist = stats.score_distribution || { "High (>74)": 0, "Medium (50-74)": 0, "Low (<50)": 0 };

        scoreChartInstance = new Chart(scoreCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(dist),
                datasets: [{
                    data: Object.values(dist),
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)', // Green for High
                        'rgba(245, 158, 11, 0.8)', // Amber for Medium
                        'rgba(239, 68, 68, 0.8)'   // Red for Low
                    ],
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: chartDefaults, grid: { display: false } },
                    y: { ticks: { ...chartDefaults, stepSize: 1 }, grid: { color: 'rgba(30, 41, 59, 0.3)' } }
                }
            }
        });
    }
}

// ==========================================
// API Operations: Leads Table
// ==========================================
async function loadLeads() {
    const search = document.getElementById('filter-search')?.value.trim();
    const status = document.getElementById('filter-status')?.value;
    const industry = document.getElementById('filter-industry')?.value;
    const country = document.getElementById('filter-country')?.value;
    const service = document.getElementById('filter-service')?.value;
    const minScore = document.getElementById('filter-min-score')?.value;

    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (status && status !== 'All') params.append('status', status);
    if (industry && industry !== 'All') params.append('industry', industry);
    if (country && country !== 'All') params.append('country', country);
    if (service && service !== 'All') params.append('service', service);
    if (minScore && minScore !== '0') params.append('min_score', minScore);

    const tbody = document.getElementById('leads-table-body');
    tbody.innerHTML = `
        <tr>
            <td colspan="7" class="text-center py-8 text-slate-400">
                <i data-lucide="loader-2" class="w-5 h-5 animate-spin mx-auto mb-1 text-blue-400"></i>
                Filtering leads...
            </td>
        </tr>
    `;
    lucide.createIcons();

    try {
        const res = await fetch(`/api/leads?${params.toString()}`);
        if (!res.ok) throw new Error('Failed to query leads');
        allLeads = await res.json();

        document.getElementById('leads-count-badge').textContent = `${allLeads.length} records`;
        renderLeadsTable(allLeads);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-red-400">Error: ${err.message}</td></tr>`;
    }
}

function renderLeadsTable(leads) {
    const tbody = document.getElementById('leads-table-body');
    tbody.innerHTML = '';

    if (!leads.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-12 text-slate-400">
                    <i data-lucide="inbox" class="w-8 h-8 mx-auto mb-2 text-slate-500"></i>
                    No leads found matching your criteria.
                </td>
            </tr>
        `;
        lucide.createIcons();
        return;
    }

    leads.forEach(lead => {
        const tr = document.createElement('tr');
        tr.className = 'cursor-pointer hover:bg-slate-800/40 transition';
        tr.onclick = (e) => {
            // Avoid triggering if clicked on direct link or button
            if (e.target.closest('a') || e.target.closest('button')) return;
            openLeadDetailModal(lead.id);
        };

        // Score badge class
        let scoreClass = 'score-pill-med';
        if (lead.score >= 70) scoreClass = 'score-pill-high';
        else if (lead.score < 50) scoreClass = 'score-pill-low';

        // Status badge class
        let statusBadgeClass = 'badge-review';
        if (lead.qualification_status === 'Qualified') statusBadgeClass = 'badge-qualified';
        else if (lead.qualification_status === 'Disqualified') statusBadgeClass = 'badge-disqualified';
        else if (lead.qualification_status === 'Contacted' || lead.qualification_status === 'Converted') statusBadgeClass = 'badge-contacted';

        const dateStr = lead.date_discovered ? new Date(lead.date_discovered).toLocaleDateString() : '';

        tr.innerHTML = `
            <td class="text-center">
                <span class="inline-block px-2.5 py-1 rounded-full text-xs font-bold font-mono ${scoreClass}">
                    ${lead.score}
                </span>
            </td>
            <td>
                <div class="font-semibold text-white max-w-sm truncate" title="${escapeHtml(lead.title)}">
                    ${escapeHtml(lead.title)}
                </div>
                <div class="text-xs text-slate-400 max-w-sm truncate mt-0.5" title="${escapeHtml(lead.stated_problem)}">
                    ${escapeHtml(lead.stated_problem)}
                </div>
            </td>
            <td>
                <div class="text-xs text-slate-200 font-medium">${escapeHtml(lead.industry)}</div>
                <div class="text-[11px] text-slate-400 flex items-center space-x-1 mt-0.5">
                    <span>${escapeHtml(lead.country)}</span>
                    ${lead.country_confirmed ? '<span class="text-emerald-400 text-[10px]" title="Confirmed region">✓</span>' : '<span class="text-slate-500 text-[10px]" title="Inferred/Unknown">?</span>'}
                </div>
            </td>
            <td>
                <span class="text-xs text-cyan-400 font-medium">${escapeHtml(lead.matching_service)}</span>
            </td>
            <td>
                <span class="px-2 py-0.5 rounded text-[11px] font-semibold ${statusBadgeClass}">
                    ${escapeHtml(lead.qualification_status)}
                </span>
            </td>
            <td class="text-xs text-slate-400">
                ${dateStr}
            </td>
            <td class="text-right space-x-1">
                <button onclick="openLeadDetailModal(${lead.id})" class="p-1 rounded hover:bg-slate-700 text-slate-300" title="Inspect Lead">
                    <i data-lucide="eye" class="w-4 h-4"></i>
                </button>
                <a href="${lead.url}" target="_blank" rel="noopener noreferrer" class="p-1 inline-block rounded hover:bg-slate-700 text-blue-400" title="Open Discussion Link">
                    <i data-lucide="external-link" class="w-4 h-4"></i>
                </a>
            </td>
        `;
        tbody.appendChild(tr);
    });

    lucide.createIcons();
}

// ==========================================
// Lead Detail & Inspector Modal
// ==========================================
async function openLeadDetailModal(leadId) {
    try {
        const res = await fetch(`/api/leads/${leadId}`);
        if (!res.ok) throw new Error('Could not fetch lead details');
        currentLead = await res.json();

        // Populate fields
        document.getElementById('modal-lead-title').textContent = currentLead.title;
        document.getElementById('modal-lead-url-txt').textContent = currentLead.url;
        document.getElementById('modal-lead-url').href = currentLead.url;
        document.getElementById('modal-lead-problem').textContent = currentLead.stated_problem;
        document.getElementById('modal-lead-industry').textContent = currentLead.industry;
        document.getElementById('modal-lead-country').textContent = currentLead.country;
        document.getElementById('modal-lead-country-badge').textContent = currentLead.country_confirmed ? 'Verified' : 'Inferred';
        document.getElementById('modal-lead-service').textContent = currentLead.matching_service;
        document.getElementById('modal-lead-source').textContent = currentLead.source || 'Manual Entry';

        // Badges
        const scoreBadge = document.getElementById('modal-lead-score-badge');
        scoreBadge.textContent = `${currentLead.score}/100`;
        scoreBadge.className = `px-2.5 py-0.5 rounded text-xs font-bold font-mono ${currentLead.score >= 70 ? 'score-pill-high' : currentLead.score < 50 ? 'score-pill-low' : 'score-pill-med'}`;

        const statusBadge = document.getElementById('modal-lead-status-badge');
        statusBadge.textContent = currentLead.qualification_status;
        statusBadge.className = `px-2 py-0.5 rounded text-xs font-semibold ${currentLead.qualification_status === 'Qualified' ? 'badge-qualified' : currentLead.qualification_status === 'Disqualified' ? 'badge-disqualified' : 'badge-review'}`;

        // Transparent Scoring Reasons
        document.getElementById('modal-lead-score-total').textContent = `Total: ${currentLead.score} / 100`;
        const reasonsContainer = document.getElementById('modal-lead-score-reasons');
        reasonsContainer.innerHTML = '';
        if (currentLead.score_breakdown) {
            try {
                const sb = typeof currentLead.score_breakdown === 'string' ? JSON.parse(currentLead.score_breakdown) : currentLead.score_breakdown;
                if (sb.reasons && sb.reasons.length) {
                    sb.reasons.forEach(r => {
                        const div = document.createElement('div');
                        div.className = 'flex items-start space-x-1.5';
                        div.innerHTML = `<span class="text-cyan-400 font-mono text-[10px]">•</span><span>${escapeHtml(r)}</span>`;
                        reasonsContainer.appendChild(div);
                    });
                }
            } catch (e) {
                reasonsContainer.textContent = currentLead.score_breakdown;
            }
        }

        // Editable inputs
        document.getElementById('modal-edit-status').value = currentLead.qualification_status;
        document.getElementById('modal-edit-score').value = currentLead.score;
        document.getElementById('modal-edit-notes').value = currentLead.notes || '';
        document.getElementById('modal-response-draft').value = currentLead.suggested_response || '';

        // Approval pill
        const approvedPill = document.getElementById('modal-response-approved-pill');
        if (currentLead.response_approved) {
            approvedPill.textContent = 'Approved for Outreach';
            approvedPill.className = 'text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800';
        } else {
            approvedPill.textContent = 'Needs Review';
            approvedPill.className = 'text-[10px] px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800';
        }

        openModal('leadDetailModal');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function saveLeadDetails() {
    if (!currentLead) return;

    const updatedStatus = document.getElementById('modal-edit-status').value;
    const updatedScore = parseInt(document.getElementById('modal-edit-score').value, 10);
    const updatedNotes = document.getElementById('modal-edit-notes').value;
    const updatedResponse = document.getElementById('modal-response-draft').value;

    try {
        const res = await fetch(`/api/leads/${currentLead.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                qualification_status: updatedStatus,
                score: isNaN(updatedScore) ? currentLead.score : updatedScore,
                notes: updatedNotes,
                suggested_response: updatedResponse
            })
        });

        if (!res.ok) throw new Error('Failed to update lead');
        showToast('Lead details updated successfully', 'success');
        closeModal('leadDetailModal');
        loadDashboardStats();
        loadLeads();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function deleteCurrentLead() {
    if (!currentLead) return;
    if (!confirm(`Are you sure you want to delete lead #${currentLead.id}?`)) return;

    try {
        const res = await fetch(`/api/leads/${currentLead.id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete lead');
        showToast(`Lead #${currentLead.id} deleted`, 'info');
        closeModal('leadDetailModal');
        loadDashboardStats();
        loadLeads();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function copyResponseDraft() {
    const draftText = document.getElementById('modal-response-draft').value;
    if (!draftText) return;

    navigator.clipboard.writeText(draftText).then(() => {
        showToast('Consultative reply draft copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy to clipboard', 'error');
    });
}

// ==========================================
// Add Lead Modal (Manual)
// ==========================================
function openAddLeadModal() {
    document.getElementById('addLeadForm').reset();
    openModal('addLeadModal');
}

async function submitAddLead(e) {
    e.preventDefault();
    const url = document.getElementById('add-url').value.trim();
    const title = document.getElementById('add-title').value.trim();
    const problem = document.getElementById('add-problem').value.trim();
    const industry = document.getElementById('add-industry').value;
    const country = document.getElementById('add-country').value;
    const author = document.getElementById('add-author').value.trim();
    const notes = document.getElementById('add-notes').value.trim();

    try {
        const res = await fetch('/api/leads', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url,
                title,
                stated_problem: problem,
                industry: industry === 'SMB / General' ? null : industry,
                country: country === 'Unknown' ? null : country,
                author: author || null,
                notes: notes || null
            })
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Failed to add lead');
        }

        showToast('Lead added and scored successfully!', 'success');
        closeModal('addLeadModal');
        loadDashboardStats();
        loadLeads();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==========================================
// Parse Freeform Notes Modal
// ==========================================
function openParseModal() {
    document.getElementById('parse-url').value = '';
    document.getElementById('parse-raw-text').value = '';
    document.getElementById('parse-results-box').classList.add('hidden');
    document.getElementById('parse-save-btn').classList.add('hidden');
    openModal('parseModal');
}

async function executeParseNotes() {
    const rawText = document.getElementById('parse-raw-text').value.trim();
    const url = document.getElementById('parse-url').value.trim();

    if (!rawText) {
        showToast('Please paste notes or post text to analyze', 'error');
        return;
    }

    const btn = document.getElementById('parse-analyze-btn');
    btn.textContent = 'Analyzing...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/leads/parse-notes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ raw_text: rawText, url: url || null })
        });

        if (!res.ok) throw new Error('Failed to parse notes');
        parsedCandidate = await res.json();
        parsedCandidate.url = url || `https://manual-research.local/entry/${Date.now()}`;

        // Display results preview
        document.getElementById('parse-res-title').textContent = parsedCandidate.title;
        document.getElementById('parse-res-score').textContent = `Score: ${parsedCandidate.score}/100`;
        document.getElementById('parse-res-score').className = `px-2 py-0.5 rounded text-[11px] font-bold ${parsedCandidate.score >= 70 ? 'score-pill-high' : 'score-pill-med'}`;
        document.getElementById('parse-res-service').textContent = parsedCandidate.matching_service;
        document.getElementById('parse-res-industry').textContent = parsedCandidate.industry;
        document.getElementById('parse-res-country').textContent = parsedCandidate.country;

        document.getElementById('parse-results-box').classList.remove('hidden');
        document.getElementById('parse-save-btn').classList.remove('hidden');
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        btn.textContent = 'Analyze Text';
        btn.disabled = false;
    }
}

async function saveParsedAsLead() {
    if (!parsedCandidate) return;

    try {
        const res = await fetch('/api/leads', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: parsedCandidate.url,
                title: parsedCandidate.title,
                stated_problem: parsedCandidate.stated_problem,
                industry: parsedCandidate.industry,
                country: parsedCandidate.country,
                matching_service: parsedCandidate.matching_service,
                score: parsedCandidate.score,
                qualification_status: parsedCandidate.recommended_status
            })
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Could not save parsed lead');
        }

        showToast('Parsed lead saved to dashboard!', 'success');
        closeModal('parseModal');
        loadDashboardStats();
        loadLeads();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==========================================
// CSV Batch Import
// ==========================================
let selectedCsvFile = null;

function openImportModal() {
    selectedCsvFile = null;
    document.getElementById('csv-file-input').value = '';
    document.getElementById('csv-file-label').textContent = 'Click to select CSV file';
    document.getElementById('csv-upload-btn').disabled = true;
    document.getElementById('csv-results-box').classList.add('hidden');
    openModal('importModal');
}

function handleCsvFileSelected(e) {
    const file = e.target.files[0];
    if (file) {
        selectedCsvFile = file;
        document.getElementById('csv-file-label').textContent = file.name;
        document.getElementById('csv-upload-btn').disabled = false;
    }
}

async function uploadCsvFile() {
    if (!selectedCsvFile) return;

    const formData = new FormData();
    formData.append('file', selectedCsvFile);

    const btn = document.getElementById('csv-upload-btn');
    btn.textContent = 'Uploading...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/leads/import-csv', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'CSV upload failed');
        }

        const result = await res.json();
        
        // Show result box
        const resultsBox = document.getElementById('csv-results-box');
        resultsBox.classList.remove('hidden');
        document.getElementById('csv-summary-counts').textContent = 
            `${result.imported_count} imported, ${result.duplicate_count} skipped (duplicate URLs)`;

        const errList = document.getElementById('csv-error-list');
        errList.innerHTML = '';
        if (result.errors && result.errors.length) {
            result.errors.forEach(e => {
                const div = document.createElement('div');
                div.textContent = `• ${e}`;
                errList.appendChild(div);
            });
        }

        showToast(`Import completed: ${result.imported_count} new leads added!`, 'success');
        loadDashboardStats();
        loadLeads();
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        btn.textContent = 'Upload & Import';
        btn.disabled = false;
    }
}

// ==========================================
// Google Sheets Integration & Sync
// ==========================================
function openSheetsModal() {
    openModal('sheetsModal');
}

async function triggerSheetsSync() {
    const icon = document.getElementById('sync-icon');
    if (icon) icon.classList.add('animate-spin');

    try {
        const res = await fetch('/api/sync/sheets', { method: 'POST' });
        const result = await res.json();

        if (result.success) {
            showToast(result.message, 'success');
            loadDashboardStats();
            loadLeads();
        } else {
            showToast(result.message, 'warning');
        }
    } catch (err) {
        showToast('Sync error: ' + err.message, 'error');
    } finally {
        if (icon) icon.classList.remove('animate-spin');
    }
}

// ==========================================
// Daily Digest Report (09:00 AM)
// ==========================================
async function openReportModal() {
    openModal('reportModal');
    const frame = document.getElementById('report-preview-frame');
    frame.srcdoc = '<p style="color:#888; font-family:sans-serif; padding:20px;">Generating digest preview...</p>';

    try {
        const res = await fetch('/api/report/preview');
        if (!res.ok) throw new Error('Failed to generate report preview');
        const data = await res.json();
        frame.srcdoc = data.html_content;
    } catch (err) {
        frame.srcdoc = `<p style="color:red; font-family:sans-serif; padding:20px;">Error: ${err.message}</p>`;
    }
}

async function copyAppsScriptCode() {
    try {
        const res = await fetch('/api/report/apps-script');
        const data = await res.json();
        navigator.clipboard.writeText(data.code).then(() => {
            showToast('Google Apps Script code copied to clipboard!', 'success');
        });
    } catch (err) {
        showToast('Error copying Apps Script code: ' + err.message, 'error');
    }
}

// ==========================================
// Export Leads
// ==========================================
function exportLeads(format) {
    window.location.href = `/api/leads/export?format=${format}`;
}

// ==========================================
// Helpers: Modals & Toasts
// ==========================================
function openModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('hidden');
    lucide.createIcons();
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
}

function resetFilters() {
    document.getElementById('filter-search').value = '';
    document.getElementById('filter-status').value = 'All';
    document.getElementById('filter-industry').value = 'All';
    document.getElementById('filter-country').value = 'All';
    document.getElementById('filter-service').value = 'All';
    document.getElementById('filter-min-score').value = '0';
    loadLeads();
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';

    let iconName = 'info';
    let borderColor = 'var(--accent-blue)';
    if (type === 'success') {
        iconName = 'check-circle';
        borderColor = 'var(--status-qualified)';
    } else if (type === 'error') {
        iconName = 'alert-triangle';
        borderColor = 'var(--status-disqualified)';
    } else if (type === 'warning') {
        iconName = 'alert-circle';
        borderColor = 'var(--status-review)';
    }

    toast.style.borderLeftColor = borderColor;
    toast.innerHTML = `
        <i data-lucide="${iconName}" class="w-4 h-4 flex-shrink-0"></i>
        <span>${escapeHtml(message)}</span>
    `;
    container.appendChild(toast);
    lucide.createIcons();

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, function(m) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        }[m];
    });
}

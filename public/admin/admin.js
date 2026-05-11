/* ════════════════════════════════════════════════════
   NursingCNE Admin Panel – JavaScript
════════════════════════════════════════════════════ */
'use strict';

let authToken = null;
let currentPage = 'dashboard';
let regPageNum = 1;

// ── Helpers ─────────────────────────────────────────
function esc(s) {
    const m = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(s || '').replace(/[&<>"']/g, c => m[c]);
}
function fmt(n) { return Number(n || 0).toLocaleString('en-IN'); }
function fmtDate(d) {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}
function fmtDateTime(d) {
    if (!d) return '—';
    return new Date(d).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function showToast(msg, type = 'info') {
    const c = document.getElementById('toastContainer');
    const t = document.createElement('div');
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    t.className = `toast ${type}`;
    t.innerHTML = `<span>${icons[type] || '💬'}</span><span>${msg}</span>`;
    c.appendChild(t);
    requestAnimationFrame(() => t.classList.add('show'));
    setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 400); }, 4000);
}

function statusBadge(s) {
    const map = {
        success: '<span class="badge badge-success">✅ Paid</span>',
        pending: '<span class="badge badge-pending">⏳ Pending</span>',
        failed: '<span class="badge badge-failed">❌ Failed</span>',
        refunded: '<span class="badge badge-refunded">↩ Refunded</span>'
    };
    return map[s] || `<span class="badge">${esc(s)}</span>`;
}

async function apiFetch(url, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
    const res = await fetch(url, { ...opts, headers, credentials: 'include' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Error ${res.status}`);
    return data;
}

// ── Clock ────────────────────────────────────────────
function updateClock() {
    const el = document.getElementById('topbarTime');
    if (el) el.textContent = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}
updateClock();
setInterval(updateClock, 60000);

// ── Auth ─────────────────────────────────────────────
document.getElementById('togglePass').addEventListener('click', () => {
    const inp = document.getElementById('loginPass');
    inp.type = inp.type === 'password' ? 'text' : 'password';
});

document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('loginBtn');
    const errEl = document.getElementById('loginError');
    btn.disabled = true;
    btn.textContent = 'Signing in...';
    errEl.textContent = '';

    try {
        const data = await apiFetch('/api/admin/login', {
            method: 'POST',
            body: JSON.stringify({
                username: document.getElementById('loginUser').value,
                password: document.getElementById('loginPass').value
            })
        });
        authToken = data.token;
        document.getElementById('adminName').textContent = data.username;
        document.getElementById('adminAvatar').textContent = data.username[0].toUpperCase();
        showAdminApp();
    } catch (err) {
        errEl.textContent = err.message || 'Login failed';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Sign In';
    }
});

// Check if already authed
async function checkAuth() {
    try {
        const data = await apiFetch('/api/admin/verify');
        if (data.valid) {
            authToken = null; // Cookie-based
            document.getElementById('adminName').textContent = data.username;
            document.getElementById('adminAvatar').textContent = data.username[0].toUpperCase();
            showAdminApp();
        }
    } catch { /* not logged in */ }
}

function showAdminApp() {
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('adminApp').style.display = 'flex';
    loadPage('dashboard');
}

document.getElementById('logoutBtn').addEventListener('click', async () => {
    try { await apiFetch('/api/admin/logout', { method: 'POST' }); } catch { }
    authToken = null;
    document.getElementById('loginScreen').style.display = 'flex';
    document.getElementById('adminApp').style.display = 'none';
    document.getElementById('loginForm').reset();
});

// ── Page Navigation ──────────────────────────────────
function loadPage(page) {
    currentPage = page;
    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const pageEl = document.getElementById(`page-${page}`);
    const navEl = document.getElementById(`nav-${page}`);
    if (pageEl) pageEl.classList.remove('hidden');
    if (navEl) navEl.classList.add('active');
    const titles = { dashboard: 'Dashboard', offers: 'Offers & Events', registrations: 'Registrations', settings: 'Settings' };
    document.getElementById('pageTitle').textContent = titles[page] || page;
    pageFunctions[page]?.();
}
window.loadPage = loadPage;

const pageFunctions = {
    dashboard: loadDashboard,
    offers: loadOffers,
    registrations: loadRegistrations,
    settings: loadSettings
};

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', e => {
        e.preventDefault();
        loadPage(item.dataset.page);
        // Close mobile sidebar
        sidebar.classList.remove('mobile-open');
    });
});

// ── Sidebar Toggle ───────────────────────────────────
const sidebar = document.getElementById('sidebar');
document.getElementById('sidebarToggle').addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
});
document.getElementById('sidebarMobileToggle').addEventListener('click', () => {
    sidebar.classList.toggle('mobile-open');
});

// ── Dashboard ────────────────────────────────────────
async function loadDashboard() {
    try {
        const data = await apiFetch('/api/admin/dashboard');
        document.getElementById('stat-totalOffers').textContent = data.totalOffers;
        document.getElementById('stat-activeOffers').textContent = data.activeOffers;
        document.getElementById('stat-totalRegs').textContent = data.totalRegs;
        document.getElementById('stat-paidRegs').textContent = data.paidRegs;
        document.getElementById('stat-revenue').textContent = `₹${fmt(data.totalRevenue)}`;

        const tbody = document.getElementById('recentRegsTbody');
        if (data.recentRegs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="table-empty">No registrations yet</td></tr>';
            return;
        }
        tbody.innerHTML = data.recentRegs.map(r => `
      <tr>
        <td>#${r.id}</td>
        <td><strong>${esc(r.name)}</strong></td>
        <td>${esc(r.mobile)}</td>
        <td>${esc(r.offer_title || 'Direct')}</td>
        <td>₹${fmt(r.amount)}</td>
        <td>${statusBadge(r.payment_status)}</td>
        <td>${fmtDateTime(r.created_at)}</td>
      </tr>`).join('');
    } catch (err) {
        showToast('Failed to load dashboard: ' + err.message, 'error');
    }
}

// ── Offers ───────────────────────────────────────────
async function loadOffers() {
    const tbody = document.getElementById('offersTbody');
    tbody.innerHTML = '<tr><td colspan="7" class="table-empty">Loading...</td></tr>';
    try {
        const data = await apiFetch('/api/offers/all');
        if (!data.offers.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="table-empty">No offers yet. Click "Add New Offer" to create one.</td></tr>';
            return;
        }
        tbody.innerHTML = data.offers.map(o => `
      <tr>
        <td>#${o.id}</td>
        <td>
          <strong>${esc(o.title)}</strong>
          ${o.badge ? `<span class="badge badge-pending" style="margin-left:6px">${esc(o.badge)}</span>` : ''}
        </td>
        <td>
          <strong>₹${fmt(o.amount)}</strong>
          ${o.original_amount ? `<br><small style="color:#94a3b8;text-decoration:line-through">₹${fmt(o.original_amount)}</small>` : ''}
        </td>
        <td>${o.seats_total > 0 ? `${o.seats_total - o.seats_filled} / ${o.seats_total}` : '∞'}</td>
        <td>${fmtDate(o.valid_till)}</td>
        <td>
          <label class="toggle">
            <input type="checkbox" ${o.is_active ? 'checked' : ''} onchange="toggleOffer(${o.id}, this)" />
            <span class="toggle-slider"></span>
          </label>
        </td>
        <td>
          <div style="display:flex;gap:6px">
            <button class="btn btn-sm btn-outline btn-icon" onclick="editOffer(${o.id})" title="Edit">✏️</button>
            <button class="btn btn-sm btn-danger btn-icon" onclick="deleteOffer(${o.id})" title="Delete">🗑️</button>
          </div>
        </td>
      </tr>`).join('');
    } catch (err) {
        showToast('Failed to load offers: ' + err.message, 'error');
    }
}
window.loadOffers = loadOffers;

async function toggleOffer(id, el) {
    try {
        const data = await apiFetch(`/api/offers/${id}/toggle`, { method: 'PATCH' });
        showToast(`Offer ${data.is_active ? 'activated' : 'deactivated'}`, 'success');
    } catch (err) {
        el.checked = !el.checked;
        showToast('Failed: ' + err.message, 'error');
    }
}
window.toggleOffer = toggleOffer;

async function deleteOffer(id) {
    if (!confirm('Delete this offer? This cannot be undone.')) return;
    try {
        await apiFetch(`/api/offers/${id}`, { method: 'DELETE' });
        showToast('Offer deleted', 'success');
        loadOffers();
    } catch (err) {
        showToast('Delete failed: ' + err.message, 'error');
    }
}
window.deleteOffer = deleteOffer;

// Offer form
document.getElementById('addOfferBtn').addEventListener('click', () => {
    document.getElementById('offerForm').reset();
    document.getElementById('of-id').value = '';
    document.getElementById('of-is_active').checked = true;
    document.getElementById('offerModalTitle').textContent = 'Add New Offer';
    document.getElementById('offerFormBtn').textContent = 'Save Offer';
    openOfferModal();
});

async function editOffer(id) {
    try {
        const data = await apiFetch(`/api/offers/${id}`);
        const o = data.offer;
        document.getElementById('of-id').value = o.id;
        document.getElementById('of-title').value = o.title || '';
        document.getElementById('of-description').value = o.description || '';
        document.getElementById('of-amount').value = o.amount || '';
        document.getElementById('of-original_amount').value = o.original_amount || '';
        document.getElementById('of-badge').value = o.badge || '';
        document.getElementById('of-image_url').value = o.image_url || '';
        document.getElementById('of-valid_till').value = o.valid_till ? o.valid_till.split('T')[0] : '';
        document.getElementById('of-seats_total').value = o.seats_total || '';
        document.getElementById('of-is_active').checked = !!o.is_active;
        document.getElementById('offerModalTitle').textContent = 'Edit Offer';
        document.getElementById('offerFormBtn').textContent = 'Update Offer';
        openOfferModal();
    } catch (err) {
        showToast('Failed to load offer: ' + err.message, 'error');
    }
}
window.editOffer = editOffer;

document.getElementById('offerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('offerFormBtn');
    btn.disabled = true;
    btn.textContent = 'Saving...';
    const id = document.getElementById('of-id').value;

    const body = {
        title: document.getElementById('of-title').value,
        description: document.getElementById('of-description').value,
        amount: document.getElementById('of-amount').value,
        original_amount: document.getElementById('of-original_amount').value || null,
        badge: document.getElementById('of-badge').value,
        image_url: document.getElementById('of-image_url').value,
        valid_till: document.getElementById('of-valid_till').value || null,
        seats_total: document.getElementById('of-seats_total').value || 0,
        is_active: document.getElementById('of-is_active').checked
    };

    try {
        if (id) {
            await apiFetch(`/api/offers/${id}`, { method: 'PUT', body: JSON.stringify(body) });
            showToast('Offer updated successfully!', 'success');
        } else {
            await apiFetch('/api/offers', { method: 'POST', body: JSON.stringify(body) });
            showToast('Offer created successfully!', 'success');
        }
        closeOfferModal();
        loadOffers();
    } catch (err) {
        showToast('Save failed: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = id ? 'Update Offer' : 'Save Offer';
    }
});

function openOfferModal() {
    document.getElementById('offerModal').classList.add('open');
    document.getElementById('offerModalBd').classList.add('open');
}
function closeOfferModal() {
    document.getElementById('offerModal').classList.remove('open');
    document.getElementById('offerModalBd').classList.remove('open');
}
window.closeOfferModal = closeOfferModal;

// ── Registrations ────────────────────────────────────
async function loadRegistrations() {
    const tbody = document.getElementById('regsTbody');
    tbody.innerHTML = '<tr><td colspan="10" class="table-empty">Loading...</td></tr>';

    const search = document.getElementById('regSearch').value;
    const status = document.getElementById('regStatusFilter').value;

    try {
        const params = new URLSearchParams({ page: regPageNum, limit: 20 });
        if (search) params.set('search', search);
        if (status) params.set('status', status);

        const data = await apiFetch(`/api/registrations?${params}`);
        document.getElementById('regTotal').textContent = `${data.total} total`;

        if (!data.registrations.length) {
            tbody.innerHTML = '<tr><td colspan="10" class="table-empty">No registrations found</td></tr>';
            document.getElementById('regPagination').innerHTML = '';
            return;
        }

        tbody.innerHTML = data.registrations.map(r => `
      <tr>
        <td>#${r.id}</td>
        <td><strong>${esc(r.name)}</strong></td>
        <td style="max-width:160px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(r.institute)}</td>
        <td>${esc(r.mobile)}</td>
        <td style="font-size:12px">${esc(r.email)}</td>
        <td>${esc(r.offer_title || '—')}</td>
        <td><strong>₹${fmt(r.amount)}</strong></td>
        <td>${statusBadge(r.payment_status)}</td>
        <td style="white-space:nowrap;font-size:12px">${fmtDateTime(r.created_at)}</td>
        <td>
          <div style="display:flex;gap:4px">
            <select class="filter-select" style="padding:5px;font-size:12px;width:auto" onchange="updateRegStatus(${r.id}, this.value, this)">
              <option value="pending" ${r.payment_status === 'pending' ? 'selected' : ''}>Pending</option>
              <option value="success" ${r.payment_status === 'success' ? 'selected' : ''}>Paid</option>
              <option value="failed"  ${r.payment_status === 'failed' ? 'selected' : ''}>Failed</option>
              <option value="refunded"${r.payment_status === 'refunded' ? 'selected' : ''}>Refunded</option>
            </select>
            <button class="btn btn-sm btn-danger btn-icon" onclick="deleteReg(${r.id})" title="Delete">🗑️</button>
          </div>
        </td>
      </tr>`).join('');

        // Pagination
        const totalPages = Math.ceil(data.total / 20);
        const pg = document.getElementById('regPagination');
        if (totalPages <= 1) { pg.innerHTML = ''; return; }
        pg.innerHTML = Array.from({ length: totalPages }, (_, i) => `
      <button class="pg-btn ${i + 1 === regPageNum ? 'active' : ''}" onclick="goRegPage(${i + 1})">${i + 1}</button>
    `).join('');
    } catch (err) {
        showToast('Failed to load registrations: ' + err.message, 'error');
    }
}
window.loadRegistrations = loadRegistrations;

function goRegPage(n) { regPageNum = n; loadRegistrations(); }
window.goRegPage = goRegPage;

async function updateRegStatus(id, status, el) {
    try {
        await apiFetch(`/api/registrations/${id}/status`, { method: 'PATCH', body: JSON.stringify({ payment_status: status }) });
        showToast('Status updated', 'success');
    } catch (err) {
        showToast('Failed to update status', 'error');
    }
}
window.updateRegStatus = updateRegStatus;

async function deleteReg(id) {
    if (!confirm('Delete this registration? This cannot be undone.')) return;
    try {
        await apiFetch(`/api/registrations/${id}`, { method: 'DELETE' });
        showToast('Registration deleted', 'success');
        loadRegistrations();
    } catch (err) {
        showToast('Delete failed: ' + err.message, 'error');
    }
}
window.deleteReg = deleteReg;

function exportExcel() {
    const status = document.getElementById('regStatusFilter').value;
    let url = '/api/registrations/export/excel';
    if (status) url += `?status=${status}`;
    // Trigger download using auth
    const a = document.createElement('a');
    a.href = url;
    a.download = '';
    document.body.appendChild(a);
    a.click();
    a.remove();
}
window.exportExcel = exportExcel;

// Search with debounce
let searchTimer;
document.getElementById('regSearch').addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { regPageNum = 1; loadRegistrations(); }, 400);
});
document.getElementById('regStatusFilter').addEventListener('change', () => {
    regPageNum = 1; loadRegistrations();
});

// ── Settings ─────────────────────────────────────────
async function loadSettings() {
    try {
        const data = await apiFetch('/api/settings');
        const s = data.settings;
        for (const [key, val] of Object.entries(s)) {
            const el = document.getElementById(`s-${key}`);
            if (el) el.value = val || '';
        }
    } catch (err) {
        showToast('Failed to load settings: ' + err.message, 'error');
    }
}

document.getElementById('settingsForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const keys = ['site_name', 'site_tagline', 'site_phone', 'site_email', 'site_whatsapp', 'about_text', 'hero_title', 'hero_subtitle'];
    const settings = {};
    keys.forEach(k => { settings[k] = document.getElementById(`s-${k}`)?.value || ''; });
    try {
        await apiFetch('/api/settings', { method: 'PUT', body: JSON.stringify({ settings }) });
        showToast('Settings saved successfully!', 'success');
    } catch (err) {
        showToast('Failed to save settings: ' + err.message, 'error');
    }
});

document.getElementById('changePassForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const current = document.getElementById('cp-current').value;
    const newPass = document.getElementById('cp-new').value;
    const confirm = document.getElementById('cp-confirm').value;

    if (newPass !== confirm) { showToast('New passwords do not match', 'error'); return; }
    if (newPass.length < 8) { showToast('Password must be at least 8 characters', 'error'); return; }

    try {
        await apiFetch('/api/admin/change-password', { method: 'PUT', body: JSON.stringify({ currentPassword: current, newPassword: newPass }) });
        showToast('Password updated successfully!', 'success');
        e.target.reset();
    } catch (err) {
        showToast('Failed: ' + err.message, 'error');
    }
});

// ── Init ─────────────────────────────────────────────
checkAuth();

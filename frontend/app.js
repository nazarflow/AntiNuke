const API_BASE = '/api';
let authHeader = '';

// DOM Elements
const loginOverlay = document.getElementById('login-overlay');
const appContainer = document.getElementById('app');
const loginBtn = document.getElementById('login-btn');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const loginError = document.getElementById('login-error');
const pageTitle = document.getElementById('page-title');

// Auth
loginBtn.addEventListener('click', async () => {
    const user = usernameInput.value;
    const pass = passwordInput.value;
    const hash = btoa(`${user}:${pass}`);
    authHeader = `Basic ${hash}`;

    try {
        const res = await fetch(`${API_BASE}/admins`, { headers: { 'Authorization': authHeader } });
        if (res.ok) {
            loginOverlay.classList.add('hidden');
            appContainer.classList.remove('hidden');
            loadDashboardStats();
        } else {
            loginError.classList.remove('hidden');
        }
    } catch (e) {
        loginError.innerText = 'Network error';
        loginError.classList.remove('hidden');
    }
});

// Navigation
document.querySelectorAll('.nav-links li').forEach(li => {
    li.addEventListener('click', (e) => {
        document.querySelectorAll('.nav-links li').forEach(el => el.classList.remove('active'));
        e.target.classList.add('active');
        const viewId = e.target.getAttribute('data-view');
        
        document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
        document.getElementById(`view-${viewId}`).classList.remove('hidden');
        
        pageTitle.innerText = e.target.innerText;

        if (viewId === 'admins') loadAdmins();
        if (viewId === 'dashboard') loadDashboardStats();
    });
});

// API Helpers
async function apiGet(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`, { headers: { 'Authorization': authHeader } });
    if (!res.ok) throw new Error('API Error');
    return res.json();
}

async function apiPost(endpoint, body = null) {
    const opts = { method: 'POST', headers: { 'Authorization': authHeader, 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${API_BASE}${endpoint}`, opts);
    if (!res.ok) throw new Error('API Error');
    return res.json();
}

async function apiDelete(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`, { method: 'DELETE', headers: { 'Authorization': authHeader } });
    if (!res.ok) throw new Error('API Error');
    return res.json();
}

// Dashboard
async function loadDashboardStats() {
    try {
        const [admins, tracked, owners] = await Promise.all([
            apiGet('/admins'),
            apiGet('/tracked-users'),
            // We can't get global owners easily without iterating guilds, so we'll leave it as a placeholder or fetch first guild
        ]);
        document.getElementById('stat-admins').innerText = admins.length;
        document.getElementById('stat-tracked').innerText = tracked.length;
        document.getElementById('stat-owners').innerText = "N/A";
    } catch (e) { console.error(e); }
}

// Admins
async function loadAdmins() {
    const tbody = document.querySelector('#admins-table tbody');
    tbody.innerHTML = '<tr><td colspan="2">Loading...</td></tr>';
    try {
        const admins = await apiGet('/admins');
        tbody.innerHTML = admins.map(id => `
            <tr>
                <td>${id}</td>
                <td><button class="btn-danger" onclick="removeAdmin(${id})">Remove</button></td>
            </tr>
        `).join('') || '<tr><td colspan="2">No admins found.</td></tr>';
    } catch (e) { tbody.innerHTML = '<tr><td colspan="2">Error loading admins</td></tr>'; }
}

async function promptAddAdmin() {
    const id = prompt("Enter User ID to add as Admin:");
    if (id && !isNaN(id)) {
        try {
            await apiPost(`/admins/${id}`);
            loadAdmins();
        } catch (e) { alert("Failed to add admin"); }
    }
}

window.removeAdmin = async (id) => {
    if (confirm(`Remove admin ${id}?`)) {
        try {
            await apiDelete(`/admins/${id}`);
            loadAdmins();
        } catch (e) { alert("Failed to remove admin"); }
    }
};

// Limits (Example for global limits view)
window.loadGuildLimits = async () => {
    const gid = document.getElementById('limit-guild-id').value;
    if (!gid) return alert("Enter Guild ID");
    try {
        const limits = await apiGet(`/guilds/${gid}/limits`);
        const editor = document.getElementById('limits-editor');
        editor.innerHTML = Object.keys(limits).filter(k => k !== 'guild_id').map(k => `
            <div>
                <label>${k}</label>
                <input type="number" id="limit-${k}" value="${limits[k]}" class="input-small" style="width:100%; margin-top:0.5rem">
            </div>
        `).join('');
        editor.classList.remove('hidden');
    } catch (e) {
        alert("Limits not found for this guild, or error loading.");
    }
};

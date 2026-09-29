/**
 * InternTrack AI - Unified API Client & JWT Session Manager
 */

class ApiClient {
    constructor() {
        this.baseUrl = '';
        this.accessTokenKey = 'it_access_token';
        this.refreshTokenKey = 'it_refresh_token';
        this.userKey = 'it_user_data';
    }

    getAccessToken() {
        return localStorage.getItem(this.accessTokenKey);
    }

    getRefreshToken() {
        return localStorage.getItem(this.refreshTokenKey);
    }

    getUser() {
        const data = localStorage.getItem(this.userKey);
        try {
            return data ? JSON.parse(data) : null;
        } catch {
            return null;
        }
    }

    setSession(tokens, user) {
        if (tokens.access) localStorage.setItem(this.accessTokenKey, tokens.access);
        if (tokens.refresh) localStorage.setItem(this.refreshTokenKey, tokens.refresh);
        if (user) localStorage.setItem(this.userKey, JSON.stringify(user));
    }

    clearSession() {
        localStorage.removeItem(this.accessTokenKey);
        localStorage.removeItem(this.refreshTokenKey);
        localStorage.removeItem(this.userKey);
    }

    isAuthenticated() {
        return Boolean(this.getAccessToken());
    }

    async refreshAccessToken() {
        const refresh = this.getRefreshToken();
        if (!refresh) return null;

        try {
            const res = await fetch('/api/auth/refresh/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh })
            });
            if (res.ok) {
                const data = await res.json();
                if (data.access) {
                    localStorage.setItem(this.accessTokenKey, data.access);
                    return data.access;
                }
            }
        } catch (e) {
            console.error('Token refresh failed:', e);
        }
        this.clearSession();
        return null;
    }

    async request(endpoint, options = {}) {
        let token = this.getAccessToken();
        const headers = options.headers || {};

        if (token && !headers['Authorization']) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // Only set Content-Type to JSON if not FormData
        if (!(options.body instanceof FormData) && !headers['Content-Type']) {
            headers['Content-Type'] = 'application/json';
        }

        options.headers = headers;

        let response = await fetch(endpoint, options);

        // If 401 Unauthorized, attempt refresh once
        if (response.status === 401 && this.getRefreshToken()) {
            token = await this.refreshAccessToken();
            if (token) {
                options.headers['Authorization'] = `Bearer ${token}`;
                response = await fetch(endpoint, options);
            } else {
                // If on a protected page, redirect to login
                if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register') && window.location.pathname !== '/') {
                    window.location.href = '/login/?session_expired=1';
                }
            }
        }

        return response;
    }

    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    async post(endpoint, data) {
        const body = data instanceof FormData ? data : JSON.stringify(data);
        return this.request(endpoint, { method: 'POST', body });
    }

    async put(endpoint, data) {
        const body = data instanceof FormData ? data : JSON.stringify(data);
        return this.request(endpoint, { method: 'PUT', body });
    }

    async patch(endpoint, data) {
        const body = data instanceof FormData ? data : JSON.stringify(data);
        return this.request(endpoint, { method: 'PATCH', body });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

const api = new ApiClient();

// Toast notification helper
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    const colorClasses = {
        success: 'bg-emerald-600 text-white border-emerald-700',
        error: 'bg-rose-600 text-white border-rose-700',
        warning: 'bg-amber-500 text-white border-amber-600',
        info: 'bg-slate-900 text-white border-slate-800'
    }[type] || 'bg-slate-900 text-white border-slate-800';

    toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border text-sm font-medium transition-all transform duration-300 opacity-0 translate-y-2 ${colorClasses}`;
    toast.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" class="ml-auto text-white/80 hover:text-white">&times;</button>
    `;

    container.appendChild(toast);
    requestAnimationFrame(() => {
        toast.classList.remove('opacity-0', 'translate-y-2');
    });

    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// Global Auth Check for Protected Pages
document.addEventListener('DOMContentLoaded', () => {
    const publicPaths = ['/', '/login/', '/register/'];
    const currentPath = window.location.pathname;

    const isPublic = publicPaths.some(p => currentPath === p || (p !== '/' && currentPath.startsWith(p)));
    if (!isPublic && !api.isAuthenticated()) {
        window.location.href = `/login/?next=${encodeURIComponent(currentPath)}`;
    }
});

/**
 * Tiny REST API client for the Tran Gia Phat backend.
 * All pages use this instead of calling fetch() directly, so error
 * handling and auth-header injection stay consistent in one place.
 */
const TGP_API = (() => {
  // Same-origin by default (the Flask backend also serves this frontend -
  // see backend/app/__init__.py). Override window.TGP_API_BASE before this
  // script loads if you deploy the frontend separately.
  const BASE = window.TGP_API_BASE || '';

  function getToken() {
    return localStorage.getItem('tgp_admin_token') || '';
  }

  function setToken(token) {
    if (token) localStorage.setItem('tgp_admin_token', token);
    else localStorage.removeItem('tgp_admin_token');
  }

  async function request(method, path, body, opts = {}) {
    const headers = { ...(opts.headers || {}) };
    let payload = body;

    if (body instanceof FormData) {
      // let the browser set the multipart boundary
    } else if (body !== undefined) {
      headers['Content-Type'] = 'application/json';
      payload = JSON.stringify(body);
    }

    if (opts.auth !== false) {
      const token = getToken();
      if (token) headers['Authorization'] = `Bearer ${token}`;
    }

    let response;
    try {
      response = await fetch(BASE + path, { method, headers, body: payload });
    } catch (networkErr) {
      throw { success: false, error: 'Không thể kết nối tới máy chủ. Vui lòng kiểm tra kết nối mạng.', networkError: true };
    }

    let data = null;
    try { data = await response.json(); } catch (_e) { /* non-JSON response (e.g. CSV export) */ }

    if (!response.ok) {
      const errObj = data || { success: false, error: `Loi ${response.status}` };
      errObj.status = response.status;
      throw errObj;
    }
    return data;
  }

  return {
    get: (path, opts) => request('GET', path, undefined, opts),
    post: (path, body, opts) => request('POST', path, body, opts),
    put: (path, body, opts) => request('PUT', path, body, opts),
    del: (path, opts) => request('DELETE', path, undefined, opts),
    getToken,
    setToken,
    isLoggedIn: () => !!getToken(),
  };
})();

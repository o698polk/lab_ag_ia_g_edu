const API = {
  base: "/api/v1",

  getTokens() {
    return {
      access: localStorage.getItem("access_token"),
      refresh: localStorage.getItem("refresh_token"),
    };
  },

  setTokens(access, refresh) {
    if (access) localStorage.setItem("access_token", access);
    if (refresh) localStorage.setItem("refresh_token", refresh);
  },

  clear() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
  },

  async request(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    const { access } = this.getTokens();
    if (access) headers.Authorization = `Bearer ${access}`;

    let res = await fetch(`${this.base}${path}`, { ...options, headers });

    if (res.status === 401 && this.getTokens().refresh) {
      const ok = await this.refresh();
      if (ok) {
        headers.Authorization = `Bearer ${this.getTokens().access}`;
        res = await fetch(`${this.base}${path}`, { ...options, headers });
      }
    }

    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Error en la solicitud");
      return data;
    }
    if (!res.ok) throw new Error("Error en la solicitud");
    return res;
  },

  async refresh() {
    const { refresh } = this.getTokens();
    if (!refresh) return false;
    const res = await fetch(`${this.base}/auth/refresh`, {
      method: "POST",
      headers: { Authorization: `Bearer ${refresh}` },
    });
    if (!res.ok) {
      this.clear();
      return false;
    }
    const data = await res.json();
    this.setTokens(data.access_token, data.refresh_token);
    return true;
  },

  get(path) {
    return this.request(path);
  },

  post(path, body) {
    return this.request(path, { method: "POST", body: JSON.stringify(body) });
  },

  put(path, body) {
    return this.request(path, { method: "PUT", body: JSON.stringify(body) });
  },

  patch(path, body) {
    return this.request(path, { method: "PATCH", body: JSON.stringify(body) });
  },

  del(path) {
    return this.request(path, { method: "DELETE" });
  },
};

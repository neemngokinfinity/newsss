/* API client + session handling */
(function () {
  const TOKEN_KEY = "nb_token";
  const Auth = {
    token() { return localStorage.getItem(TOKEN_KEY); },
    setToken(t) { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); },
  };
  window.Auth = Auth;

  async function req(method, path, body) {
    const headers = {};
    const t = Auth.token();
    if (t) headers["Authorization"] = "Bearer " + t;
    if (body !== undefined && !(body instanceof FormData)) headers["Content-Type"] = "application/json";
    const opts = { method, headers };
    if (body !== undefined) opts.body = body instanceof FormData ? body : JSON.stringify(body);
    let res;
    try {
      res = await fetch(path, opts);
    } catch (e) {
      throw new Error("Network error: " + e.message);
    }
    if (res.status === 401) {
      Auth.setToken(null);
      if (window.onUnauthorized) window.onUnauthorized();
      const err = new Error("Unauthorized");
      err.status = 401;
      throw err;
    }
    const ct = res.headers.get("content-type") || "";
    let data = null;
    if (ct.includes("application/json")) {
      try { data = await res.json(); } catch (e) { data = null; }
    }
    if (!res.ok) {
      const err = new Error((data && data.detail) || ("HTTP " + res.status));
      err.status = res.status;
      throw err;
    }
    return data;
  }

  const API = {
    get: (p) => req("GET", p),
    post: (p, b) => req("POST", p, b),
    put: (p, b) => req("PUT", p, b),
    del: (p) => req("DELETE", p),
    login: async (username, password) => {
      const data = await req("POST", "/api/auth/login", { username, password });
      Auth.setToken(data.token);
      return data;
    },
    logout: () => req("POST", "/api/auth/logout"),
    me: () => req("GET", "/api/auth/me"),
    upload: (path, file) => {
      const fd = new FormData();
      fd.append("file", file);
      return req("POST", path, fd);
    },
  };
  window.API = API;

  /* Streaming chat over SSE (POST + ReadableStream) */
  function streamChat(payload, handlers) {
    const controller = new AbortController();
    (async () => {
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(Auth.token() ? { Authorization: "Bearer " + Auth.token() } : {}),
          },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });
        if (!res.ok) {
          let detail = "HTTP " + res.status;
          try { const j = await res.json(); if (j.detail) detail = j.detail; } catch (e) {}
          handlers.error && handlers.error(new Error(detail));
          return;
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        let ev = null;
        let data = "";
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          let idx;
          while ((idx = buf.indexOf("\n\n")) !== -1) {
            const frame = buf.slice(0, idx);
            buf = buf.slice(idx + 2);
            for (const line of frame.split("\n")) {
              if (line.startsWith("event: ")) ev = line.slice(7).trim();
              else if (line.startsWith("data: ")) data = line.slice(6).trim();
            }
            if (data) {
              let parsed = null;
              try { parsed = JSON.parse(data); } catch (e) {}
              if (handlers.onEvent) handlers.onEvent(ev || "message", parsed);
              if (ev === "done" || ev === "error" || ev === "stopped") {
                if (handlers.onFinish) handlers.onFinish(ev, parsed);
              }
              ev = null; data = "";
            }
          }
        }
        if (handlers.onFinish && ev !== "done" && ev !== "error") handlers.onFinish("eof", null);
      } catch (e) {
        if (e.name !== "AbortError" && handlers.error) handlers.error(e);
      }
    })();
    return { abort: () => controller.abort() };
  }
  window.streamChat = streamChat;
})();

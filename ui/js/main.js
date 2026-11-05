/* App shell, router, login, dashboard */
(function () {
  const U = window.UI;

  const NAV = [
    { id: "dashboard", label: "Dashboard", icon: "🏠" },
    { id: "chat", label: "Chat", icon: "💬" },
    { id: "agents", label: "Agents", icon: "🤖" },
    { id: "mcp", label: "MCP", icon: "🔌" },
    { id: "providers", label: "Providers", icon: "⚡" },
    { id: "tools", label: "Tools", icon: "🛠" },
    { id: "files", label: "Files", icon: "📁" },
    { id: "history", label: "History", icon: "🕘" },
    { id: "logs", label: "Logs", icon: "📜" },
    { id: "settings", label: "Settings", icon: "⚙️" },
  ];

  function showLogin() {
    document.body.innerHTML = "";
    const w = U.el(`
      <div class="login-wrap">
        <div class="card login-card">
          <div class="login-logo">🐈</div>
          <h1 style="text-align:center">nanobot</h1>
          <p class="muted" style="text-align:center">AI Platform</p>
          <label>Username</label><input id="lg-user">
          <label>Password</label><input id="lg-pass" type="password">
          <div id="lg-err" class="err" style="display:none"></div>
          <button class="btn" id="lg-btn" style="width:100%;margin-top:14px">Sign in</button>
        </div>
      </div>`);
    const doLogin = async () => {
      const user = U.$("#lg-user").value.trim(), pass = U.$("#lg-pass").value;
      if (!user || !pass) return;
      const btn = U.$("#lg-btn");
      btn.disabled = true; btn.textContent = "Signing in…";
      try {
        await API.login(user, pass);
        boot();
      } catch (e) {
        const err = U.$("#lg-err");
        err.style.display = "block"; err.textContent = e.message;
        btn.disabled = false; btn.textContent = "Sign in";
      }
    };
    U.$("#lg-btn").onclick = doLogin;
    U.$("#lg-pass").addEventListener("keydown", (e) => { if (e.key === "Enter") doLogin(); });
    U.$("#lg-user").focus();
  }

  function shell() {
    document.body.innerHTML = `
      <div class="shell">
        <aside class="sidebar" id="sidebar">
          <div class="brand"><div class="logo">🐈</div><span>nanobot</span></div>
          <nav id="nav" style="display:flex;flex-direction:column;gap:4px"></nav>
          <div class="muted" style="font-size:11px;padding:12px 8px;border-top:1px solid var(--border);margin-top:auto">AI Platform · v<span id="ver"></span></div>
        </aside>
        <div class="overlay" id="overlay" style="display:none"></div>
        <main class="main">
          <div class="topbar">
            <button class="btn ghost hamburger" id="burger">☰</button>
            <h1 id="page-title">Dashboard</h1>
            <div id="health" class="health" title="Service status"><span></span></div>
          </div>
          <div id="content" class="content"></div>
        </main>
      </div>`;

    const nav = U.$("#nav");
    NAV.forEach((n) => {
      const a = U.el(`<a href="#${n.id}" class="nav-item" data-nav="${n.id}">${n.icon} <span>${n.label}</span></a>`);
      nav.appendChild(a);
    });

    const burger = U.$("#burger"), sidebar = U.$("#sidebar"), overlay = U.$("#overlay");
    const closeMobile = () => { sidebar.classList.remove("open"); overlay.style.display = "none"; };
    burger.onclick = () => { sidebar.classList.toggle("open"); overlay.style.display = sidebar.classList.contains("open") ? "block" : "none"; };
    overlay.onclick = closeMobile;

    try { API.get("/api/version").then((v) => { U.$("#ver").textContent = v.version || ""; }); } catch (e) {}

    window.addEventListener("hashchange", route);
    route();
    monitorHealth();
  }

  function route() {
    let hash = window.location.hash.replace(/^#\/?/, "");
    if (!hash || hash === "login") hash = "dashboard";
    const parts = hash.split("/");
    const id = parts[0];
    const content = U.$("#content");
    if (!content) return;

    document.querySelectorAll("[data-nav]").forEach((a) => a.classList.toggle("active", a.dataset.nav === id));

    const titles = { dashboard: "Dashboard", chat: "Chat", agents: "Agents", mcp: "MCP Servers", providers: "Providers", tools: "Tools", files: "Files", history: "History", logs: "Logs", settings: "Settings" };
    const titleEl = U.$("#page-title");
    if (titleEl) titleEl.textContent = titles[id] || "nanobot";

    if (id === "chat") {
      const chat = new window.ChatPage();
      chat.render(content);
      if (parts[1]) chat.convId = Number(parts[1]);
      if (parts[1]) chat.loadConversation(Number(parts[1]));
    } else if (id === "dashboard") {
      dashboard(content);
    } else if (N[id]) {
      N[id](content);
    } else {
      content.innerHTML = '<div class="muted">Unknown page</div>';
    }
  }

  const N = {
    agents: (r) => Manage.listAgents(r),
    mcp: (r) => Manage.listMcp(r),
    providers: (r) => Manage.listProviders(r),
    tools: (r) => Manage.listTools(r),
    files: (r) => Manage.filesPage(r),
    history: (r) => Manage.historyPage(r),
    logs: (r) => Manage.logsPage(r),
    settings: (r) => Manage.settingsPage(r),
  };

  function cards(rows) {
    return `<div class="cards">` + rows.map((c) => `
      <div class="card dash">
        <div class="dash-icon">${c.icon}</div>
        <div class="dash-body"><div class="dash-val">${c.val}</div><div class="dash-label">${c.label}</div></div>
      </div>`).join("") + `</div>`;
  }

  async function dashboard(root) {
    root.innerHTML = `<div class="row spread"><h3>Dashboard</h3><span class="muted" id="dash-time">…</span></div>
      <div id="dash-cards" class="cards"><div class="muted">Loading…</div></div>
      <div class="row spread" style="margin-top:22px"><h4 style="margin:0">Recent activity</h4></div>
      <div id="dash-audit" class="card" style="font-size:13px"></div>`;
    const refresh = async () => {
      U.$("#dash-time").textContent = new Date().toLocaleString();
      try {
        const [sys, convs, providers, tools, audit] = await Promise.all([
          API.get("/api/system/status"),
          API.get("/api/conversations").catch(() => []),
          API.get("/api/providers").catch(() => []),
          API.get("/api/tools").catch(() => []),
          API.get("/api/audit").catch(() => []),
        ]);
        const gb = (n) => n != null ? (n / 1073741824).toFixed(1) : "?";
        const memUsed = sys.mem && sys.mem.used != null ? gb(sys.mem.used) : "?";
        const memTotal = sys.mem && sys.mem.total != null ? gb(sys.mem.total) : "?";
        const load = sys.cpu && sys.cpu.load1 != null ? sys.cpu.load1.toFixed(1) : "?";
        const convCount = sys.conversations != null ? sys.conversations : convs.length;
        U.$("#dash-cards").innerHTML = cards([
          { icon: "🖥", val: `${load}`, label: "Load (1m)" },
          { icon: "🧠", val: `${memUsed}G`, label: `Memory (${memTotal}G)` },
          { icon: "💬", val: `${convCount}`, label: "Conversations" },
          { icon: "⚡", val: `${providers.length}`, label: "Providers" },
          { icon: "🛠", val: `${tools.length}`, label: "Tools" },
          { icon: "🟢", val: "Online", label: "Service" },
        ]);
        const auditEl = U.$("#dash-audit");
        if (Array.isArray(audit) && audit.length) {
          auditEl.innerHTML = audit.slice(0, 12).map((a) => `
            <div class="audit"><span class="badge">${U.esc(a.action || a.event || "")}</span>
            <span class="muted">${U.esc(a.actor || a.user || "")}</span>
            <span>${U.esc((a.detail || "").slice(0, 120))}</span>
            <em class="muted">${U.esc(a.ts || a.timestamp || "")}</em></div>`).join("");
        } else {
          auditEl.textContent = "(no activity yet)";
        }
      } catch (e) {
        U.$("#dash-cards").innerHTML = '<div class="err">' + U.esc("Failed to load: " + e.message) + "</div>";
      }
    };
    await refresh();
    const timer = setInterval(() => { if (window.location.hash.startsWith("#dashboard") || window.location.hash === "") refresh(); }, 10000);
    window.__dashTimer = timer;
  }

  function monitorHealth() {
    const h = U.$("#health");
    const tick = async () => {
      try {
        await API.get("/api/system/status");
        h.classList.toggle("ok", true);
        h.title = "Service online";
      } catch (e) {
        h.classList.remove("ok");
        h.title = "Service unreachable";
      }
    };
    tick();
    setInterval(tick, 15000);
  }

  async function boot() {
    try {
      await API.me();
      shell();
    } catch (e) {
      if (e.status === 401) showLogin();
      else { showLogin(); }
    }
  }

  window.addEventListener("DOMContentLoaded", boot);
})();

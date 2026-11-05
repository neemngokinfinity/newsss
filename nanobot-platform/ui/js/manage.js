/* Management pages */
(function () {
  const U = window.UI;

  function confirmTable(rows, cols) {
    const t = U.el("<table class='table'>" + cols.map((c) => `<th>${c}</th>`).join("") + "</table>");
    rows.forEach((r) => {
      const tr = document.createElement("tr");
      r.cells.forEach((c) => { const td = document.createElement("td"); td.innerHTML = c; tr.appendChild(td); });
      if (r.actions) tr.appendChild(r.actions);
      t.appendChild(tr);
    });
    return t;
  }

  async function listAgents(root) {
    let agents = [];
    try { agents = await API.get("/api/config/agents"); } catch (e) { U.toast(e.message, "err"); }
    root.innerHTML = `<div class="row spread"><h3>Agents</h3>
      <button class="btn" id="ma-new">+ New agent</button></div>
      <div class="muted" style="margin:6px 0 12px">Agents are Markdown files in <code>agents/</code>. Edit or create them here.</div>
      <div id="ma-list"></div>
      <div id="ma-editor" style="display:none;margin-top:16px"></div>`;
    const listEl = U.$("#ma-list");
    if (!agents.length) { listEl.innerHTML = '<div class="muted">No agents yet</div>'; }
    listEl.appendChild(confirmTable(agents.map((a) => ({
      cells: [U.esc(a.name), U.esc(a.title || ""), U.esc(a.provider || ""), U.esc(a.model || "")],
      actions: (() => {
        const td = document.createElement("td");
        const edit = U.el('<button class="btn ghost sm">Edit</button>');
        const del = U.el('<button class="btn ghost sm danger">Delete</button>');
        edit.onclick = () => editAgent(root, a, agents);
        del.onclick = async () => {
          U.confirmDialog("Delete agent", a.name, async () => {
            try { await API.del(`/api/config/agents/${a.name}`); U.toast("Deleted", "ok"); listAgents(root); }
            catch (e) { U.toast(e.message, "err"); }
          });
        };
        td.append(edit, del);
        return td;
      })(),
    })), ["Name", "Title", "Provider", "Model", ""]));

    U.$("#ma-new").onclick = () => editAgent(root, null, agents);
  }

  function editAgent(root, agent, allAgents) {
    const ed = U.$("#ma-editor");
    U.$$("#ma-list tr.selected").forEach((e) => e.classList.remove("selected"));
    ed.style.display = "block";
    const a = agent || {};
    ed.innerHTML = `
      <div class="card">
        <h4>${a.name ? "Edit agent" : "New agent"}</h4>
        <label>Name (file name, no spaces)</label>
        <input id="ea-name" value="${U.esc(a.name || "")}" ${a.name ? "disabled" : ""}>
        <label>Title</label>
        <input id="ea-title" value="${U.esc(a.title || "")}">
        <label>Description</label>
        <textarea id="ea-desc" rows="2">${U.esc(a.description || "")}</textarea>
        <div class="row" style="gap:12px;flex-wrap:wrap">
          <div><label>Provider</label><input id="ea-provider" value="${U.esc(a.provider || "")}"></div>
          <div><label>Model</label><input id="ea-model" value="${U.esc(a.model || "")}"></div>
        </div>
        <label>Prompt (Markdown, optional)</label>
        <textarea id="ea-prompt" rows="6">${U.esc(a.prompt || "")}</textarea>
        <div class="row" style="gap:10px;margin-top:12px">
          <button class="btn" id="ea-save">Save</button>
          <button class="btn ghost" id="ea-cancel">Cancel</button>
        </div>
      </div>`;
    U.$("#ea-cancel").onclick = () => { ed.style.display = "none"; };
    U.$("#ea-save").onclick = async () => {
      const name = U.$("#ea-name").value.trim();
      if (!name) { U.toast("Name required", "err"); return; }
      const body = { name, title: U.$("#ea-title").value.trim(), description: U.$("#ea-desc").value.trim(), prompt: U.$("#ea-prompt").value };
      const provider = U.$("#ea-provider").value.trim(), model = U.$("#ea-model").value.trim();
      if (provider || model) body.llm = { provider: provider || undefined, model: model || undefined };
      try {
        if (agent) { await API.put(`/api/config/agents/${agent.name}`, body); }
        else { await API.post("/api/config/agents", body); }
        U.toast("Saved", "ok");
        listAgents(root);
      } catch (e) { U.toast(e.message, "err"); }
    };
  }

  async function listMcp(root) {
    let servers = [];
    try { servers = await API.get("/api/mcpservers"); } catch (e) { U.toast(e.message, "err"); }
    root.innerHTML = `<div class="row spread"><h3>MCP Servers</h3>
      <button class="btn" id="mm-new">+ Add server</button></div>
      <div class="muted" style="margin:6px 0 12px">MCP servers provide tools. Only <code>http</code> (JSON-RPC) transport is supported.</div>
      <div id="mm-list"></div>`;
    const listEl = U.$("#mm-list");
    if (!servers.length) { listEl.innerHTML = '<div class="muted">No servers yet</div>'; }
    listEl.appendChild(confirmTable(servers.map((s) => ({
      cells: [U.esc(s.name), `<code>${U.esc(s.url || "")}</code>`, U.esc(s.headers ? Object.keys(s.headers).length + " header(s)" : "")],
      actions: (() => {
        const td = document.createElement("td");
        const test = U.el('<button class="btn ghost sm">Test</button>');
        const del = U.el('<button class="btn ghost sm danger">Delete</button>');
        test.onclick = async () => {
          try { const r = await API.post(`/api/mcpservers/${s.name}/test`, {}); U.toast("OK: " + JSON.stringify(r), "ok"); }
          catch (e) { U.toast(e.message, "err"); }
        };
        del.onclick = () => {
          U.confirmDialog("Delete MCP server", s.name, async () => {
            try { await API.del(`/api/mcpservers/${s.name}`); U.toast("Deleted", "ok"); listMcp(root); }
            catch (e) { U.toast(e.message, "err"); }
          });
        };
        td.append(test, del);
        return td;
      })(),
    })), ["Name", "URL", "Headers", ""]));

    U.$("#mm-new").onclick = () => {
      const ed = U.el(`
        <div class="card">
          <h4>Add MCP server</h4>
          <label>Name</label><input id="me-name">
          <label>URL (e.g. http://host:port/mcp)</label><input id="me-url">
          <label>Headers (JSON, optional)</label><textarea id="me-headers" rows="2"></textarea>
          <div class="row" style="gap:10px;margin-top:12px">
            <button class="btn" id="me-save">Save</button>
            <button class="btn ghost" id="me-cancel">Cancel</button>
          </div>
        </div>`);
      ed.querySelector("#me-cancel").onclick = () => ed.remove();
      ed.querySelector("#me-save").onclick = async () => {
        let headers = {};
        try { headers = U.$("#me-headers").value.trim() ? JSON.parse(U.$("#me-headers").value) : {}; }
        catch (e) { U.toast("Headers must be valid JSON", "err"); return; }
        try {
          await API.post("/api/mcpservers", { name: U.$("#me-name").value.trim(), url: U.$("#me-url").value.trim(), headers });
          U.toast("Added", "ok");
          listMcp(root);
        } catch (e) { U.toast(e.message, "err"); }
      };
      ed.style.display = "block";
      listEl.after(ed);
    };
  }

  async function listProviders(root) {
    let providers = [];
    try { providers = await API.get("/api/providers"); } catch (e) { U.toast(e.message, "err"); }
    root.innerHTML = `<div class="row spread"><h3>LLM Providers</h3>
      <button class="btn" id="mp-new">+ Add provider</button></div>
      <div class="muted" style="margin:6px 0 12px">API keys are masked after save and never shown again.</div>
      <div id="mp-list"></div>`;
    const listEl = U.$("#mp-list");
    if (!providers.length) { listEl.innerHTML = '<div class="muted">No providers yet</div>'; }
    listEl.appendChild(confirmTable(providers.map((p) => ({
      cells: [U.esc(p.name), U.esc(p.baseURL || ""), U.esc(p.hasKey ? "••••••••" : ""), U.esc(p.model || "")],
      actions: (() => {
        const td = document.createElement("td");
        const test = U.el('<button class="btn ghost sm">Test</button>');
        const del = U.el('<button class="btn ghost sm danger">Delete</button>');
        test.onclick = async () => {
          U.toast("Testing…", "ok");
          try { await API.post(`/api/providers/${p.name}/test`, {}); U.toast("Provider OK", "ok"); }
          catch (e) { U.toast(e.message, "err"); }
        };
        del.onclick = () => {
          U.confirmDialog("Delete provider", p.name, async () => {
            try { await API.del(`/api/providers/${p.name}`); U.toast("Deleted", "ok"); listProviders(root); }
            catch (e) { U.toast(e.message, "err"); }
          });
        };
        td.append(test, del);
        return td;
      })(),
    })), ["Name", "Base URL", "Key", "Model", ""]));

    U.$("#mp-new").onclick = () => {
      const ed = U.el(`
        <div class="card">
          <h4>Add provider</h4>
          <div class="row" style="gap:12px;flex-wrap:wrap">
            <div><label>Name</label><input id="pe-name"></div>
            <div><label>Dialect</label>
              <select id="pe-dialect">
                <option value="openai-chat">openai-chat (streaming)</option>
                <option value="openai-responses">openai-responses</option>
                <option value="generic-openresponses">generic-openresponses</option>
                <option value="anthropic-messages">anthropic-messages (not implemented)</option>
                <option value="other">other (not implemented)</option>
              </select>
            </div>
          </div>
          <label>Base URL</label><input id="pe-url" placeholder="https://api.openai.com/v1">
          <label>API key</label><input id="pe-key" type="password">
          <label>Default model</label><input id="pe-model" placeholder="gpt-4o-mini">
          <div class="row" style="gap:10px;margin-top:12px">
            <button class="btn" id="pe-save">Save</button>
            <button class="btn ghost" id="pe-cancel">Cancel</button>
          </div>
        </div>`);
      ed.querySelector("#pe-cancel").onclick = () => ed.remove();
      ed.querySelector("#pe-save").onclick = async () => {
        const name = U.$("#pe-name").value.trim();
        if (!name) { U.toast("Name required", "err"); return; }
        try {
          await API.post("/api/providers", {
            name,
            dialect: U.$("#pe-dialect").value,
            baseURL: U.$("#pe-url").value.trim() || undefined,
            apiKey: U.$("#pe-key").value || undefined,
            model: U.$("#pe-model").value.trim() || undefined,
          });
          U.toast("Provider saved", "ok");
          listProviders(root);
        } catch (e) { U.toast(e.message, "err"); }
      };
      ed.style.display = "block";
      listEl.after(ed);
    };
  }

  async function listTools(root) {
    let tools = [];
    try { tools = await API.get("/api/tools"); } catch (e) { U.toast(e.message, "err"); }
    root.innerHTML = `<h3>Tools</h3><div class="muted" style="margin:6px 0 12px">Available to agents. Tools are discovered from MCP servers and built-ins.</div><div id="mt-list"></div>`;
    const listEl = U.$("#mt-list");
    if (!tools.length) { listEl.innerHTML = '<div class="muted">No tools found</div>'; }
    const tbl = confirmTable(tools.map((t) => {
      const enabled = t.enabled !== false;
      const td = document.createElement("td");
      const btn = U.el(`<button class="btn ghost sm">${enabled ? "Disable" : "Enable"}</button>`);
      btn.onclick = async () => {
        try { const r = await API.post(`/api/tools/${encodeURIComponent(t.server)}/${encodeURIComponent(t.name)}/toggle`, {}); U.toast(`${r.enabled !== false ? "Enabled" : "Disabled"}`, "ok"); listTools(root); }
        catch (e) { U.toast(e.message, "err"); }
      };
      td.appendChild(btn);
      return {
        cells: [U.esc(t.name), U.esc(t.description || ""), `<span class="badge ${enabled ? "ok" : ""}">${enabled ? "enabled" : "disabled"}</span>`, U.esc(t.server || "")],
        actions: td,
      };
    }), ["Name", "Description", "State", "Source", ""]);
    listEl.appendChild(tbl);
  }

  async function filesPage(root) {
    let files = [];
    try { files = await API.get("/api/files"); } catch (e) { U.toast(e.message, "err"); }
    root.innerHTML = `<div class="row spread"><h3>Files</h3>
      <div class="row" style="gap:8px">
        <input type="file" id="mf-input" multiple style="display:none">
        <button class="btn" id="mf-upload">+ Upload</button>
      </div></div>
      <div class="muted" style="margin:6px 0 12px">Files are served from the data directory and can be referenced by agents.</div>
      <div id="mf-list"></div>`;
    const listEl = U.$("#mf-list");
    if (!files.length) { listEl.innerHTML = '<div class="muted">No files</div>'; }
    listEl.appendChild(confirmTable(files.map((f) => ({
      cells: [U.esc(f.name), U.esc(f.size != null ? fmtSize(f.size) : "")],
      actions: (() => {
        const td = document.createElement("td");
        const dl = U.el('<button class="btn ghost sm">Download</button>');
        const del = U.el('<button class="btn ghost sm danger">Delete</button>');
        dl.onclick = () => { const a = document.createElement("a"); a.href = `/api/files/${encodeURIComponent(f.name)}`; a.download = f.name; a.click(); };
        del.onclick = () => {
          U.confirmDialog("Delete file", f.name, async () => {
            try { await API.del(`/api/files/${f.name}`); U.toast("Deleted", "ok"); filesPage(root); }
            catch (e) { U.toast(e.message, "err"); }
          });
        };
        td.append(dl, del);
        return td;
      })(),
    })), ["Name", "Size", ""]));
    U.$("#mf-upload").onclick = () => U.$("#mf-input").click();
    U.$("#mf-input").onchange = async (e) => {
      const f = e.target.files[0];
      if (!f) return;
      try { await API.upload("/api/files", f); U.toast("Uploaded", "ok"); filesPage(root); }
      catch (err) { U.toast(err.message, "err"); }
    };
  }

  function fmtSize(n) {
    if (n < 1024) return n + " B";
    if (n < 1048576) return (n / 1024).toFixed(1) + " KB";
    return (n / 1048576).toFixed(1) + " MB";
  }

  async function historyPage(root) {
    let convs = [];
    try { convs = await API.get("/api/conversations"); } catch (e) { U.toast(e.message, "err"); }
    root.innerHTML = `<h3>Conversation history</h3><div class="muted" style="margin:6px 0 12px">All chats on this deployment.</div><div id="mh-list"></div>`;
    const listEl = U.$("#mh-list");
    if (!convs.length) { listEl.innerHTML = '<div class="muted">No conversations yet</div>'; }
    listEl.appendChild(confirmTable(convs.map((c) => ({
      cells: [U.esc(c.title || "(untitled)"), c.id, U.esc(c.created_at || "")],
      actions: (() => {
        const td = document.createElement("td");
        const open = U.el('<button class="btn ghost sm">Open</button>');
        const del = U.el('<button class="btn ghost sm danger">Delete</button>');
        open.onclick = () => { window.location.hash = "chat/" + c.id; };
        del.onclick = () => {
          U.confirmDialog("Delete conversation", c.title, async () => {
            try { await API.del(`/api/conversations/${c.id}`); U.toast("Deleted", "ok"); historyPage(root); }
            catch (e) { U.toast(e.message, "err"); }
          });
        };
        td.append(open, del);
        return td;
      })(),
    })), ["Title", "ID", "Created", ""]));
  }

  async function logsPage(root) {
    root.innerHTML = `<div class="row spread"><h3>Logs</h3><button class="btn ghost sm" id="ml-refresh">↻ Refresh</button></div>
      <div id="ml-logs" class="card" style="font-family:var(--mono);font-size:12px;max-height:60vh;overflow:auto;white-space:pre-wrap"></div>`;
    const load = async () => {
      try {
        const logs = await API.get("/api/logs?lines=80");
        U.$("#ml-logs").textContent = (logs.lines || []).join("\n") || "(no logs)";
        U.$("#ml-logs").scrollTop = U.$("#ml-logs").scrollHeight;
      } catch (e) { U.toast(e.message, "err"); }
    };
    load();
    U.$("#ml-refresh").onclick = load;
    setInterval(() => { if (window.location.hash.startsWith("#logs")) load(); }, 8000);
  }

  async function settingsPage(root) {
    let settings = null;
    try { settings = await API.get("/api/settings"); } catch (e) { U.toast(e.message, "err"); }
    const theme = settings && settings.theme || "dark";
    const showTools = settings ? String(settings.showToolCalls) !== "0" : true;
    root.innerHTML = `<h3>Settings</h3>
      <div id="ms-card" class="card">
        <label>Theme</label>
        <select id="st-theme">
          <option value="dark" ${theme === "dark" ? "selected" : ""}>Dark</option>
          <option value="light" ${theme === "light" ? "selected" : ""}>Light</option>
        </select>
        <label style="margin-top:14px"><input type="checkbox" id="st-tools" ${showTools ? "checked" : ""}> Show tool calls in chat</label>
        <div class="row" style="gap:10px;margin-top:14px">
          <button class="btn" id="st-save">Save</button>
          <button class="btn ghost" id="st-logout">Log out</button>
        </div>
        <div class="muted" style="margin-top:14px;font-size:12px">ℹ️ Platform version: <span id="st-ver">…</span></div>
      </div>`;
    try { const v = await API.get("/api/version"); U.$("#st-ver").textContent = v.version || "?"; } catch (e) {}
    U.$("#st-save").onclick = async () => {
      try {
        await API.put("/api/settings", { theme: U.$("#st-theme").value, showToolCalls: U.$("#st-tools").checked ? "1" : "0" });
        document.documentElement.dataset.theme = U.$("#st-theme").value;
        U.toast("Settings saved", "ok");
      } catch (e) { U.toast(e.message, "err"); }
    };
    U.$("#st-logout").onclick = () => { API.logout(); window.location.hash = "login"; window.location.reload(); };
  }

  window.Manage = { listAgents, listMcp, listProviders, listTools, filesPage, historyPage, logsPage, settingsPage };
})();

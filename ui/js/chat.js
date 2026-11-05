/* Chat page */
(function () {
  const U = window.UI;

  function ChatPage() {
    this.convId = null;
    this.agent = "";
    this.provider = "";
    this.model = "";
    this.stream = null;
    this.sendBtn = null;
    this.stopBtn = null;
    this.input = null;
    this.scroll = null;
    this.listEl = null;
    this.typingEl = null;
  }

  ChatPage.prototype.render = function (root) {
    U.$$("#chat-root").forEach((e) => e.remove());
    root.innerHTML = `
      <div class="chat-layout" id="chat-root">
        <div class="chat-list">
          <div class="row spread" style="margin-bottom:10px">
            <strong>Conversations</strong>
            <button class="btn sm" id="chat-new">+ New</button>
          </div>
          <div id="chat-list-items" style="display:flex;flex-direction:column;gap:6px"></div>
        </div>
        <div class="chat-main">
          <div class="chat-scroll" id="chat-scroll"></div>
          <div class="row wrap" style="padding:0 14px 6px;gap:8px">
            <select id="chat-agent" style="width:auto;max-width:180px"><option value="">Agent: auto</option></select>
            <select id="chat-provider" style="width:auto;max-width:180px"><option value="">Provider…</option></select>
            <select id="chat-model" style="width:auto;max-width:180px"><option value="">Model…</option></select>
            <label class="muted" style="font-size:12px;margin:0"><input type="checkbox" id="chat-tools" checked> Tools</label>
          </div>
          <div class="composer">
            <textarea id="chat-input" rows="1" placeholder="Message… (Enter to send, Shift+Enter for newline)"></textarea>
            <button class="btn" id="chat-send">Send</button>
            <button class="btn ghost" id="chat-stop" style="display:none">Stop</button>
          </div>
        </div>
      </div>`;
    this.scroll = U.$("#chat-scroll");
    this.input = U.$("#chat-input");
    this.sendBtn = U.$("#chat-send");
    this.stopBtn = U.$("#chat-stop");
    this.listEl = U.$("#chat-list-items");

    this.loadSelects();
    this.loadList();

    U.$("#chat-new").onclick = () => { this.convId = null; this.setConvId(null); };
    U.$("#chat-send").onclick = () => this.send();
    U.$("#chat-stop").onclick = () => { if (this.stream) this.stream.abort(); };
    this.input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); this.send(); }
    });
    this.input.addEventListener("input", () => {
      this.input.style.height = "auto";
      this.input.style.height = Math.min(this.input.scrollHeight, 140) + "px";
    });
  };

  ChatPage.prototype.loadSelects = async function () {
    try {
      const [agents, providers] = await Promise.all([API.get("/api/config/agents"), API.get("/api/providers")]);
      const agSel = U.$("#chat-agent"), prSel = U.$("#chat-provider"), mdSel = U.$("#chat-model");
      agSel.innerHTML = '<option value="">Agent: auto</option>' + agents.map((a) => `<option value="${U.esc(a.name)}">${U.esc(a.title)}</option>`).join("");
      prSel.innerHTML = '<option value="">Provider…</option>' + providers.map((p) => `<option value="${U.esc(p.name)}">${U.esc(p.name)}</option>`).join("");
      agSel.onchange = () => {
        const ag = agents.find((a) => a.name === agSel.value);
        this.agent = agSel.value;
        if (ag) {
          if (ag.provider) { prSel.value = ag.provider; this.provider = ag.provider; }
          if (ag.model) { mdSel.value = ag.model; this.model = ag.model; }
        } else {
          this.provider = prSel.value; this.model = mdSel.value;
        }
      };
      prSel.onchange = () => { this.provider = prSel.value; };
      mdSel.onchange = () => { this.model = mdSel.value; };
    } catch (e) { U.toast(e.message, "err"); }
  };

  ChatPage.prototype.loadList = async function () {
    try {
      const convs = await API.get("/api/conversations");
      this.listEl.innerHTML = convs.map((c) => `
        <div class="row spread" data-id="${c.id}" style="padding:8px 10px;border-radius:10px;cursor:pointer;border:1px solid var(--border);background:var(--bg3)">
          <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${U.esc(c.title)}</span>
          <button class="btn ghost sm" data-del title="Delete">🗑</button>
        </div>`).join("") || '<div class="muted">No conversations yet</div>';
      this.listEl.querySelectorAll("[data-id]").forEach((row) => {
        row.onclick = (e) => {
          if (e.target.closest("[data-del]")) return;
          this.convId = Number(row.dataset.id);
          this.loadConversation(this.convId);
        };
        row.querySelector("[data-del]").onclick = async (e) => {
          e.stopPropagation();
          U.confirmDialog("Delete conversation", "This cannot be undone.", async () => {
            await API.del(`/api/conversations/${row.dataset.id}`);
            this.loadList();
          });
        };
      });
    } catch (e) { U.toast(e.message, "err"); }
  };

  ChatPage.prototype.loadConversation = async function (id) {
    try {
      const msgs = await API.get(`/api/conversations/${id}/messages`);
      this.scroll.innerHTML = "";
      this.setConvId(id);
      msgs.forEach((m) => this.appendMessage(m.role, m.content, m.tool_calls));
      this.scrollTop();
    } catch (e) { U.toast(e.message, "err"); }
  };

  ChatPage.prototype.setConvId = function (id) {
    this.convId = id;
    const titleEl = document.querySelector(".topbar h1");
    if (titleEl) titleEl.textContent = id ? `Chat #${id}` : "Chat";
  };

  ChatPage.prototype.scrollTop = function () {
    requestAnimationFrame(() => { this.scroll.scrollTop = this.scroll.scrollHeight; });
  };

  ChatPage.prototype.appendMessage = function (role, content, toolCalls) {
    if (role === "assistant" && toolCalls && Array.isArray(toolCalls)) {
      toolCalls.forEach((tc) => this.appendToolChip(tc.function.name, JSON.stringify(tc.function.arguments), null));
    }
    const div = document.createElement("div");
    div.className = "msg " + role;
    div.innerHTML = `<div class="md">${U.markdown(content || "")}</div>
      <button class="btn ghost sm copy" title="Copy">📋</button>`;
    div.querySelector(".copy").onclick = async () => {
      try { await navigator.clipboard.writeText(content || ""); U.toast("Copied", "ok"); }
      catch (e) { U.toast("Copy failed", "err"); }
    };
    this.scroll.appendChild(div);
  };

  ChatPage.prototype.appendToolChip = function (name, argsJson, resultText) {
    const chip = U.el(`
      <div class="toolchip">
        <div class="row spread"><span class="name">🛠 ${U.esc(name)}</span><span class="muted">${U.esc(argsJson || "{}")}</span></div>
        <div class="res"><pre class="code">${U.esc(resultText || "")}</pre></div>
      </div>`);
    chip.onclick = () => chip.classList.toggle("open");
    if (resultText) chip.querySelector(".res").style.display = "block";
    this.scroll.appendChild(chip);
  };

  ChatPage.prototype.startTyping = function () {
    this.typingEl = U.el('<div class="typing"><i></i><i></i><i></i></div>');
    this.scroll.appendChild(this.typingEl);
    this.scrollTop();
  };

  ChatPage.prototype.stopTyping = function () {
    if (this.typingEl) { this.typingEl.remove(); this.typingEl = null; }
  };

  ChatPage.prototype.send = async function () {
    const msg = this.input.value.trim();
    if (!msg) return;
    const provider = this.provider || U.$("#chat-provider").value;
    const model = this.model || U.$("#chat-model").value;
    this.input.value = "";
    this.appendMessage("user", msg);
    this.startTyping();
    this.sendBtn.disabled = true;
    this.stopBtn.style.display = "";
    let hadText = false;

    const payload = { message: msg, agent: this.agent || undefined, provider: provider || undefined, model: model || undefined };
    if (this.convId) payload.conversation_id = this.convId;
    payload.tools = U.$("#chat-tools").checked;

    this.stream = streamChat(payload, {
      onEvent: (ev, d) => {
        if (ev === "meta" && d && d.conversation_id && !this.convId) {
          this.convId = d.conversation_id;
          this.setConvId(this.convId);
        }
        if (ev === "delta" && d && d.text) {
          if (!hadText) { this.stopTyping(); hadText = true; }
          const last = this.scroll.lastElementChild;
          if (!last || !last.classList.contains("msg") || !last.classList.contains("assistant") || last.dataset.live !== "1") {
            const div = document.createElement("div");
            div.className = "msg assistant";
            div.dataset.live = "1";
            div.innerHTML = '<div class="md"></div><button class="btn ghost sm copy" title="Copy">📋</button>';
            this.scroll.appendChild(div);
          }
          const live = this.scroll.lastElementChild;
          live.querySelector(".md").innerHTML = U.markdown(live.querySelector(".md").textContent + d.text);
          this.scrollTop();
        } else if (ev === "tool_start" && d && d.name) {
          this.stopTyping();
          this.appendToolChip(d.name, JSON.stringify(d.args || {}), null);
          this.scrollTop();
        } else if (ev === "tool_end" && d && d.name) {
          const chips = this.scroll.querySelectorAll(".toolchip");
          const lastChip = chips[chips.length - 1];
          const content = d.result && d.result.result ? (d.result.result.content || "") : "";
          if (lastChip && lastChip.querySelector(".name").textContent.includes(d.name)) {
            lastChip.querySelector(".res pre").textContent = content || "(empty result)";
            lastChip.classList.add("open");
          }
          this.scrollTop();
        }
      },
      onFinish: (ev) => {
        this.stopTyping();
        this.sendBtn.disabled = false;
        this.stopBtn.style.display = "none";
        if (ev === "error") U.toast("Chat error", "err");
        const last = this.scroll.lastElementChild;
        if (last && last.dataset && last.dataset.live === "1") {
          delete last.dataset.live;
          const btn = last.querySelector(".copy");
          if (btn) btn.onclick = () => navigator.clipboard.writeText(last.querySelector(".md").textContent);
        }
        this.loadList();
        this.stream = null;
      },
      error: (e) => {
        this.stopTyping();
        this.sendBtn.disabled = false;
        this.stopBtn.style.display = "none";
        U.toast(e.message, "err");
        this.stream = null;
      },
    });
  };

  window.ChatPage = ChatPage;
})();

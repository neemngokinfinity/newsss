/* UI helpers */
(function () {
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
  const el = (html) => { const t = document.createElement("template"); t.innerHTML = html.trim(); return t.content.firstElementChild; };
  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

  function toast(msg, kind) {
    const r = $("#toast-root");
    const t = el(`<div class="toast ${kind || ""}">${esc(msg)}</div>`);
    r.appendChild(t);
    setTimeout(() => { t.style.opacity = "0"; t.style.transition = "opacity .3s"; }, 2800);
    setTimeout(() => t.remove(), 3200);
  }

  function modal(title, bodyHtml, onMount) {
    const backdrop = el(`<div class="modal-backdrop"><div class="modal"><div class="row spread"><h3 style="margin:0">${esc(title)}</h3><button class="btn ghost sm" data-close>✕</button></div><div class="modal-body"></div></div></div>`);
    const close = () => backdrop.remove();
    backdrop.querySelector("[data-close]").onclick = close;
    backdrop.onclick = (e) => { if (e.target === backdrop) close(); };
    backdrop.querySelector(".modal-body").innerHTML = bodyHtml;
    document.body.appendChild(backdrop);
    if (onMount) onMount(backdrop.querySelector(".modal-body"), close);
    return { backdrop, close };
  }

  function confirmDialog(title, text, onYes) {
    modal(title, `<p>${esc(text)}</p><div class="row" style="justify-content:flex-end;margin-top:16px"><button class="btn ghost" data-no>Cancel</button> <button class="btn danger" data-yes>Confirm</button></div>`,
      (body, close) => {
        body.querySelector("[data-no]").onclick = close;
        body.querySelector("[data-yes]").onclick = () => { close(); onYes(); };
      });
  }

  function markdown(text) {
    if (window.marked) {
      try { return window.marked.parse(String(text || ""), { breaks: true }); } catch (e) {}
    }
    return esc(text).replace(/\n/g, "<br>");
  }

  function fmtBytes(n) {
    if (n == null) return "—";
    const u = ["B", "KB", "MB", "GB"];
    let i = 0;
    while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
    return n.toFixed(i ? 1 : 0) + " " + u[i];
  }

  function field(label, innerHtml) {
    return `<label>${esc(label)}${innerHtml}</label>`;
  }

  function jsonArea(value) {
    return `<textarea class="mono" rows="5" placeholder='{"key": "value"}'>${esc(value || "")}</textarea>`;
  }

  function parseJsonOr(text) {
    if (!text || !text.trim()) return {};
    try { return JSON.parse(text); } catch (e) { throw new Error("Invalid JSON"); }
  }

  window.UI = { $, $$, el, esc, toast, modal, confirmDialog, markdown, fmtBytes, field, jsonArea, parseJsonOr };
})();

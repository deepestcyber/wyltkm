// WYLTKM web app: live preview, pickers, upload and theme switch.
// The page works without this script as a plain form.
"use strict";

document.documentElement.classList.add("js");

function debounce(fn, ms) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

function el(tag, attrs = {}, children = []) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === false || v === null || v === undefined) continue;
    if (k === "text") e.textContent = v; else e.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children) e.append(c);
  return e;
}

function iconUrl(name, colour) {
  return "/icons/" + name.replace(":", "/") + ".svg?colour=" + encodeURIComponent(colour);
}

// ---------------------------------------------------------------- theme
function setupTheme() {
  const button = document.getElementById("theme");
  if (!button) return;
  const label = button.querySelector(".label");
  const names = { system: "System", dark: "Dark", light: "Light" };
  const order = ["system", "dark", "light"];
  let current = document.documentElement.dataset.theme || "system";
  const show = () => {
    label.textContent = names[current];
    button.title = current === "system" ? "Theme: follows the system" : "Theme: " + names[current].toLowerCase();
  };
  button.hidden = false;
  show();
  button.addEventListener("click", () => {
    current = order[(order.indexOf(current) + 1) % order.length];
    if (current === "system") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = current;
    try {
      if (current === "system") localStorage.removeItem("wyltkm-theme");
      else localStorage.setItem("wyltkm-theme", current);
    } catch (e) { /* storage blocked: the choice lasts for this page */ }
    show();
  });
}

// ----------------------------------------------------------------- form
function setupForm() {
  const form = document.getElementById("qr");
  if (!form) return;
  const $ = (id) => document.getElementById(id);
  const sheet = $("sheet"), img = $("preview"), dims = $("dims"), error = $("error");
  const warnings = $("warnings"), licences = $("licences");
  const dlSvg = $("dl-svg"), dlPng = $("dl-png"), copy = $("copy-link");
  const fileInput = $("icon_file"), fileClear = $("icon_file_clear"), iconName = $("icon-name");
  const icons = $("icons"), schemes = $("schemes");
  const LOCAL = new Set(["icon_q", "icon_source", "icon_file"]);
  let designs = null;
  let objectUrl = null;
  let seq = 0;

  function params() {
    const p = new URLSearchParams();
    for (const [k, v] of new FormData(form)) {
      if (LOCAL.has(k) || v === "") continue;
      if (k === "side_font" && form.elements.side.value !== "1") continue;
      p.append(k, v);
    }
    return p;
  }

  function uploaded() { return fileInput && fileInput.files.length ? fileInput.files[0] : null; }

  function postBody(p, extra = {}) {
    const fd = new FormData();
    for (const [k, v] of p) if (k !== "icon") fd.append(k, v);
    for (const [k, v] of Object.entries(extra)) fd.append(k, v);
    fd.append("icon_file", uploaded());
    return fd;
  }

  function showError(text) {
    error.textContent = text;
    error.hidden = false;
    sheet.hidden = true;
  }

  function showInfo(info) {
    error.hidden = true;
    sheet.hidden = false;
    img.width = info.width;
    dims.textContent = `${info.width} × ${Math.round(info.height)} px · ${info.modules} modules`;
    warnings.replaceChildren(...info.warnings.map((w) => el("li", { text: w })));
    licences.replaceChildren(...info.licences.map((lic) => {
      const name = lic.url ? el("a", { href: lic.url, text: lic.name }) : lic.name;
      const p = el("p", {}, [lic.part + ": ", name, lic.holder ? ", " + lic.holder : ""]);
      if (lic.requires_attribution) {
        p.append(el("br"), el("span", { class: "attribution" },
          ["Attribution required: ", el("code", { text: lic.attribution })]));
      }
      return p;
    }));
  }

  async function update() {
    const mine = ++seq;
    const p = params();
    history.replaceState(null, "", "/?" + p.toString());
    sheet.classList.add("loading");
    try {
      let info;
      if (uploaded()) {
        const [imgResp, infoResp] = await Promise.all([
          fetch("/render.svg", { method: "POST", body: postBody(p) }),
          fetch("/api/render-info", { method: "POST", body: postBody(p) }),
        ]);
        if (mine !== seq) return;
        if (!infoResp.ok) return showError(await infoResp.text());
        info = await infoResp.json();
        if (objectUrl) URL.revokeObjectURL(objectUrl);
        objectUrl = URL.createObjectURL(await imgResp.blob());
        img.src = objectUrl;
      } else {
        const resp = await fetch("/api/render-info?" + p);
        if (mine !== seq) return;
        if (!resp.ok) return showError(await resp.text());
        info = await resp.json();
        img.src = "/render.svg?" + p;
      }
      showInfo(info);
      dlSvg.href = "/render.svg?" + p + "&download=1";
      dlPng.href = "/render.png?" + p + "&download=1";
    } catch (e) {
      if (mine === seq) showError("The preview could not be loaded.");
    } finally {
      if (mine === seq) sheet.classList.remove("loading");
    }
  }
  const later = debounce(update, 250);

  // downloads with an uploaded icon cannot be links: post the form instead
  async function download(event, fmt) {
    if (!uploaded()) return;
    event.preventDefault();
    const resp = await fetch("/render." + fmt, { method: "POST", body: postBody(params(), { download: "1" }) });
    if (!resp.ok) return showError(await resp.text());
    const name = /filename="([^"]+)"/.exec(resp.headers.get("Content-Disposition") || "");
    const url = URL.createObjectURL(await resp.blob());
    const a = el("a", { href: url, download: name ? name[1] : "wyltkm-qr." + fmt });
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }
  dlSvg.addEventListener("click", (e) => download(e, "svg"));
  dlPng.addEventListener("click", (e) => download(e, "png"));

  copy.hidden = !navigator.clipboard;
  copy.addEventListener("click", async () => {
    await navigator.clipboard.writeText(location.origin + "/?" + params());
    copy.textContent = uploaded() ? "Copied, without the uploaded icon" : "Copied";
    setTimeout(() => { copy.textContent = "Copy link"; }, 2000);
  });

  // --- designs and colour schemes
  async function loadDesigns() {
    if (!designs) designs = await (await fetch("/api/designs")).json();
    return designs;
  }

  function currentDesign() {
    const name = form.elements.design.value;
    return designs ? designs.find((d) => d.name === name) : null;
  }

  function iconColour() {
    const d = currentDesign();
    if (!d) return getComputedStyle(icons).getPropertyValue("--icon-colour").trim() || "#85858b";
    const s = d.schemes.find((x) => x.name === (form.elements.scheme && form.elements.scheme.value));
    return (s ? s.colours : d.colours).icon;
  }

  function recolourIcons() {
    const colour = iconColour();
    for (const image of icons.querySelectorAll("img")) {
      image.src = iconUrl(image.alt, colour);
    }
  }

  async function designChanged() {
    await loadDesigns();
    const d = currentDesign();
    if (!d) return;
    schemes.replaceChildren(...d.schemes.map((s) => el("label", { class: "chip" }, [
      el("input", { type: "radio", name: "scheme", value: s.name, checked: s.name === d.default_scheme }),
      el("span", {}, [
        el("i", { class: "dot", style: `background: ${s.colours.finder_ring}; box-shadow: 0 0 0 2px ${s.colours.background}` }),
        s.title,
      ]),
    ])));
    schemes.hidden = d.schemes.length === 0;
    recolourIcons();
    describeIcon();
  }

  // --- icons
  function describeIcon() {
    if (uploaded()) { iconName.textContent = "uploaded: " + uploaded().name; return; }
    const v = form.elements.icon.value;
    const d = currentDesign();
    let fallback = d ? d.default_icon : "design default";
    if (d && form.elements.scheme) {
      const s = d.schemes.find((x) => x.name === form.elements.scheme.value);
      if (s) fallback = s.icon;
    }
    iconName.textContent = v || fallback;
  }

  const search = debounce(async () => {
    const q = $("icon_q").value.trim();
    const source = $("icon_source").value;
    const chosen = form.elements.icon.value;
    const keep = [...icons.querySelectorAll("label.icon.text")];
    if (!q) {
      const current = chosen && chosen !== "none" ? [iconChoice(chosen, "", true)] : [];
      icons.replaceChildren(...keep, ...current);
      return;
    }
    const hits = await (await fetch(`/api/icons?q=${encodeURIComponent(q)}&source=${encodeURIComponent(source)}&limit=64`)).json();
    const items = hits.map((h) => iconChoice(h.name, h.label, h.name === chosen));
    if (chosen && chosen !== "none" && !hits.some((h) => h.name === chosen)) items.unshift(iconChoice(chosen, "", true));
    icons.replaceChildren(...keep, ...items);
  }, 200);

  function iconChoice(name, label, checked) {
    return el("label", { class: "icon", title: label ? `${name} · ${label}` : name }, [
      el("input", { type: "radio", name: "icon", value: name, checked }),
      el("img", { src: iconUrl(name, iconColour()), alt: name, width: 20, height: 20, loading: "lazy" }),
    ]);
  }

  function fileChanged() {
    fileClear.hidden = !uploaded();
    describeIcon();
    later();
  }
  fileInput.addEventListener("change", fileChanged);
  fileClear.addEventListener("click", () => { fileInput.value = ""; fileChanged(); });

  // --- side text
  let fontsLoaded = false;
  async function sideChanged() {
    const on = form.elements.side.value === "1";
    $("side-font-row").hidden = !on;
    if (on && !fontsLoaded) {
      fontsLoaded = true;
      const fonts = await (await fetch("/api/fonts")).json();
      $("fonts").replaceChildren(...fonts.map((f) => el("option", { value: f.name })));
    }
  }

  // --- wiring
  form.addEventListener("submit", (e) => { e.preventDefault(); update(); });
  form.addEventListener("input", (e) => {
    const name = e.target.name;
    if (name === "icon_q" || name === "icon_source") return search();
    if (name === "icon_file") return;
    if (name === "design") return designChanged().then(later);
    if (name === "scheme") { recolourIcons(); describeIcon(); }
    if (name === "icon") describeIcon();
    if (name === "side") sideChanged();
    later();
  });
  form.addEventListener("change", (e) => { if (e.target.name === "icon_source") search(); });
  loadDesigns().then(describeIcon);
}

setupTheme();
setupForm();

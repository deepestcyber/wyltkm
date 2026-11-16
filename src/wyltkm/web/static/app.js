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
  return "/icon/" + name.replace(":", "/") + ".svg?colour=" + encodeURIComponent(colour);
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
  const icons = $("icons"), schemes = $("schemes"), grid = $("browse-grid");
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

  function designColours() {
    const d = currentDesign();
    if (!d) return null;
    const s = d.schemes.find((x) => x.name === (form.elements.scheme && form.elements.scheme.value));
    return (s ? s.colours : d.colours);
  }

  function iconColour() {
    const c = designColours();
    return c ? c.icon : getComputedStyle(icons).getPropertyValue("--icon-colour").trim() || "#85858b";
  }

  // icon tiles show the design's background, so each icon looks as in the code
  function paintTiles() {
    const c = designColours();
    if (!c) return;
    for (const box of [icons, grid, $("browse-pick-img")]) {
      box.style.setProperty("--icon-colour", c.icon);
      box.style.setProperty("--tile-bg", c.background);
    }
  }

  function recolourIcons() {
    const colour = iconColour();
    paintTiles();
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

  // --- icon browser (dialog); the "Browse" link is the page without JS
  const dialog = $("browser");
  const browse = {
    q: "", source: "", folder: "", offset: 0, total: 0, loading: false, chosen: null,
    sources: null, seq: 0,
  };
  const more = $("browse-more"), main = $("browse-main");

  function chooseInForm(name) {
    let input = icons.querySelector(`input[name=icon][value="${CSS.escape(name)}"]`);
    if (!input) {
      const label = iconChoice(name, "", true);
      const keep = icons.querySelectorAll("label.icon.text");
      keep[keep.length - 1].after(label);
      input = label.querySelector("input");
    }
    input.checked = true;
    if (uploaded()) { fileInput.value = ""; fileClear.hidden = true; }
    describeIcon();
    later();
  }

  function sourceInfo(name) {
    return browse.sources ? browse.sources.find((s) => s.name === name) : null;
  }

  function renderSources() {
    const total = browse.sources.reduce((n, s) => n + s.count, 0);
    const chip = (name, label, count) => {
      const b = el("button", { type: "button", class: "chip-link" + (browse.source === name ? " on" : "") },
        [label, " ", el("span", { class: "mono", text: String(count) })]);
      b.addEventListener("click", () => { browse.source = name; browse.folder = ""; renderSources(); reload(); });
      return b;
    };
    $("browse-sources").replaceChildren(chip("", "All", total),
      ...browse.sources.map((s) => chip(s.name, s.name, s.count)));
    const src = sourceInfo(browse.source);
    const folders = src ? src.folders.filter((f) => f.name) : [];
    const folderButton = (name, label, count) => {
      const b = el("button", { type: "button", class: browse.folder === name ? "on" : "" },
        [label, count === null ? "" : el("span", { class: "mono", text: String(count) })]);
      b.addEventListener("click", () => { browse.folder = name; renderSources(); reload(); });
      return b;
    };
    $("browse-folders").replaceChildren(...(src
      ? [folderButton("", "All folders", null), ...folders.map((f) => folderButton(f.name, f.name, f.count))]
      : [el("p", { class: "hint", text: "Choose a source to see its folders." })]));
    $("browse-folders").hidden = !!src && folders.length === 0;
  }

  async function loadPage() {
    if (browse.loading || (browse.offset > 0 && browse.offset >= browse.total)) return;
    browse.loading = true;
    const mine = browse.seq;
    const p = new URLSearchParams({ q: browse.q, source: browse.source, folder: browse.folder,
      offset: browse.offset, limit: 120 });
    try {
      const data = await (await fetch("/api/icons/browse?" + p)).json();
      if (mine !== browse.seq) return;
      browse.total = data.total;
      browse.offset += data.hits.length;
      $("browse-count").textContent = `${data.total} icons`;
      const colour = iconColour();
      grid.append(...data.hits.map((h) => {
        const b = el("button", { type: "button", class: "icon" + (h.name === browse.chosen ? " on" : ""),
          title: h.label ? `${h.name} · ${h.label}` : h.name, role: "option", "data-name": h.name,
          "data-label": h.label }, [el("img", { src: iconUrl(h.name, colour), alt: h.name, width: 24,
          height: 24, loading: "lazy" })]);
        return b;
      }));
    } finally {
      browse.loading = false;
    }
    if (mine === browse.seq && nearEnd()) loadPage();
  }

  // load more when the end of the grid comes within 400 px of the view
  function nearEnd() {
    return more.getBoundingClientRect().top < main.getBoundingClientRect().bottom + 400;
  }

  function reload() {
    browse.seq++;
    browse.offset = 0;
    browse.total = 0;
    browse.loading = false;
    grid.replaceChildren();
    main.scrollTop = 0;
    loadPage();
  }

  function pick(button) {
    for (const b of grid.querySelectorAll(".icon.on")) b.classList.remove("on");
    button.classList.add("on");
    browse.chosen = button.dataset.name;
    const name = browse.chosen;
    const src = sourceInfo(name.split(":")[0]);
    $("browse-pick-img").replaceChildren(el("img", { src: iconUrl(name, iconColour()), alt: "" }));
    $("browse-pick-name").textContent = name;
    $("browse-pick-meta").textContent = [button.dataset.label,
      src ? `${src.title}, ${src.licence.name}${src.licence.requires_attribution ? ", attribution required" : ""}` : ""]
      .filter(Boolean).join(" · ");
    $("browse-use").disabled = false;
  }

  function use() {
    if (!browse.chosen) return;
    chooseInForm(browse.chosen);
    dialog.close();
  }

  grid.addEventListener("click", (e) => { const b = e.target.closest(".icon"); if (b) pick(b); });
  grid.addEventListener("dblclick", (e) => { const b = e.target.closest(".icon"); if (b) { pick(b); use(); } });
  grid.addEventListener("keydown", (e) => {
    const b = e.target.closest(".icon");
    if (!b) return;
    if (e.key === "Enter") { e.preventDefault(); pick(b); use(); }
    const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
    if (step) {
      e.preventDefault();
      const next = step > 0 ? b.nextElementSibling : b.previousElementSibling;
      if (next) { next.focus(); pick(next); }
    }
  });
  main.addEventListener("scroll", () => { if (nearEnd()) loadPage(); }, { passive: true });
  $("browse-q").addEventListener("input", debounce(() => { browse.q = $("browse-q").value.trim(); reload(); }, 200));
  $("browse-use").addEventListener("click", use);
  $("browse-cancel").addEventListener("click", () => dialog.close());
  $("browse-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });

  $("browse-open").addEventListener("click", async (e) => {
    if (typeof dialog.showModal !== "function") return; // old browser: use the page
    e.preventDefault();
    if (!browse.sources) browse.sources = await (await fetch("/api/icon-sources")).json();
    const current = form.elements.icon.value;
    browse.chosen = current && current !== "none" ? current : null;
    $("browse-use").disabled = !browse.chosen;
    $("browse-pick-img").replaceChildren();
    $("browse-pick-name").textContent = browse.chosen || "No icon chosen";
    $("browse-pick-meta").textContent = "";
    browse.q = $("icon_q").value.trim();
    browse.source = $("icon_source").value;
    browse.folder = "";
    $("browse-q").value = browse.q;
    renderSources();
    paintTiles();
    dialog.showModal();
    reload();
    $("browse-q").focus();
  });

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

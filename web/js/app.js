// ============================================================
// Vault PAU — aplicación de una sola página, sin frameworks.
// Router muy simple basado en location.hash.
// ============================================================

let DATA = null;
let STATS = null;

const SUBJECT_META = {
  matematicas_ii: { label: "Matemáticas II", desc: "Álgebra, análisis, geometría, probabilidad" },
  bioloxia: { label: "Biología", desc: "Bioquímica, genética, fisiología, ecología" },
  fisica: { label: "Física", desc: "Interacción gravitatoria, electromagnetismo, ondas, física moderna" },
  quimica: { label: "Química", desc: "Reacciones, enlace, estructura de la materia, orgánica" },
  historiaespana: { label: "Historia de España", desc: "De los Reyes Católicos a la España actual" },
  historiafilosofia: { label: "Historia da Filosofía", desc: "De Platón a Simone de Beauvoir" },
};

function normalize(str) {
  return (str || "")
    .toString()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");
}

function escapeHtml(str) {
  return (str || "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

// -------------------- carga de datos --------------------

async function loadData() {
  // cache: "no-store" + parámetro de versión en la URL para evitar que el
  // navegador (o un CDN intermedio) sirva una copia vieja de los datos
  // después de recompilar el vault y volver a desplegar.
  const res = await fetch("data/preguntas.json?v=" + Date.now(), { cache: "no-store" });
  DATA = await res.json();
  const res2 = await fetch("data/estadisticas.json?v=" + Date.now(), { cache: "no-store" });
  STATS = await res2.json();
}

// -------------------- router --------------------

function parseHash() {
  const raw = location.hash.slice(1) || "/";
  const [path, query] = raw.split("?");
  const segments = path.split("/").filter(Boolean);
  const params = new URLSearchParams(query || "");
  return { segments, params };
}

function navigate(hash) {
  location.hash = hash;
}

function render() {
  const { segments, params } = parseHash();
  const main = document.getElementById("main");
  const nav = document.getElementById("topbar-nav");

  if (segments.length === 0) {
    nav.innerHTML = "";
    renderPortada(main);
  } else if (segments[0] === "materias") {
    nav.innerHTML = `<a href="#/">Portada</a><a href="#/estadisticas">Estadísticas</a>`;
    renderSelector(main);
  } else if (segments[0] === "materia" && segments[1]) {
    nav.innerHTML = `<a href="#/">Portada</a><a href="#/materias">Asignaturas</a><a href="#/estadisticas">Estadísticas</a>`;
    renderLista(main, segments[1], params);
  } else if (segments[0] === "pregunta" && segments[1]) {
    nav.innerHTML = `<a href="#/">Portada</a><a href="#/materias">Asignaturas</a><a href="#/estadisticas">Estadísticas</a>`;
    renderDetalle(main, decodeURIComponent(segments[1]));
  } else if (segments[0] === "estadisticas") {
    nav.innerHTML = `<a href="#/">Portada</a><a href="#/materias">Asignaturas</a>`;
    renderEstadisticas(main);
  } else {
    nav.innerHTML = "";
    renderPortada(main);
  }

  window.scrollTo(0, 0);
}

// -------------------- vista: portada --------------------

function renderPortada(main) {
  const total = DATA.total_preguntas;
  const nAsignaturas = DATA.asignaturas.length;
  const rango = `${DATA.anio_min}–${DATA.anio_max}`;

  main.innerHTML = `
    <section class="hero">
      <p class="hero-kicker">Exámenes oficiales CIUG · Galicia</p>
      <h1>Toda la ABAU/PAU, troceada y buscable</h1>
      <p>Preguntas reales de exámenes oficiales, organizadas por asignatura, tema, año y convocatoria.</p>

      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-number">${total}</div>
          <div class="stat-label">Preguntas</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${nAsignaturas}</div>
          <div class="stat-label">Asignaturas</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${rango}</div>
          <div class="stat-label">Años cubiertos</div>
        </div>
      </div>

      <a class="btn-primary" href="#/materias">Entrar al vault →</a>
    </section>
  `;
}

// -------------------- vista: estadísticas --------------------

function renderEstadisticas(main) {
  const subjects = Object.keys(SUBJECT_META).filter((s) => STATS.por_asignatura[s]);

  main.innerHTML = `
    <h1 class="page-title" style="text-align:left; margin-bottom: 8px;">Qué cae más</h1>
    <p class="page-subtitle" style="text-align:left; margin-bottom: 12px;">
      Frecuencia de cada tema en las preguntas de examen, ${STATS.anio_min}–${STATS.anio_max}.
    </p>
    <div class="notice-box">
      Los años ${STATS.anio_min}–2019 son solo estadística (clasificados automáticamente a partir
      del texto original del examen): no están trozeados como preguntas navegables en el vault,
      solo cuentan aquí para calcular la frecuencia de cada tema. 2020–2026 sí están en el vault.
      Una pregunta puede contar en más de un tema si el examen la relaciona con varios bloques —
      por eso los porcentajes de una asignatura no tienen por qué sumar 100%.
    </div>
    <div class="stats-grid">
      ${subjects.map((slug) => renderStatsCard(slug)).join("")}
    </div>
  `;
}

function renderStatsCard(slug) {
  const meta = SUBJECT_META[slug];
  const info = STATS.por_asignatura[slug];
  const maxPct = Math.max(...info.temas.map((t) => t.pct_preguntas), 1);

  const rows = info.temas
    .map(
      (t) => `
      <div class="stat-bar-row">
        <div class="stat-bar-label">${escapeHtml(t.tema)}</div>
        <div class="stat-bar-track">
          <div class="stat-bar-fill" style="width:${(100 * t.pct_preguntas) / maxPct}%"></div>
        </div>
        <div class="stat-bar-value">${t.pct_preguntas}% <span class="stat-bar-n">(${t.n})</span></div>
      </div>`
    )
    .join("");

  return `
    <div class="stats-card">
      <h2>${meta.label}</h2>
      <p class="stats-card-meta">${info.total_preguntas} preguntas contabilizadas</p>
      ${rows}
    </div>
  `;
}

// -------------------- vista: selector de asignatura --------------------

function renderSelector(main) {
  const counts = {};
  for (const p of DATA.preguntas) {
    counts[p.asignatura_slug] = (counts[p.asignatura_slug] || 0) + 1;
  }

  const slugs = Object.keys(SUBJECT_META).filter((s) => counts[s]);

  main.innerHTML = `
    <h1 class="page-title">Elige una asignatura</h1>
    <p class="page-subtitle">Cada una con sus propios filtros de tema, año y convocatoria.</p>
    <div class="subject-grid">
      ${slugs
        .map((slug) => {
          const meta = SUBJECT_META[slug];
          return `
          <a class="subject-card" href="#/materia/${slug}">
            <h2>${meta.label}</h2>
            <p class="subject-meta">${counts[slug]} preguntas · ${meta.desc}</p>
          </a>`;
        })
        .join("")}
    </div>
  `;
}

// -------------------- vista: lista con filtros --------------------

function renderLista(main, slug, initialParams) {
  const meta = SUBJECT_META[slug] || { label: slug };
  const preguntas = DATA.preguntas.filter((p) => p.asignatura_slug === slug);

  const temas = [...new Set(preguntas.flatMap((p) => p.tema || []))].sort();
  const anios = [...new Set(preguntas.map((p) => p.anio))].sort();
  const hayVacios = preguntas.some((p) => !p.tema || p.tema.length === 0);

  main.innerHTML = `
    <p class="breadcrumb"><a href="#/materias">Asignaturas</a> / ${meta.label}</p>
    <h1 class="page-title" style="text-align:left; margin-bottom: 24px;">${meta.label}</h1>

    <div class="filters-bar">
      <div>
        <label for="f-buscar">Buscar en el enunciado</label>
        <input type="text" id="f-buscar" placeholder="Texto libre…" />
      </div>
      <div>
        <label for="f-tema">Tema</label>
        <select id="f-tema">
          <option value="">Todos los temas</option>
          ${temas.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join("")}
          ${hayVacios ? `<option value="__sin_tema__">Sin clasificar</option>` : ""}
        </select>
      </div>
      <div>
        <label for="f-anio">Año</label>
        <select id="f-anio">
          <option value="">Todos los años</option>
          ${anios.map((a) => `<option value="${a}">${a}</option>`).join("")}
        </select>
      </div>
      <div>
        <label for="f-conv">Convocatoria</label>
        <select id="f-conv">
          <option value="">Todas</option>
          <option value="ordinaria">Ordinaria</option>
          <option value="extraordinaria">Extraordinaria</option>
        </select>
      </div>
    </div>

    <p class="results-count" id="results-count"></p>
    <div class="question-list" id="question-list"></div>
  `;

  const buscarEl = document.getElementById("f-buscar");
  const temaEl = document.getElementById("f-tema");
  const anioEl = document.getElementById("f-anio");
  const convEl = document.getElementById("f-conv");

  // restaurar filtros desde la URL
  if (initialParams.get("q")) buscarEl.value = initialParams.get("q");
  if (initialParams.get("tema")) temaEl.value = initialParams.get("tema");
  if (initialParams.get("anio")) anioEl.value = initialParams.get("anio");
  if (initialParams.get("conv")) convEl.value = initialParams.get("conv");

  function applyFilters() {
    const q = normalize(buscarEl.value.trim());
    const tema = temaEl.value;
    const anio = anioEl.value;
    const conv = convEl.value;

    const filtered = preguntas.filter((p) => {
      const pTemas = p.tema || [];
      if (tema === "__sin_tema__" && pTemas.length) return false;
      if (tema && tema !== "__sin_tema__" && !pTemas.includes(tema)) return false;
      if (anio && String(p.anio) !== anio) return false;
      if (conv && p.convocatoria !== conv) return false;
      if (q) {
        const haystack = normalize(
          p.enunciado + " " + (p.apartados || []).join(" ") + " " + pTemas.join(" ")
        );
        if (!haystack.includes(q)) return false;
      }
      return true;
    });

    renderQuestionList(filtered);

    // sincroniza la URL sin disparar un evento hashchange ni ensuciar el historial
    const newParams = new URLSearchParams();
    if (q) newParams.set("q", buscarEl.value.trim());
    if (tema) newParams.set("tema", tema);
    if (anio) newParams.set("anio", anio);
    if (conv) newParams.set("conv", conv);
    const qs = newParams.toString();
    const newHash = `#/materia/${slug}${qs ? "?" + qs : ""}`;
    history.replaceState(null, "", newHash);
  }

  buscarEl.addEventListener("input", applyFilters);
  temaEl.addEventListener("change", applyFilters);
  anioEl.addEventListener("change", applyFilters);
  convEl.addEventListener("change", applyFilters);

  applyFilters();
}

function renderQuestionList(preguntas) {
  const countEl = document.getElementById("results-count");
  const listEl = document.getElementById("question-list");

  countEl.textContent = `${preguntas.length} pregunta${preguntas.length === 1 ? "" : "s"}`;

  if (preguntas.length === 0) {
    listEl.innerHTML = `<div class="empty-state">Ninguna pregunta coincide con estos filtros.</div>`;
    return;
  }

  const sorted = [...preguntas].sort((a, b) => {
    if (a.anio !== b.anio) return b.anio - a.anio;
    if (a.convocatoria !== b.convocatoria) return a.convocatoria.localeCompare(b.convocatoria);
    return (a.numero_pregunta || 0) - (b.numero_pregunta || 0);
  });

  listEl.innerHTML = sorted
    .map((p) => {
      const snippet = escapeHtml(p.enunciado.slice(0, 180).replace(/\s+/g, " "));
      const temaTags = (p.tema && p.tema.length)
        ? p.tema.map((t) => `<span class="tag tag-tema">${escapeHtml(t)}</span>`).join("")
        : `<span class="tag tag-sin-tema">Sin clasificar</span>`;
      return `
      <a class="question-card" href="#/pregunta/${encodeURIComponent(p.id)}">
        <div class="question-card-head">
          <span class="question-card-title">${p.anio} · ${p.convocatoria} · Pregunta ${p.numero_pregunta ?? "?"}</span>
          <span class="tag-row">
            ${temaTags}
            <span class="tag">${escapeHtml(p.puntuacion || "")}</span>
          </span>
        </div>
        <p class="question-card-snippet">${snippet}…</p>
      </a>`;
    })
    .join("");
}

// -------------------- vista: detalle de pregunta --------------------

function renderDetalle(main, id) {
  const p = DATA.preguntas.find((x) => x.id === id);

  if (!p) {
    main.innerHTML = `<div class="empty-state">No se encontró esa pregunta.</div>`;
    return;
  }

  const meta = SUBJECT_META[p.asignatura_slug] || { label: p.asignatura_slug };
  const pdfHref = "../" + p.fuente;

  const apartadosHtml = (p.apartados || []).length
    ? `<ul class="question-apartados">${p.apartados
        .map((a) => `<li>${escapeHtml(a)}</li>`)
        .join("")}</ul>`
    : "";

  const avisoHtml = p.revision_manual_dudosa
    ? `<div class="notice-box">Esta pregunta está marcada como pendiente de revisión manual (transcripción dudosa).</div>`
    : "";

  const temaTags = (p.tema && p.tema.length)
    ? p.tema.map((t) => `<span class="tag tag-tema">${escapeHtml(t)}</span>`).join("")
    : `<span class="tag tag-sin-tema">Sin clasificar</span>`;

  main.innerHTML = `
    <p class="breadcrumb">
      <a href="#/materias">Asignaturas</a> /
      <a href="#/materia/${p.asignatura_slug}">${meta.label}</a> /
      Pregunta ${p.numero_pregunta ?? "?"}
    </p>

    <article class="question-detail">
      <div class="question-detail-head">
        <h1>${meta.label} · ${p.anio} · ${p.convocatoria}</h1>
        <span class="tag-row">
          ${temaTags}
          <span class="tag">${escapeHtml(p.puntuacion || "")}</span>
          <span class="tag">${escapeHtml(p.ley_educativa || "")}</span>
        </span>
      </div>

      ${avisoHtml}

      <div class="question-body">${escapeHtml(p.enunciado)}</div>

      ${apartadosHtml}

      <div class="detail-meta">
        <a class="pdf-link" href="${escapeHtml(pdfHref)}" target="_blank" rel="noopener">
          Ver examen completo en PDF ↗
        </a>
      </div>
    </article>
  `;
}

// -------------------- arranque --------------------

async function boot() {
  await loadData();
  render();
  window.addEventListener("hashchange", render);
}

window.addEventListener("vault-unlocked", boot, { once: true });

// si ya estaba desbloqueado en esta sesión, auth.js ya quitó el hidden
// antes de que este script corra; comprobamos por si acaso el evento
// se disparó antes de registrar el listener.
if (!document.getElementById("app").hidden) {
  boot();
}

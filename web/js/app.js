// ============================================================
// Vault PAU — aplicación de una sola página, sin frameworks.
// Router muy simple basado en location.hash.
// ============================================================

let DATA = null;
let STATS = null;
let CATALOGO_DEBUXO = null;

const SUBJECT_META = {
  matematicas_ii: { label: "Matemáticas II", desc: "Álgebra, análisis, geometría, probabilidad" },
  bioloxia: { label: "Biología", desc: "Bioquímica, genética, fisiología, ecología" },
  fisica: { label: "Física", desc: "Interacción gravitatoria, electromagnetismo, ondas, física moderna" },
  quimica: { label: "Química", desc: "Reacciones, enlace, estructura de la materia, orgánica" },
  historiaespana: { label: "Historia de España", desc: "De los Reyes Católicos a la España actual" },
  historiafilosofia: { label: "Historia da Filosofía", desc: "De Platón a Simone de Beauvoir" },
  ingles: { label: "Inglés", desc: "Reading, gramática, vocabulario y writing" },
  castelan: { label: "Lingua Castelá e Literatura", desc: "Comentario de texto, gramática y literatura española" },
  galego: { label: "Lingua Galega e Literatura", desc: "Comunicación, gramática, sociolingüística e literatura galega" },
  tecnoloxia: { label: "Tecnoloxía e Enxeñaría", desc: "Materiales, sistemas mecánicos, eléctricos y control" },
  debuxotecnico: { label: "Debuxo Técnico", desc: "Catálogo de exámenes completos en PDF (examen gráfico, sin trocear)" },
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
  const res3 = await fetch("data/debuxotecnico.json?v=" + Date.now(), { cache: "no-store" });
  CATALOGO_DEBUXO = await res3.json();
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
  } else if (segments[0] === "materia" && segments[1] === "debuxotecnico") {
    nav.innerHTML = `<a href="#/">Portada</a><a href="#/materias">Asignaturas</a><a href="#/estadisticas">Estadísticas</a>`;
    renderCatalogoDebuxo(main);
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

  const slugs = Object.keys(SUBJECT_META).filter((s) => counts[s] || s === "debuxotecnico");

  main.innerHTML = `
    <h1 class="page-title">Elige una asignatura</h1>
    <p class="page-subtitle">Cada una con sus propios filtros de tema, año y convocatoria.</p>
    <div class="subject-grid">
      ${slugs
        .map((slug) => {
          const meta = SUBJECT_META[slug];
          const cardMeta =
            slug === "debuxotecnico"
              ? `${CATALOGO_DEBUXO.examenes.length} exámenes (PDF) · ${meta.desc}`
              : `${counts[slug]} preguntas · ${meta.desc}`;
          return `
          <a class="subject-card" href="#/materia/${slug}">
            <h2>${meta.label}</h2>
            <p class="subject-meta">${cardMeta}</p>
          </a>`;
        })
        .join("")}
    </div>
  `;
}

// -------------------- vista: catálogo Debuxo Técnico (solo PDF) --------------------

function renderCatalogoDebuxo(main) {
  const meta = SUBJECT_META.debuxotecnico;
  const filas = CATALOGO_DEBUXO.examenes
    .map(
      (e) => `
      <a class="pdf-catalog-row" href="${escapeHtml(e.fuente)}" target="_blank" rel="noopener">
        <span class="pdf-catalog-anio">${e.año}</span>
        <span class="pdf-catalog-conv">${e.convocatoria}</span>
        <span class="pdf-catalog-link">Ver PDF ↗</span>
      </a>`
    )
    .join("");

  main.innerHTML = `
    <p class="breadcrumb"><a href="#/materias">Asignaturas</a> / ${meta.label}</p>
    <h1 class="page-title" style="text-align:left; margin-bottom: 8px;">${meta.label}</h1>
    <div class="notice-box">${CATALOGO_DEBUXO.nota}</div>
    <div class="pdf-catalog-list">${filas}</div>
  `;
}

// -------------------- vista: lista con filtros --------------------

// asignaturas con el mapa de calor habilitado (Fase 3). Confirmado el
// diseño con Biología como piloto, se replica a todas las asignaturas
// troceadas en vault/ (Debuxo Técnico queda fuera: es un catálogo de PDF,
// no tiene preguntas trozeadas).
const HEATMAP_SUBJECTS = [
  "matematicas_ii", "bioloxia", "fisica", "quimica",
  "historiaespana", "historiafilosofia", "ingles",
  "castelan", "galego", "tecnoloxia",
];

// Fase 4: generador de simulacros. Confirmado el piloto de Biología,
// replicado a las demás asignaturas troceadas en vault/ (Debuxo Técnico
// queda fuera: catálogo de PDF, no hay texto real de pregunta que
// reutilizar). "huecos" = nº de preguntas de un examen real de esa
// asignatura en el formato vigente (LOMLOE 2025-2026): las 10 asignaturas
// troceadas convergen en 4 huecos (antes de 2025 el PDF fuente traía 8
// preguntas repartidas en 2 opciones de 4, de las que se respondía solo
// una; eso no cambia el nº real de huecos de un examen). "avoidRepeatTema"
// refleja si los exámenes reales 2025-2026 de esa asignatura repiten tema
// entre sus 4 preguntas (inventario Fase 4 Paso 1, sobre los 4 exámenes
// evaluables del formato vigente):
//   bioloxia 4/4, quimica 4/4, galego 4/4, fisica 2/4, tecnoloxia 3/4
//     -> se repite con frecuencia real -> avoidRepeatTema: false
//   matematicas_ii 0/4, historiaespana 0/4, historiafilosofia 0/4,
//   castelan 0/4, ingles 1/4
//     -> no suele repetirse -> avoidRepeatTema: true
// Fase 5: dato destacado de portada, indicador de frecuencia, temporizador
// e impresión del simulacro. Piloto solo en Biología mientras se confirma
// el diseño; una vez confirmado, ampliar esta lista a las 10 asignaturas
// (las mismas de HEATMAP_SUBJECTS/SIMULACRO_CONFIG).
const FASE5_SUBJECTS = ["bioloxia"];

const SIMULACRO_CONFIG = {
  matematicas_ii: { huecos: 4, avoidRepeatTema: true },
  bioloxia: { huecos: 4, avoidRepeatTema: false },
  fisica: { huecos: 4, avoidRepeatTema: false },
  quimica: { huecos: 4, avoidRepeatTema: false },
  historiaespana: { huecos: 4, avoidRepeatTema: true },
  historiafilosofia: { huecos: 4, avoidRepeatTema: true },
  ingles: { huecos: 4, avoidRepeatTema: true },
  castelan: { huecos: 4, avoidRepeatTema: true },
  galego: { huecos: 4, avoidRepeatTema: false },
  tecnoloxia: { huecos: 4, avoidRepeatTema: false },
};

function renderLista(main, slug, initialParams) {
  const meta = SUBJECT_META[slug] || { label: slug };
  const preguntas = DATA.preguntas.filter((p) => p.asignatura_slug === slug);

  const temas = [...new Set(preguntas.flatMap((p) => p.tema || []))].sort();
  const anios = [...new Set(preguntas.map((p) => p.anio))].sort();
  const hayVacios = preguntas.some((p) => !p.tema || p.tema.length === 0);

  const conHeatmap = HEATMAP_SUBJECTS.includes(slug);
  const conSimulacro = Object.prototype.hasOwnProperty.call(SIMULACRO_CONFIG, slug);
  const conFase5 = FASE5_SUBJECTS.includes(slug);

  const tabButtonsHtml = [
    `<button class="view-tab is-active" data-view="lista">Lista</button>`,
    conHeatmap ? `<button class="view-tab" data-view="heatmap">Mapa de calor</button>` : "",
    conHeatmap && conFase5 ? `<button class="view-tab" data-view="frecuencia">Frecuencia</button>` : "",
    conSimulacro ? `<button class="view-tab" data-view="simulacro">Simulacro</button>` : "",
  ].join("");

  const tabsHtml = (conHeatmap || conSimulacro)
    ? `<div class="view-tabs">${tabButtonsHtml}</div>`
    : "";

  const datoDestacadoHtml = conHeatmap && conFase5 ? renderDatoDestacado(preguntas, anios) : "";

  main.innerHTML = `
    <p class="breadcrumb"><a href="#/materias">Asignaturas</a> / ${meta.label}</p>
    <h1 class="page-title" style="text-align:left; margin-bottom: 12px;">${meta.label}</h1>
    ${datoDestacadoHtml}
    ${tabsHtml}
    <div id="vista-lista">
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
    </div>
    <div id="vista-heatmap" hidden></div>
    <div id="vista-frecuencia" hidden></div>
    <div id="vista-simulacro" hidden></div>
  `;

  if (conHeatmap || conSimulacro) {
    const tabButtons = main.querySelectorAll(".view-tab");
    const vistas = {
      lista: document.getElementById("vista-lista"),
      heatmap: document.getElementById("vista-heatmap"),
      frecuencia: document.getElementById("vista-frecuencia"),
      simulacro: document.getElementById("vista-simulacro"),
    };
    tabButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        tabButtons.forEach((b) => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        const view = btn.dataset.view;
        for (const [name, el] of Object.entries(vistas)) el.hidden = name !== view;
        if (view === "heatmap" && !vistas.heatmap.dataset.rendered) {
          renderHeatmap(vistas.heatmap, preguntas);
          vistas.heatmap.dataset.rendered = "1";
        }
        if (view === "frecuencia" && !vistas.frecuencia.dataset.rendered) {
          renderFrecuencia(vistas.frecuencia, preguntas, anios[anios.length - 1]);
          vistas.frecuencia.dataset.rendered = "1";
        }
        if (view === "simulacro" && !vistas.simulacro.dataset.rendered) {
          renderSimulacro(vistas.simulacro, preguntas, slug);
          vistas.simulacro.dataset.rendered = "1";
        }
      });
    });
  }

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

// -------------------- vista: mapa de calor (tema × año) --------------------
//
// Fase 3. Se calcula en el cliente a partir de DATA.preguntas (el mismo
// preguntas.json que ya usa la lista/buscador), no de estadisticas.json —
// una sola fuente de verdad, y solo cubre el rango del vault (2020-2026).

function parsePuntuacion(str) {
  // "2 puntos" / "2,5 puntos" / "2 puntos (1 punto por apartado)" -> 2 / 2.5 / 2
  // toma el primer número que aparezca, ignorando cualquier texto entre
  // paréntesis o después.
  const m = String(str || "").match(/(\d+(?:[.,]\d+)?)/);
  if (!m) return 0;
  return parseFloat(m[1].replace(",", "."));
}

function normalizeTemaBucket(t) {
  const s = (t || "").toString().trim();
  if (!s) return null;
  if (/^\d+$/.test(s)) return null; // "1", "3"... basura conocida, no un tema real
  return s;
}

function temasDePregunta(p) {
  const limpios = (p.tema || []).map(normalizeTemaBucket).filter(Boolean);
  return limpios.length ? limpios : ["Sin clasificar"];
}

// Fase 5 (puntos 3 y 4): una sola función de frecuencia por tema, misma
// fuente y mismo criterio de limpieza de tema que ya usa el mapa de calor
// (temasDePregunta) - el dato destacado de portada y el indicador "lleva
// X años sin caer" salen de aquí, no de un cálculo aparte.
function computeTemaFrecuencia(preguntas) {
  const info = {};
  for (const p of preguntas) {
    for (const t of temasDePregunta(p)) {
      if (t === "Sin clasificar") continue;
      if (!info[t]) info[t] = { tema: t, n: 0, primerAnio: p.anio, ultimoAnio: p.anio };
      info[t].n++;
      info[t].primerAnio = Math.min(info[t].primerAnio, p.anio);
      info[t].ultimoAnio = Math.max(info[t].ultimoAnio, p.anio);
    }
  }
  return Object.values(info);
}

// Fase 5, punto 3: dato destacado en la portada de cada asignatura, un
// tema calculado en el momento desde el mismo preguntas.json (computeTemaFrecuencia).
function renderDatoDestacado(preguntas, anios) {
  const frecuencias = computeTemaFrecuencia(preguntas);
  if (!frecuencias.length || !anios.length) return "";

  const maxN = Math.max(...frecuencias.map((f) => f.n));
  const ganadores = frecuencias.filter((f) => f.n === maxN).map((f) => f.tema);
  const anioMin = anios[0];

  const nombres = ganadores.map((t) => `<strong>${escapeHtml(t)}</strong>`);
  const listaNombres =
    nombres.length === 1
      ? nombres[0]
      : nombres.slice(0, -1).join(", ") + " y " + nombres[nombres.length - 1];
  const verbo = ganadores.length === 1 ? "es el que más se repite" : "son los que más se repiten";
  const vecesTexto = ganadores.length === 1 ? `aparece ${maxN} veces` : `aparecen ${maxN} veces cada uno`;

  return `
    <div class="dato-destacado">
      ${listaNombres} ${verbo}: ${vecesTexto} desde ${anioMin}.
    </div>
  `;
}

function heatColor(ratio) {
  // interpola cream-100 (#f2ead6, baja intensidad) -> ink-900 (#0b1c30, alta)
  const c0 = [242, 234, 214];
  const c1 = [11, 28, 48];
  const r = Math.round(c0[0] + (c1[0] - c0[0]) * ratio);
  const g = Math.round(c0[1] + (c1[1] - c0[1]) * ratio);
  const b = Math.round(c0[2] + (c1[2] - c0[2]) * ratio);
  return `rgb(${r}, ${g}, ${b})`;
}

function computeHeatmapData(preguntas, { metric, leyes, conv }) {
  const filtered = preguntas.filter((p) => {
    if (leyes.length && !leyes.includes(p.ley_educativa)) return false;
    if (conv && p.convocatoria !== conv) return false;
    return true;
  });

  const anios = [...new Set(filtered.map((p) => p.anio))].sort((a, b) => a - b);
  const cell = {};
  const temaTotal = {};
  let sinClasificarPreguntas = 0;
  const sinClasificarVistas = new Set();

  for (const p of filtered) {
    const temas = temasDePregunta(p);
    const valor = metric === "puntuacion" ? parsePuntuacion(p.puntuacion) : 1;
    for (const t of temas) {
      if (t === "Sin clasificar" && !sinClasificarVistas.has(p.id)) {
        sinClasificarVistas.add(p.id);
        sinClasificarPreguntas++;
      }
      cell[t] = cell[t] || {};
      cell[t][p.anio] = (cell[t][p.anio] || 0) + valor;
      temaTotal[t] = (temaTotal[t] || 0) + valor;
    }
  }

  const temas = Object.keys(cell).sort((a, b) => {
    if (a === "Sin clasificar") return 1;
    if (b === "Sin clasificar") return -1;
    return temaTotal[b] - temaTotal[a];
  });

  let max = 0;
  for (const t of temas) {
    for (const a of anios) max = Math.max(max, cell[t][a] || 0);
  }

  return { temas, anios, cell, max, sinClasificarPreguntas, totalFiltradas: filtered.length };
}

function renderHeatmap(container, preguntas) {
  const leyesDisponibles = [...new Set(preguntas.map((p) => p.ley_educativa).filter(Boolean))];

  container.innerHTML = `
    <div class="heatmap-controls">
      <div>
        <label for="hm-metric">Colorear por</label>
        <select id="hm-metric">
          <option value="frecuencia">Frecuencia (nº de preguntas)</option>
          <option value="puntuacion">Puntuación acumulada</option>
        </select>
      </div>
      <div>
        <label for="hm-conv">Convocatoria</label>
        <select id="hm-conv">
          <option value="">Ambas</option>
          <option value="ordinaria">Ordinaria</option>
          <option value="extraordinaria">Extraordinaria</option>
        </select>
      </div>
      <div class="heatmap-ley-filter">
        <label>Legislación</label>
        <div class="heatmap-ley-checks">
          ${["LOE", "LOMCE", "LOMLOE"]
            .map((ley) => {
              const disabled = !leyesDisponibles.includes(ley);
              return `
              <label class="heatmap-ley-check ${disabled ? "is-disabled" : ""}">
                <input type="checkbox" value="${ley}" ${disabled ? "disabled" : "checked"} />
                ${ley}
              </label>`;
            })
            .join("")}
        </div>
      </div>
    </div>
    <div class="heatmap-scroll">
      <div id="heatmap-grid"></div>
    </div>
    <div class="heatmap-legend" id="heatmap-legend"></div>
    <p class="heatmap-note" id="heatmap-note"></p>
  `;

  const metricEl = document.getElementById("hm-metric");
  const convEl = document.getElementById("hm-conv");
  const leyChecks = [...container.querySelectorAll('.heatmap-ley-checks input[type="checkbox"]')];

  function draw() {
    const metric = metricEl.value;
    const conv = convEl.value;
    const leyes = leyChecks.filter((c) => c.checked).map((c) => c.value);

    const data = computeHeatmapData(preguntas, { metric, leyes, conv });
    drawGrid(data, metric);
  }

  function drawGrid(data, metric) {
    const grid = document.getElementById("heatmap-grid");
    const legend = document.getElementById("heatmap-legend");
    const note = document.getElementById("heatmap-note");

    if (!data.temas.length || !data.anios.length) {
      grid.innerHTML = `<div class="empty-state">Ningún dato coincide con estos filtros.</div>`;
      legend.innerHTML = "";
      note.textContent = "";
      return;
    }

    const cols = data.anios.length;
    grid.style.gridTemplateColumns = `220px repeat(${cols}, minmax(56px, 1fr))`;

    const headerCells = [`<div class="heatmap-cell heatmap-corner"></div>`]
      .concat(data.anios.map((a) => `<div class="heatmap-cell heatmap-colhead">${a}</div>`));

    const rows = data.temas.map((t) => {
      const rowCells = [
        `<div class="heatmap-cell heatmap-rowhead" title="${escapeHtml(t)}">${escapeHtml(t)}</div>`,
      ];
      for (const a of data.anios) {
        const v = data.cell[t][a] || 0;
        const ratio = data.max > 0 ? v / data.max : 0;
        const bg = v > 0 ? heatColor(ratio) : "transparent";
        const textClass = ratio >= 0.55 ? "heatmap-value-light" : "heatmap-value-dark";
        const label = v === 0 ? "" : metric === "puntuacion" ? v.toFixed(1).replace(/\.0$/, "") : v;
        rowCells.push(
          `<div class="heatmap-cell heatmap-value ${textClass}" style="background:${bg}">${label}</div>`
        );
      }
      return rowCells.join("");
    });

    grid.innerHTML = headerCells.join("") + rows.join("");

    const steps = 5;
    const legendCells = Array.from({ length: steps }, (_, i) => {
      const ratio = i / (steps - 1);
      return `<div class="heatmap-legend-step" style="background:${heatColor(ratio)}"></div>`;
    }).join("");

    legend.innerHTML = `
      <span class="heatmap-legend-label">Menos</span>
      <div class="heatmap-legend-scale">${legendCells}</div>
      <span class="heatmap-legend-label">Más</span>
      <span class="heatmap-legend-max">máximo: ${
        metric === "puntuacion" ? data.max.toFixed(1).replace(/\.0$/, "") + " ptos" : data.max + " preguntas"
      }</span>
    `;

    note.textContent = `${data.totalFiltradas} preguntas contabilizadas` +
      (data.sinClasificarPreguntas
        ? ` · ${data.sinClasificarPreguntas} sin tema clasificado (bucket "Sin clasificar")`
        : "");
  }

  metricEl.addEventListener("change", draw);
  convEl.addEventListener("change", draw);
  leyChecks.forEach((c) => c.addEventListener("change", draw));

  draw();
}

// -------------------- vista: frecuencia (Fase 5, punto 4) --------------------
//
// Sección propia (no escondida en el mapa de calor): qué temas se repiten
// más, y qué temas llevan más años sin aparecer. Misma fuente y mismo
// cálculo que el dato destacado de portada (computeTemaFrecuencia).

function renderFrecuencia(container, preguntas, anioMax) {
  const frecuencias = computeTemaFrecuencia(preguntas);

  if (!frecuencias.length) {
    container.innerHTML = `<div class="empty-state">No hay temas clasificados todavía para calcular esto.</div>`;
    return;
  }

  const masFrecuentes = [...frecuencias].sort((a, b) => b.n - a.n || a.tema.localeCompare(b.tema));
  const masAusentes = [...frecuencias]
    .map((f) => ({ ...f, aniosSinCaer: anioMax - f.ultimoAnio }))
    .sort((a, b) => b.aniosSinCaer - a.aniosSinCaer || a.tema.localeCompare(b.tema));

  const itemFrecuente = (f) => `
    <li>
      <span class="frecuencia-tema">${escapeHtml(f.tema)}</span>
      <span class="frecuencia-valor">${f.n} ${f.n === 1 ? "vez" : "veces"}</span>
    </li>`;

  const itemAusente = (f) => `
    <li>
      <span class="frecuencia-tema">${escapeHtml(f.tema)}</span>
      <span class="frecuencia-valor">${
        f.aniosSinCaer <= 0 ? `en ${anioMax}` : `${f.aniosSinCaer} año${f.aniosSinCaer === 1 ? "" : "s"} sin caer`
      }</span>
    </li>`;

  container.innerHTML = `
    <div class="frecuencia-header">
      Frecuencia histórica, no es una predicción garantizada de lo que va a caer.
    </div>
    <div class="frecuencia-columns">
      <div class="frecuencia-col">
        <h2>Los que más se repiten</h2>
        <ul class="frecuencia-list">${masFrecuentes.map(itemFrecuente).join("")}</ul>
      </div>
      <div class="frecuencia-col">
        <h2>Los que más años llevan sin caer</h2>
        <ul class="frecuencia-list">${masAusentes.map(itemAusente).join("")}</ul>
      </div>
    </div>
  `;
}

// -------------------- vista: simulacro (Fase 4) --------------------
//
// Ensambla un examen completo con preguntas REALES del vault (nunca texto
// inventado), eligiendo un tema por hueco ponderado por su frecuencia
// histórica real en esta asignatura, y luego una pregunta real al azar
// que trate ese tema. Piloto: solo Biología (SIMULACRO_CONFIG).

// Fase 5, punto 1: duración del temporizador. Por defecto, los 90 minutos
// estándar de un examen de la ABAU/PAU. Las "Orientacións xerais" oficiales
// de CIUG revisadas esta sesión (Bioloxía, Física, Química, Matemáticas II,
// Debuxo Técnico) describen contenidos y bloques, no la duración del
// examen - no se encontró ahí una duración distinta por asignatura, así
// que se usa el estándar para las 10. Si en algún momento se localiza la
// duración oficial real de alguna, se añade aquí su excepción.
const SIMULACRO_DEFAULT_DURATION_MIN = 90;
const SIMULACRO_DURATION_MIN = {};

function formatTiempo(segundosRestantes) {
  const s = Math.max(0, segundosRestantes);
  const mm = String(Math.floor(s / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

// Cuenta atrás pura en memoria: no guarda nada (ni localStorage ni al
// servidor), no corrige, solo cuenta. Se reinicia cada vez que se genera
// un simulacro nuevo.
function iniciarTemporizador(el, minutos) {
  if (el._intervalId) clearInterval(el._intervalId);
  let restante = Math.round(minutos * 60);
  el.classList.remove("timer-expired");
  el.textContent = formatTiempo(restante);
  el._intervalId = setInterval(() => {
    restante--;
    if (restante <= 0) {
      clearInterval(el._intervalId);
      el._intervalId = null;
      el.classList.add("timer-expired");
      el.textContent = "Tiempo agotado";
      return;
    }
    el.textContent = formatTiempo(restante);
  }, 1000);
}

function pesarTemasPorFrecuencia(preguntas) {
  const freq = {};
  for (const p of preguntas) {
    for (const t of temasDePregunta(p)) {
      if (t === "Sin clasificar") continue; // no tiene sentido "practicar" este bucket
      freq[t] = (freq[t] || 0) + 1;
    }
  }
  return freq; // { tema: nº de preguntas históricas con ese tema }
}

function elegirTemaPonderado(freq, excluir) {
  const entradas = Object.entries(freq).filter(([t]) => !excluir.has(t));
  const total = entradas.reduce((s, [, n]) => s + n, 0);
  if (total === 0) return null;
  let r = Math.random() * total;
  for (const [tema, n] of entradas) {
    r -= n;
    if (r <= 0) return tema;
  }
  return entradas[entradas.length - 1][0];
}

function generarSimulacro(preguntas, config) {
  const freq = pesarTemasPorFrecuencia(preguntas);
  const porTema = {};
  for (const p of preguntas) {
    for (const t of temasDePregunta(p)) {
      if (t === "Sin clasificar") continue;
      (porTema[t] = porTema[t] || []).push(p);
    }
  }

  const huecos = [];
  const temasUsados = new Set();
  const idsUsados = new Set();

  for (let i = 0; i < config.huecos; i++) {
    const excluir = config.avoidRepeatTema ? temasUsados : new Set();
    const tema = elegirTemaPonderado(freq, excluir) || elegirTemaPonderado(freq, new Set());
    if (!tema) break;
    temasUsados.add(tema);

    const candidatas = (porTema[tema] || []).filter((p) => !idsUsados.has(p.id));
    const pool = candidatas.length ? candidatas : porTema[tema] || [];
    if (!pool.length) continue;
    const elegida = pool[Math.floor(Math.random() * pool.length)];
    idsUsados.add(elegida.id);
    huecos.push({ tema, pregunta: elegida });
  }

  return huecos;
}

function renderSimulacro(container, preguntas, slug) {
  const config = SIMULACRO_CONFIG[slug];
  const conFase5 = FASE5_SUBJECTS.includes(slug);
  const duracionMin = SIMULACRO_DURATION_MIN[slug] || SIMULACRO_DEFAULT_DURATION_MIN;

  // Piloto Fase 5 (temporizador + descarga en PDF): solo en las asignaturas
  // de FASE5_SUBJECTS mientras se confirma el diseño; el resto conserva la
  // toolbar simple ya confirmada en Fase 4.
  const toolbarHtml = conFase5
    ? `
    <div class="simulacro-toolbar no-print">
      <button class="btn-primary" id="btn-generar-simulacro">Generar otro simulacro</button>
      <button class="btn-secondary" id="btn-imprimir-simulacro">Descargar / imprimir PDF</button>
      <div class="simulacro-timer">
        <span class="simulacro-timer-label">Tiempo (${duracionMin} min)</span>
        <span class="simulacro-timer-value" id="simulacro-timer-value">--:--</span>
      </div>
    </div>`
    : `<button class="btn-primary" id="btn-generar-simulacro" style="margin-bottom: 24px;">
        Generar otro simulacro
      </button>`;

  container.innerHTML = `
    <div class="notice-box no-print">
      Simulacro generado a partir de preguntas reales, ponderado por frecuencia histórica —
      no es una predicción de lo que va a caer, es una herramienta de práctica.
    </div>
    ${toolbarHtml}
    <div id="simulacro-huecos"></div>
  `;

  const btn = document.getElementById("btn-generar-simulacro");
  const btnImprimir = document.getElementById("btn-imprimir-simulacro");
  const huecosEl = document.getElementById("simulacro-huecos");
  const timerEl = document.getElementById("simulacro-timer-value");

  function draw() {
    const huecos = generarSimulacro(preguntas, config);
    if (!huecos.length) {
      huecosEl.innerHTML = `<div class="empty-state">No hay suficientes preguntas clasificadas por tema para generar un simulacro.</div>`;
      return;
    }
    huecosEl.innerHTML = huecos
      .map(({ tema, pregunta }, i) => {
        const heading = `Pregunta ${i + 1} · ${escapeHtml(tema)}`;
        return renderQuestionCard(pregunta, { heading });
      })
      .join("");
    if (conFase5) iniciarTemporizador(timerEl, duracionMin);
  }

  btn.addEventListener("click", draw);
  if (btnImprimir) btnImprimir.addEventListener("click", () => window.print());
  draw();
}

// -------------------- vista: detalle de pregunta --------------------

function renderQuestionCard(p, { heading } = {}) {
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

  return `
    <article class="question-detail">
      <div class="question-detail-head">
        <h1>${heading || `${meta.label} · ${p.anio} · ${p.convocatoria}`}</h1>
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

function renderDetalle(main, id) {
  const p = DATA.preguntas.find((x) => x.id === id);

  if (!p) {
    main.innerHTML = `<div class="empty-state">No se encontró esa pregunta.</div>`;
    return;
  }

  const meta = SUBJECT_META[p.asignatura_slug] || { label: p.asignatura_slug };

  main.innerHTML = `
    <p class="breadcrumb">
      <a href="#/materias">Asignaturas</a> /
      <a href="#/materia/${p.asignatura_slug}">${meta.label}</a> /
      Pregunta ${p.numero_pregunta ?? "?"}
    </p>
    ${renderQuestionCard(p)}
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

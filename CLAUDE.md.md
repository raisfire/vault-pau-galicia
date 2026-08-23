# Herramienta ABAU/PAU Galicia — Plan del proyecto
*Resumen de la entrevista de definición. Última actualización: 23/08/2026.*

**Nota de terminología:** desde 2025 el nombre oficial de la prueba pasó de ABAU a PAU en toda España (unificación entre comunidades). La CIUG ya usa "PAU" en su web actual. Los exámenes de 2010-2024 de este proyecto se llamaron oficialmente ABAU; los de 2025 en adelante se llaman PAU — es la misma prueba, organizada por la misma CIUG. El nombre puede guardarse como un dato más ligado al año del examen, no hay que elegir uno solo para todo el proyecto. Este documento sigue usando "ABAU" de forma genérica por comodidad, salvo que se indique lo contrario.

---

## 1. Objetivo del proceso

Construir la mejor herramienta posible sobre la ABAU de Galicia: una base de datos completa de exámenes oficiales de la CIUG, troceada y etiquetada, con un visor visual para buscar y filtrar, una capa de estadísticas y mapas de calor sobre qué cae y cuánto puntúa, y —si el tiempo lo permite— un intento honesto de predicción. Fin último: preparar la ABAU para entrar en Medicina en la USC con un 12,8.

## 2. Usuario o destinatario

Un único usuario: el propio estudiante (2º de bachillerato, Galicia). No programa; toda la construcción técnica la hace Claude Code bajo su dirección. Ocasionalmente se la enseñará a otras personas (profesores, compañeros), pero no es una herramienta multiusuario ni pública.

## 3. Alcance: asignaturas y oleadas

12 asignaturas, atacadas en tres oleadas. No se pasa a la oleada N+1 sin dejar sólida la N.

| Oleada | Asignaturas | Motivo del orden |
|---|---|---|
| **1** | Matemáticas II, Biología, Química, Física | Las que cursa el usuario, estructura de examen más regular (preguntas numeradas, puntuación explícita en el enunciado) → mejor caso para probar el motor de troceo |
| **2** | Historia de España, Historia de la Filosofía, Lengua Castellana, Lingua Galega, Inglés | También las cursa, pero con estructura más difícil de trocear (comentarios de texto, apartados encadenados) |
| **3** | Matemáticas Aplicadas a las CC.SS., Tecnología e Ingeniería, Dibujo Técnico | Ampliación "para que impresione"; no las cursa el usuario. Se atacan solo si sobra tiempo. Puerta abierta a asignaturas de letras si el proyecto va muy bien. |

**Corte de realidad asumido:** con el calendario disponible (agosto libre, luego ~3h/semana), lo más probable es llegar al 31 de octubre con la oleada 1 completa, la oleada 2 a medias y la oleada 3 sin empezar. Si esto no es aceptable, hay que quitar alcance de otro sitio, no forzar el calendario.

## 4. Flujo paso a paso (orden innegociable)

1. **Base de datos** — descargar los PDFs de exámenes de la CIUG, trocearlos en preguntas etiquetadas por asignatura, tema y año.
2. **Visor** — buscar y filtrar cualquier pregunta por asignatura, tema, año, convocatoria y ley educativa.
3. **Estadísticas y mapas de calor** — qué cae, cuánto puntúa, cada cuánto se repite, con varios cortes de análisis (general, por legislación, por convocatoria...).
4. **Predicción** — lo último, y con expectativas ajustadas (ver Riesgos).

Si algo se queda fuera el 31 de octubre, se queda fuera lo de abajo de esta lista, nunca lo de arriba.

## 5. Inputs necesarios

- PDFs de exámenes oficiales de la CIUG (ciug.gal), castellano, 2010–2026, ambas convocatorias (ordinaria y extraordinaria). *Hallazgo de la entrevista: cada PDF trae gallego y castellano en el mismo documento — no hay que buscar dos ficheros por examen.*
- PDFs de criterios de corrección de la CIUG (solo para extraer la puntuación de cada pregunta, no el texto).
- Programaciones/orientaciones oficiales de la CIUG por materia (para contrastar la lista de temas que proponga la IA).
- Respaldo si algo falta en ciug.gal: examenesdepau.com, selectividad.academy.
- Cuota de la API de Claude Sonnet (10$ ya cargados, uso exclusivo para el etiquetado de temas).

## 6. Outputs esperados

- Base de datos de preguntas etiquetadas (asignatura, año, convocatoria, tema, puntuación, ley educativa, texto en castellano salvo Lingua Galega).
- Visor tipo biblioteca: buscar, filtrar, leer, con el criterio de puntuación al lado.
- Panel de estadísticas con varios cortes: general desde 2010, por legislación (LOE / LOMCE / LOMLOE), por convocatoria, por asignatura/tema.
- Mapas de calor visuales sobre lo anterior.
- (Fase 4, si llega) Un indicador tipo "lleva X años sin caer / ha caído Y de los últimos Z años", no un porcentaje de probabilidad inventado.

## 7. Reglas principales

- **Formato de almacenamiento: texto + metadatos, un archivo por pregunta.** Es, por construcción, un vault de Obsidian (metadatos tipo asignatura/año/tema/puntuación arriba, enunciado debajo). La web privada con enlace es una capa aparte que Claude Code construye leyendo esos mismos archivos; ambas conviven sin conflicto.

- **Orden de construcción fijo** (sección 4): no se empieza una fase sin cerrar razonablemente la anterior.
- **Un solo motor de troceo, no 12 programas distintos.** La diferencia entre asignaturas vive en una "ficha de troceo" corta (cómo se numeran las preguntas, si se trocea por pregunta o por apartado, etc.), no en código separado por asignatura.
- **Etiquetado de temas = IA + contraste oficial.** Claude agrupa lo que ve en los exámenes y propone temas; se contrastan contra las programaciones/orientaciones de la CIUG (y, en asignaturas como Biología, contra los propios títulos de bloque que ya trae el examen). El usuario revisa el resultado.
- **De los criterios de corrección solo se extrae el número de puntos de cada pregunta.** El texto del criterio no se parsea; se enlaza al PDF original.
- **Presupuesto de la API: 10$ máximo, ya cargados, no ampliables.** Etiquetado con Haiku 4.5 + Batch API + prompt caching (coste estimado real: 2-3$ para las ~4.000 preguntas). Cualquier script que use la API debe llevar un tope de gasto y mostrar el coste estimado antes de lanzarse.
- **Castellano como idioma de trabajo**, excepto Lingua Galega e Literatura (que se queda en gallego por ser una asignatura sobre la propia lengua).
- **Convocatoria ordinaria y extraordinaria, ambas incluidas, con un filtro que permita diferenciarlas** en cualquier estadística.
- **Nada de hardware ni APIs de pago fuera de los 10$ ya asignados.**

## 8. Excepciones y casos límite

- **Lingua Galega e Literatura:** excepción de idioma (se queda en gallego).
- **Cambio de legislación (2025, LOMLOE):** los exámenes anteriores a ese cambio no dejan de ser útiles para practicar, pero mezclarlos sin distinguir puede dar estadísticas engañosas si un tema ya no está en el currículo actual. Por eso el filtro "por legislación" es un requisito, no un extra.
- **PDFs escaneados (más probables cuanto más viejo el examen):** el parseo automático de texto falla en escaneados; puede hacer falta OCR o revisión manual puntual. Puede ser motivo para recortar el rango de años en la práctica si da demasiados problemas.
- **Historia de España / Lengua / Lingua Galega:** la puntuación de cada apartado no siempre está en el enunciado como en ciencias; para el mapa de calor de puntuación en estas asignaturas puede hacer falta mirar el criterio de corrección aunque la regla general sea no tocarlo.

## 9. Criterios de calidad

- El visor encuentra cualquier pregunta filtrando por asignatura + tema + año en segundos.
- Cada pregunta muestra su puntuación correcta y el enlace a su criterio de corrección.
- Las estadísticas de "qué cae más" cambian de forma coherente al aplicar el filtro de legislación o de convocatoria (si no cambian nada, el filtro no sirve).
- El etiquetado de temas, revisado por el usuario, coincide razonablemente con los temas de sus apuntes/libro de texto.
- El gasto real de la API queda por debajo de los 10$ en todo momento, con margen visible antes de cada lote de etiquetado.
- La oleada 1 (Mat II, Bio, Química, Física) funciona de punta a punta —base de datos, visor y estadísticas— antes de invertir tiempo en la oleada 2.

## 10. Riesgos o ambigüedades pendientes

- **Cortes exactos de legislación por año** (LOE / LOMCE / LOMLOE): estimación aproximada LOE hasta 2016, LOMCE 2017-2024, LOMLOE desde 2025. El corte de 2025 tiene ahora más respaldo, porque coincide con el cambio oficial de nombre ABAU→PAU y de estructura de examen (RD 534/2024), confirmado por la propia CIUG. Aun así, **hay que verificar el detalle fino contra la documentación oficial** al construir la base de datos, especialmente el límite LOE/LOMCE (2016-2017), que no se ha contrastado directamente.
- **Dónde vive la web (privada, con enlace):** confirmado que hay opciones gratuitas, pero la opción concreta (qué servicio, cómo se protege el acceso) no está decidida todavía — es una decisión de implementación pendiente de plantear antes de construir esa parte.
- **La predicción (fase 4)** tiene una limitación real de datos (15-25 exámenes por asignatura no da para un modelo estadístico serio). El plan asume un indicador tipo "frecuencia histórica", no un modelo predictivo con porcentajes. Si el usuario quiere algo más ambicioso ahí, hay que hablarlo específicamente cuando se llegue a esa fase.
- **Historia de España / Lengua / Lingua Galega** son las asignaturas donde el grano de troceo y la extracción de puntuación son más inciertos; su ficha de troceo puede necesitar más de una iteración.

## 11. Estructura de carpetas del proyecto

```
ABAU-Galicia/
├── CLAUDE.md          ← este documento, renombrado (Claude Code lo carga solo)
├── fuentes/           ← PDFs descargados de la CIUG, sin tocar
├── vault/             ← SOLO esto se abre en Obsidian (preguntas troceadas)
├── scripts/           ← scraping, parseo, etiquetado
└── web/               ← la web privada, más adelante
```

## 12. Siguiente acción recomendada

Decidido ya: la estructura de carpetas (sección 11) y el método de descarga (scraping con Scrapling contra las páginas índice de la CIUG, un año/asignatura a la vez para validar antes de lanzar todo). Pendiente de construir tras eso, en orden:
- formato exacto de la "ficha de troceo" por asignatura (cómo se numeran las preguntas de cada una, dónde vive la puntuación),
- el parseo del PDF a preguntas sueltas dentro de `vault/`,
- el script de etiquetado de temas con control de gasto de la API.

Cada una de esas decisiones se plantea como pregunta antes de escribir nada, igual que hasta ahora.

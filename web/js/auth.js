// ============================================================
// FILTRO DE ACCESO — NO ES SEGURIDAD REAL.
//
// Esto es un filtro discreto para evitar que alguien que tropiece
// con el enlace vea el contenido por accidente. La contraseña está
// en texto plano aquí mismo, en el JavaScript que se sirve al
// navegador: cualquiera que abra las herramientas de desarrollador
// (o simplemente vea el código fuente de esta página) puede leerla
// o saltarse la comprobación directamente. Es un candado de cortina,
// no una cerradura.
//
// Es aceptable en este proyecto porque el contenido son exámenes
// públicos de la CIUG (organismo oficial, PDFs ya públicos en su
// web), no datos personales ni información sensible.
// ============================================================

const GATE_PASSWORD = "LebronJames31";
const GATE_SESSION_KEY = "vault_pau_auth_ok";

function unlockApp() {
  document.getElementById("gate").hidden = true;
  document.getElementById("app").hidden = false;
  window.dispatchEvent(new Event("vault-unlocked"));
}

(function initGate() {
  // sessionStorage puede lanzar una excepción en algunos navegadores
  // (Safari en modo privado, "Bloquear todas las cookies", ciertos
  // modos restringidos) — si eso corta el script antes de tiempo, el
  // usuario ve la contraseña "no hacer nada" al pulsar Entrar. Por
  // eso cada acceso a sessionStorage va envuelto en try/catch: si
  // falla, la app se sigue desbloqueando igual, solo que sin recordar
  // la sesión (habrá que reintroducir la contraseña la próxima vez).
  function tryGetSession() {
    try {
      return sessionStorage.getItem(GATE_SESSION_KEY);
    } catch (err) {
      return null;
    }
  }

  function trySetSession() {
    try {
      sessionStorage.setItem(GATE_SESSION_KEY, "1");
    } catch (err) {
      // ignorado a propósito, ver comentario arriba
    }
  }

  if (tryGetSession() === "1") {
    unlockApp();
    return;
  }

  const form = document.getElementById("gate-form");
  const input = document.getElementById("gate-input");
  const error = document.getElementById("gate-error");

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const typed = input.value.trim();
    if (typed === GATE_PASSWORD) {
      trySetSession();
      error.hidden = true;
      unlockApp();
    } else {
      // DIAGNÓSTICO TEMPORAL: no revela la contraseña, solo compara
      // longitudes para saber si el navegador está metiendo algo
      // distinto a lo que el usuario escribe (autofill, gestor de
      // contraseñas, etc.). Quitar una vez resuelto el problema de acceso.
      error.textContent =
        "Contraseña incorrecta. (Diagnóstico: escribiste " + typed.length +
        " caracteres; se esperan " + GATE_PASSWORD.length + ".)";
      error.hidden = false;
      input.value = "";
      input.focus();
    }
  });
})();

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
  if (sessionStorage.getItem(GATE_SESSION_KEY) === "1") {
    unlockApp();
    return;
  }

  const form = document.getElementById("gate-form");
  const input = document.getElementById("gate-input");
  const error = document.getElementById("gate-error");

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (input.value === GATE_PASSWORD) {
      sessionStorage.setItem(GATE_SESSION_KEY, "1");
      error.hidden = true;
      unlockApp();
    } else {
      error.hidden = false;
      input.value = "";
      input.focus();
    }
  });
})();

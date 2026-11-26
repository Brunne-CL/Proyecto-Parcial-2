function escapar(texto) {
  return String(texto ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

const contenido = document.querySelector("#contenido");
const pastilla = document.querySelector("[data-testid='estado-sistema']");

async function api(ruta, opciones = {}) {
  const respuesta = await fetch(ruta, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(opciones.headers || {}) },
    ...opciones,
  });
  const datos = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    throw new Error(datos.error || "No se pudo completar la operación.");
  }
  return datos;
}

function marcarEstado(operativo, texto) {
  pastilla.classList.toggle("fallo", !operativo);
  pastilla.querySelector("span").textContent = texto;
}

async function revisarSalud() {
  const respuesta = await fetch("/salud");
  if (!respuesta.ok) {
    marcarEstado(false, "fallo intencional");
    return;
  }
  marcarEstado(true, "operativo");
}

function vistaLogin(mensaje = "") {
  contenido.innerHTML = `
    <section class="tarjeta login">
      <h2>Iniciar sesión</h2>
      <p class="subtitulo">Use la cuenta de administrador para gestionar usuarios.</p>
      <form id="form-login">
        <label for="usuario">Usuario</label>
        <input id="usuario" name="usuario" autocomplete="username" required>
        <label for="clave">Clave</label>
        <input id="clave" name="clave" type="password" autocomplete="current-password" required>
        <div class="fila" style="margin-top:16px">
          <button type="submit">Entrar</button>
        </div>
        <p id="mensaje-error" class="error" ${mensaje ? "" : "hidden"}>${escapar(mensaje)}</p>
      </form>
    </section>`;
  document.querySelector("#form-login").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const boton = evento.target.querySelector("button");
    boton.disabled = true;
    try {
      await api("/api/sesion", {
        method: "POST",
        body: JSON.stringify({
          usuario: document.querySelector("#usuario").value,
          clave: document.querySelector("#clave").value,
        }),
      });
      await vistaUsuarios();
    } catch (error) {
      const aviso = document.querySelector("#mensaje-error");
      aviso.hidden = false;
      aviso.textContent = error.message;
      boton.disabled = false;
    }
  });
}

function formulario(persona) {
  const editando = Boolean(persona);
  return `
      <form id="form-usuario" class="panel" data-id="${editando ? persona.id : ""}">
      <h2>${editando ? "Editar usuario" : "Nuevo usuario"}</h2>
      <div class="rejilla">
        <div>
          <label for="f-usuario">Usuario</label>
          <input id="f-usuario" required value="${editando ? escapar(persona.usuario) : ""}">
        </div>
        <div>
          <label for="f-correo">Correo</label>
          <input id="f-correo" type="email" required value="${editando ? escapar(persona.correo) : ""}">
        </div>
        <div>
          <label for="f-rol">Rol</label>
          <select id="f-rol">
            <option value="usuario" ${!editando || persona.rol === "usuario" ? "selected" : ""}>usuario</option>
            <option value="admin" ${editando && persona.rol === "admin" ? "selected" : ""}>admin</option>
          </select>
        </div>
        <div>
          <label for="f-activo">Estado</label>
          <select id="f-activo">
            <option value="true" ${!editando || persona.activo ? "selected" : ""}>activo</option>
            <option value="false" ${editando && !persona.activo ? "selected" : ""}>inactivo</option>
          </select>
        </div>
        <div class="ancho">
          <label for="f-clave">${editando ? "Nueva clave (opcional)" : "Clave"}</label>
          <input id="f-clave" type="password" autocomplete="new-password" ${editando ? "" : "required"}>
        </div>
      </div>
      <div class="fila" style="margin-top:16px">
        <button type="submit">Guardar</button>
        <button type="button" class="secundario" id="cancelar">Cancelar</button>
      </div>
      <p id="mensaje-form" class="error" hidden></p>
    </form>`;
}

function fila(persona) {
  return `
    <tr data-usuario="${escapar(persona.usuario)}">
      <td>${persona.id}</td>
      <td>${escapar(persona.usuario)}</td>
      <td>${escapar(persona.correo)}</td>
      <td>${persona.rol}</td>
      <td>${persona.activo ? "activo" : "inactivo"}</td>
      <td class="fila">
        <button type="button" class="secundario" data-accion="editar" data-id="${persona.id}">Editar</button>
        <button type="button" class="peligro" data-accion="eliminar" data-id="${persona.id}">Eliminar</button>
      </td>
    </tr>`;
}

async function vistaUsuarios(aviso = "") {
  const lista = await api("/api/usuarios");
  const sesion = await api("/api/sesion");
  contenido.innerHTML = `
    <section class="tarjeta">
      <div class="espacio">
        <div>
          <h2>Usuarios</h2>
          <p class="subtitulo">Sesión de ${escapar(sesion.usuario.usuario)}</p>
        </div>
        <div class="fila">
          <button type="button" id="nuevo">Nuevo usuario</button>
          <button type="button" class="secundario" id="salir">Salir</button>
        </div>
      </div>
      <p id="aviso" class="aviso" ${aviso ? "" : "hidden"}>${escapar(aviso)}</p>
      <table id="tabla-usuarios">
        <thead>
          <tr><th>Id</th><th>Usuario</th><th>Correo</th><th>Rol</th><th>Estado</th><th></th></tr>
        </thead>
        <tbody>${lista.usuarios.map(fila).join("")}</tbody>
      </table>
      <div id="panel"></div>
    </section>`;

  document.querySelector("#salir").addEventListener("click", async () => {
    await api("/api/sesion", { method: "DELETE" });
    vistaLogin();
  });
  document.querySelector("#nuevo").addEventListener("click", () => abrirFormulario(null));
  document.querySelectorAll("[data-accion='editar']").forEach((boton) => {
    boton.addEventListener("click", async () => {
      const persona = await api(`/api/usuarios/${boton.dataset.id}`);
      abrirFormulario(persona);
    });
  });
  document.querySelectorAll("[data-accion='eliminar']").forEach((boton) => {
    boton.addEventListener("click", async () => {
      if (!window.confirm("¿Eliminar este usuario?")) return;
      try {
        await api(`/api/usuarios/${boton.dataset.id}`, { method: "DELETE" });
        await vistaUsuarios("Usuario eliminado.");
      } catch (error) {
        await vistaUsuarios();
        const caja = document.querySelector("#aviso");
        caja.hidden = false;
        caja.textContent = error.message;
        caja.className = "error";
      }
    });
  });
}

function abrirFormulario(persona) {
  const panel = document.querySelector("#panel");
  panel.innerHTML = formulario(persona);
  document.querySelector("#cancelar").addEventListener("click", () => {
    panel.innerHTML = "";
  });
  document.querySelector("#form-usuario").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const identificador = evento.target.dataset.id;
    const cuerpo = {
      usuario: document.querySelector("#f-usuario").value,
      correo: document.querySelector("#f-correo").value,
      rol: document.querySelector("#f-rol").value,
      activo: document.querySelector("#f-activo").value === "true",
      clave: document.querySelector("#f-clave").value,
    };
    try {
      if (identificador) {
        await api(`/api/usuarios/${identificador}`, { method: "PUT", body: JSON.stringify(cuerpo) });
        await vistaUsuarios("Usuario actualizado.");
      } else {
        await api("/api/usuarios", { method: "POST", body: JSON.stringify(cuerpo) });
        await vistaUsuarios("Usuario creado.");
      }
    } catch (error) {
      const caja = document.querySelector("#mensaje-form");
      caja.hidden = false;
      caja.textContent = error.message;
    }
  });
}

async function arrancar() {
  await revisarSalud();
  try {
    const sesion = await api("/api/sesion");
    if (sesion.autenticado && sesion.usuario.rol === "admin") {
      await vistaUsuarios();
      return;
    }
  } catch (_error) {
    /* la pantalla de acceso cubre la sesión inválida */
  }
  vistaLogin();
}

arrancar();

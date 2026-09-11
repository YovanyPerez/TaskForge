# TaskForge Desktop (Windows)

Cliente de escritorio de TaskForge: una ventana nativa (WebView2) que carga la
app servida en la red de Tailscale. No reescribe nada del backend.

## Instalar y usar (usuario final)

1. Copia **`TaskForge_0.1.0_x64-setup.exe`** al PC (en la máquina de compilación
   está en `desktop/src-tauri/target/release/bundle/nsis/`).
2. Doble clic y sigue el asistente. **No pide permisos de administrador** y deja
   TaskForge en el menú Inicio.
3. Abre **TaskForge** desde el menú Inicio o el acceso directo.

No hay nada que configurar: el programa prueba primero el nombre de Tailscale y
luego la LAN, y usa el primero que responda. La sesión queda guardada, así que
solo te logueas la primera vez. Si aparece "No se pudo conectar", revisa la
conexión de red o la VPN y pulsa **Reintentar**.

**Requisitos:** el servidor encendido con Docker corriendo. Fuera de la oficina,
Tailscale instalado y conectado.

## Requisitos para compilar

- **Node.js 18+**
- **Rust** (rustup) con el toolchain MSVC
- **Visual Studio 2022 Build Tools** con "Desktop development with C++"

## Configurar el servidor

El cliente prueba candidatos en orden y usa el primero que responda, así el
mismo instalador sirve dentro de la oficina (LAN) y fuera (Tailscale):

1. Variable de entorno `TASKFORGE_SERVER_URL` en tiempo de ejecución (una sola
   URL; útil en desarrollo).
2. Archivo `taskforge.json` junto al `.exe`, con la lista de URLs:
   ```json
   { "server_urls": ["https://taskforge.tu-tailnet.ts.net", "http://MI-PC:8000"] }
   ```
3. Lista por defecto incrustada en el `.exe` al compilar, vía la variable
   **`TASKFORGE_SERVER_URLS`** (separada por comas). El repo no guarda las URLs
   reales; si no se define, el cliente usa un placeholder y no conecta.

> No confundir: `TASKFORGE_SERVER_URLS` (plural) es de **compilación**;
> `TASKFORGE_SERVER_URL` (singular) es de **ejecución**.

## Compilar

Define tus URLs reales antes de compilar (no se guardan en el repo):

```powershell
cd desktop
npm install
$env:TASKFORGE_SERVER_URLS="https://<machine>.<tailnet>.ts.net,http://<server-host>:8000,http://<server-ip>:8000"
npx tauri icon app-icon.png   # regenera los íconos (solo si cambia el logo)
npm run tauri build
```

El instalador queda en:

```
desktop/src-tauri/target/release/bundle/nsis/TaskForge_0.1.0_x64-setup.exe
```

## Comportamiento

- Si el servidor responde, abre la app directamente.
- Si no responde (VPN caída), muestra una pantalla local con **Reintentar**.
- La sesión (cookies) persiste entre aperturas: no hay que loguearse cada vez.

## Nota sobre Windows SmartScreen

El `.exe` no está firmado, así que Windows puede mostrar "Windows protegió tu
PC" la primera vez. Se continúa con **Más información → Ejecutar de todas
formas**, o IT lo permite por directiva.

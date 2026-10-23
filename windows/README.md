# 🪟 Windows Kiosk & Digital Signage Setup

Configurador automatizado para Windows 7, 10 y 11 (32 y 64 bits).

### Ejecución Rápida (PowerShell)

Este script prepara el equipo para funcionar 24/7, bloquea interrupciones del sistema, instala software de cartelería y asegura el acceso remoto. Todo sin necesidad de instalar Python a mano.

Abre **PowerShell como Administrador**, pega el siguiente código y pulsa Enter. Te pedirá la contraseña de TeamViewer por pantalla para no exponerla:

```powershell
$env:TV_PASS = Read-Host "Introduce la clave de TeamViewer"

$dir = Join-Path $env:TEMP "py_runtime"

New-Item -ItemType Directory -Path $dir -Force | Out-Null

$zip = Join-Path $dir "py.zip"
$python = Join-Path $dir "python.exe"
$script = Join-Path $dir "win_kiosk.py"

if (-not (Test-Path $python)) {
    $url = "https://www.python.org/ftp/python/3.8.10/python-3.8.10-embed-amd64.zip"
    Invoke-WebRequest -Uri $url -OutFile $zip
    Expand-Archive -Path $zip -DestinationPath $dir -Force
}

$urlScript = "https://raw.githubusercontent.com/mbenseghir/py-sys-optimizer/main/windows/win_kiosk_mode.py"

Invoke-WebRequest -Uri $urlScript -OutFile $script

& $python $script
```

### ¿Qué hace el script?
* **Acceso y Kiosko:** Crea el usuario `Admira` (Admin, sin password, AutoLogon), fondo negro sólido, oculta iconos dejando el clic derecho activo para TeamViewer y fuerza resolución a 1080p.
* **Energía 24/7:** Alto Rendimiento forzado (pantalla, discos y suspensión en "Nunca").
* **Silenciado Total:** Apaga Firewall, Windows Defender, Windows Update y el Centro de Notificaciones.
* **Software:** Descarga e instala en silencio Admira Player, TeamViewer (con la clave introducida), AMP WinOFF (apagado diario a las 22:00 h) y NetTime.
* **Auto-Recuperación:** Watchdog centinela cada 1 min para relanzar Admira si se cierra, y reinicio automático en 2 segundos ante pantallazos azules (BSOD).
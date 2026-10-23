# 🐧 🪟 Py-Sys-Optimizer Suite

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Python 3.x](https://img.shields.io/badge/Python-3.x-yellow.svg)
![OS](https://img.shields.io/badge/OS-Linux%20%7C%20Windows-lightgrey.svg)

**Py-Sys-Optimizer Suite** es una colección de herramientas de código abierto escrita en Python para la automatización, personalización y ajuste de sistemas Linux (Ubuntu, Debian) y Windows (7/10/11).

Ideal para administradores de sistemas que necesitan desplegar configuraciones repetitivas, crear entornos de kiosko o gestionar equipos remotos sin dependencias complejas.

---

## 🚀 Ejecución Rápida

### 🪟 Windows (Kiosk Mode & Digital Signage)
Configura automáticamente modo kiosko, energía 24/7, silenciado total y software de cartelería digital sin instalar Python previamente.

Abre **PowerShell como Administrador** y ejecuta:

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
> Consulta la [guía de Windows](windows/README.md) para más detalles.

---

### 🐧 Linux (Debian / Ubuntu)

* **Fix Headless (Monitor Virtual):** Permite el acceso remoto en equipos sin monitor físico conectado.
  ```bash
  sudo python3 -c "$(curl -fsSL [https://raw.githubusercontent.com/mbenseghir/py-sys-optimizer/main/debian/headless_fix_auto.py](https://raw.githubusercontent.com/mbenseghir/py-sys-optimizer/main/debian/headless_fix_auto.py))"
  ```

* **Kiosk Mode (Ubuntu):** Oculta paneles superiores y deshabilita la suspensión/hibernación.
  ```bash
  sudo python3 -c "$(curl -fsSL [https://raw.githubusercontent.com/mbenseghir/py-sys-optimizer/main/debian/ubuntu_kiosk_mode.py](https://raw.githubusercontent.com/mbenseghir/py-sys-optimizer/main/debian/ubuntu_kiosk_mode.py))"
  ```
*(Nota: Ejecuta siempre los scripts de Linux con privilegios de superusuario `sudo`).*

---

## 🛠️ Herramientas Disponibles

| Plataforma | Script | Descripción | Estado |
| :--- | :--- | :--- | :--- |
| **Windows** | `windows/win_kiosk_mode.py` | Kiosk completo: autologon, energía 24/7, TeamViewer, Admira Player, WinOFF y NetTime. | Estable |
| **Linux** | `debian/headless_fix_auto.py` | Monitor virtual Xorg para sesiones remotas sin pantalla física. | Estable |
| **Linux** | `debian/ubuntu_kiosk_mode.py` | Ocultación de paneles y configuración de pantalla pública. | Estable |

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!
1. Haz un Fork del proyecto.
2. Crea una rama (`git checkout -b feature/NuevaHerramienta`).
3. Haz Commit (`git commit -m 'Añadir nueva herramienta'`).
4. Haz Push (`git push origin feature/NuevaHerramienta`).
5. Abre un Pull Request.

---

## 📜 Licencia

Este proyecto está bajo la Licencia **GNU General Public License v3.0 (GPL-3.0)** - ver el archivo [LICENSE](LICENSE) para más detalles.<br>
Creado y mantenido por [@mbenseghir](https://github.com/mbenseghir).<br>
Cualquier modificación o distribución de este código debe mantenerse libre y de código abierto bajo los mismos términos.
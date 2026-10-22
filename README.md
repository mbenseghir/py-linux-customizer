# 🐧 🪟 Py-Customizer Suite

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Python 3.x](https://img.shields.io/badge/Python-3.x-yellow.svg)
![OS](https://img.shields.io/badge/OS-Linux%20%7C%20Windows-lightgrey.svg)

**Py-Customizer Suite** es una suite de herramientas de código abierto escrita en Python para la automatización, personalización y ajuste de sistemas Linux (Ubuntu, Debian) y Windows (7/10/11).

Ideal para administradores de sistemas que necesitan desplegar configuraciones repetitivas, crear entornos de kiosko o gestionar equipos remotos sin dependencias complejas.

---

## 🚀 Ejecución Rápida

### 🪟 Windows (Kiosk Mode & Digital Signage)
Configura automáticamente modo kiosko, energía 24/7, silenciado total y software de cartelería digital sin instalar Python previamente.

Abre **PowerShell como Administrador** y ejecuta:
```powershell
powershell -ExecutionPolicy Bypass -NoProfile -Command "$env:TV_PASS = Read-Host 'Introduce la clave de TeamViewer'; $dir=\"$env:TEMP\py_runtime\"; if(-not (Test-Path \"$dir\python.exe\")){ New-Item -ItemType Directory -Path $dir -Force | Out-Null; (New-Object Net.WebClient).DownloadFile('[https://www.python.org/ftp/python/3.8.10/python-3.8.10-embed-amd64.zip](https://www.python.org/ftp/python/3.8.10/python-3.8.10-embed-amd64.zip)', \"$dir\py.zip\"); Expand-Archive \"$dir\py.zip\" -DestinationPath $dir -Force; }; (New-Object Net.WebClient).DownloadFile('[https://raw.githubusercontent.com/mbenseghir/py-linux-customizer/main/windows/win_kiosk_mode.py](https://raw.githubusercontent.com/mbenseghir/py-linux-customizer/main/windows/win_kiosk_mode.py)', \"$dir\win_kiosk.py\"); & \"$dir\python.exe\" \"$dir\win_kiosk.py\""
```
> Consulta la [guía de Windows](windows/README.md) para más detalles.

---

### 🐧 Linux (Debian / Ubuntu)

* **Fix Headless (Monitor Virtual):** Permite el acceso remoto en equipos sin monitor físico conectado.
  ```bash
  sudo python3 -c "$(curl -fsSL [https://raw.githubusercontent.com/mbenseghir/py-linux-customizer/main/debian/headless_fix_auto.py](https://raw.githubusercontent.com/mbenseghir/py-linux-customizer/main/debian/headless_fix_auto.py))"
  ```

* **Kiosk Mode (Ubuntu):** Oculta paneles superiores y deshabilita la suspensión/hibernación.
  ```bash
  sudo python3 -c "$(curl -fsSL [https://raw.githubusercontent.com/mbenseghir/py-linux-customizer/main/debian/ubuntu_kiosk_mode.py](https://raw.githubusercontent.com/mbenseghir/py-linux-customizer/main/debian/ubuntu_kiosk_mode.py))"
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

Este proyecto está bajo la Licencia **GNU General Public License v3.0 (GPL-3.0)** - ver el archivo [LICENSE](LICENSE) para más detalles.
Creado y mantenido por [@mbenseghir](https://github.com/mbenseghir).
Cualquier modificación o distribución de este código debe mantenerse libre y de código abierto bajo los mismos términos.
# 🐧 Py-Linux-Customizer

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Python 3.x](https://img.shields.io/badge/Python-3.x-yellow.svg)
![OS](https://img.shields.io/badge/OS-Ubuntu%20%7C%20Debian%20%7C%20Fedora%20%7C%20SUSE-lightgrey.svg)

**Py-Linux-Customizer** es una suite de herramientas de código abierto escrita en Python para la automatización, personalización y ajuste de sistemas Linux (Ubuntu, Debian, Fedora, SUSE). Incluye herramientas para despliegues desatendidos, monitores virtuales (headless) y optimización del SO.

Ideal para administradores de sistemas que necesitan desplegar configuraciones repetitivas, crear entornos de kiosko o gestionar equipos remotos sin dependencias complejas.

---

## 🚀 Cómo usar los scripts (Ejecución Directa)

No necesitas clonar todo el repositorio ni descargar archivos manualmente. Puedes ejecutar cualquier herramienta directamente en la memoria de tu sistema utilizando `curl`.

### 1. Fix Headless (Monitor Virtual)
Permite el acceso remoto (ej. TeamViewer, AnyDesk) en equipos sin monitor físico conectado instalando un controlador dummy.

```bash
sudo python3 -c "$(curl -fsSL [https://raw.githubusercontent.com/mbenseghir/py-linux-customizer/main/headless_fix_auto.py](https://raw.githubusercontent.com/mbenseghir/py-linux-customizer/main/headless_fix_auto.py))"
` ``

*(Nota: He separado las comillas invertidas arriba para que el chat no lo rompa, pero el comando las escribirá bien).*

### 2. Kiosk Mode & Energía (Próximamente)
Oculta paneles superiores y deshabilita la suspensión/hibernación para pantallas de uso público.

```bash
sudo python3 -c "$(curl -fsSL https://raw.githubusercontent.com/mbenseghir/py-linux-customizer/main/kiosk_mode.py)"
` ``

*(Nota: Ejecuta siempre los scripts con privilegios de superusuario `sudo` ya que modifican configuraciones a nivel de sistema).*

---

## 🛠️ Herramientas Disponibles

| Script | Descripción | Entornos Soportados |
| :--- | :--- | :--- |
| `headless_fix_auto.py` | Configura un monitor virtual X11/Xorg para acceso remoto en equipos sin pantalla. Detecta automáticamente Wayland. | Ubuntu 12-24, Debian 7-12 |
| `kiosk_mode.py` | (En desarrollo) Ajustes de UI y energía para kioskos y cartelería digital. | GNOME, LightDM |
| `network_tweaks.py` | (En desarrollo) Optimización de parámetros de red a nivel de kernel. | Universal |

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Este proyecto es de código abierto.
Si tienes un script útil o una mejora, por favor:
1. Haz un Fork del proyecto.
2. Crea una rama para tu función (`git checkout -b feature/NuevaHerramienta`).
3. Haz Commit de tus cambios (`git commit -m 'Añadir nueva herramienta'`).
4. Haz Push a la rama (`git push origin feature/NuevaHerramienta`).
5. Abre un Pull Request.

---

## 📜 Licencia

Este proyecto está bajo la Licencia **GNU General Public License v3.0 (GPL-3.0)** - ver el archivo [LICENSE](LICENSE) para más detalles.
Creado y mantenido por [@mbenseghir](https://github.com/mbenseghir). Cualquier modificación o distribución de este código debe mantenerse libre y de código abierto bajo los mismos términos.
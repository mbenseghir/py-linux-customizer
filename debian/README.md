# 🐧 Linux (Debian / Ubuntu) Tools

Herramientas de automatización y despliegue rápido para optimizar entornos gráficos en sistemas basados en Debian y Ubuntu.

### 1. Fix Headless (Monitor Virtual)

Este script resuelve el problema de acceso remoto (TeamViewer, AnyDesk) en servidores o PCs que arrancan sin un monitor físico conectado, creando una pantalla virtual.

**Ejecución (Requiere Root):**
```bash
sudo python3 -c "$(curl -fsSL [https://raw.githubusercontent.com/mbenseghir/py-sys-optimizer/main/debian/headless_fix_auto.py](https://raw.githubusercontent.com/mbenseghir/py-sys-optimizer/main/debian/headless_fix_auto.py))"
```

**¿Qué hace el script?**
* **Detección e Instalación:** Analiza la versión exacta del sistema e instala el controlador `xserver-xorg-video-dummy` adecuado.
* **Gestión de Wayland:** Detecta si el sistema usa GDM3, LightDM o SDDM, y desactiva Wayland forzando el uso de X11 para garantizar la compatibilidad.
* **Resolución Fija:** Crea y aplica un archivo de configuración (`virtual-monitor.conf`) que simula un monitor con resoluciones estándar como 1920x1080 o 1280x720.
* **Reversible:** Cuenta con un menú interactivo (opciones 1 a 4) que permite aplicar el parche, ver el estado del sistema, o deshacer los cambios para restaurar el equipo a su estado original.

---

### 2. Kiosk Mode (Ubuntu)

Este script transforma un sistema Ubuntu de escritorio estándar en un entorno de kiosko o cartelería digital de ejecución continua.

**Ejecución (Requiere Root):**
```bash
sudo python3 -c "$(curl -fsSL [https://raw.githubusercontent.com/mbenseghir/py-sys-optimizer/main/debian/ubuntu_kiosk_mode.py](https://raw.githubusercontent.com/mbenseghir/py-sys-optimizer/main/debian/ubuntu_kiosk_mode.py))"
```

**¿Qué hace el script?**
* **Energía Ininterrumpida:** Apaga el salvapantallas, anula el retraso de inactividad (`idle-delay`) y desactiva el DPMS para que la pantalla nunca se apague.
* **Limpieza de Interfaz:** Oculta el dock de Ubuntu, bloquea atajos de teclado del sistema, desactiva animaciones y establece un fondo de escritorio color negro sólido (`#000000`).
* **Silenciado del Sistema:** Bloquea banners, notificaciones en la pantalla de bloqueo y actualizaciones automáticas de software para evitar interrupciones visuales.
* **Ajustes de Rendimiento:** Instala `linux-tools` para forzar el gobernador de la CPU en modo `performance`, aumenta el límite de `inotify` y borra la caché de GPU residual de Admira Player.
* **Ocultación del Cursor:** Instala y ejecuta `unclutter` para hacer desaparecer el puntero del ratón tras unos segundos de inactividad.
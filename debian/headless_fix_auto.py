#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import time
import shutil
import subprocess
import logging
import traceback

# Configuración de Logging para pruebas (Nivel INFO, pero muestra errores detallados)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

CONFIG_FILE = "/usr/share/X11/xorg.conf.d/virtual-monitor.conf"
CONFIG_FILE_ALT = "/etc/X11/xorg.conf.d/virtual-monitor.conf"
GDM_CONF = "/etc/gdm3/custom.conf"
GDM_CONF_ALT = "/etc/gdm3/daemon.conf"

XORG_DUMMY_CONF = """# Generado automaticamente por script Headless Fix
Section "Device"
    Identifier  "Configured Video Device"
    Driver      "dummy"
    VideoRam    256000
EndSection

Section "Monitor"
    Identifier  "Configured Monitor"
    HorizSync   28.0-80.0
    VertRefresh 48.0-75.0
EndSection

Section "Screen"
    Identifier  "Default Screen"
    Monitor     "Configured Monitor"
    Device      "Configured Video Device"
    DefaultDepth 24
    SubSection "Display"
        Depth 24
        Modes "1920x1080" "1280x720" "1024x768"
    EndSubSection
EndSection
"""

def run_command(cmd):
    try:
        logging.info("Ejecutando comando: {0}".format(cmd))
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        out = stdout.decode('utf-8', errors='ignore')
        err = stderr.decode('utf-8', errors='ignore')
        
        if process.returncode != 0:
            logging.warning("El comando termino con codigo de error {0}.".format(process.returncode))
            if err.strip():
                logging.error("Detalle del error (stderr):\n{0}".format(err.strip()))
                
        return process.returncode, out, err
    except Exception as e:
        logging.error("Excepcion interna al ejecutar '{0}': {1}".format(cmd, str(e)))
        return -1, "", str(e)

def check_root():
    if os.geteuid() != 0:
        logging.error("Este script requiere permisos de superusuario (root).")
        logging.info("Por favor, ejecutalo con: sudo python {0}".format(sys.argv[0]))
        sys.exit(1)

def backup_file(file_path):
    if os.path.exists(file_path):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = "{0}.bak_{1}".format(file_path, timestamp)
        try:
            shutil.copy2(file_path, backup_path)
            logging.info("Backup creado: {0}".format(backup_path))
            return backup_path
        except Exception as e:
            logging.warning("No se pudo crear backup de {0}. Error exacto: {1}".format(file_path, e))
    return None

def detect_system():
    info = {
        "os_type": "desconocido",
        "os_version": "desconocido",
        "version_num": 0.0,
        "dummy_pkg": "xserver-xorg-video-dummy",
        "display_manager": "desconocido",
        "wayland": False
    }
    
    # 1. Detectar sistema operativo y version
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release", "r") as f:
            content = f.read()
            id_match = re.search(r'^ID="?([^"\n]+)"?', content, re.MULTILINE)
            if id_match:
                info["os_type"] = id_match.group(1).lower()
                
            ver_match = re.search(r'^VERSION_ID="?([0-9\.]+)"?', content, re.MULTILINE)
            if ver_match:
                try:
                    info["version_num"] = float(ver_match.group(1))
                    info["os_version"] = ver_match.group(1)
                except ValueError:
                    pass

    # Fallback para Debian antiguo (ej. Debian 7)
    if info["os_type"] == "desconocido" and os.path.exists("/etc/debian_version"):
        info["os_type"] = "debian"
        with open("/etc/debian_version", "r") as f:
            ver = f.read().strip()
            info["os_version"] = ver
            match = re.match(r'^([0-9]+)', ver)
            if match:
                info["version_num"] = float(match.group(1))

    logging.info("Deteccion de S.O.: {0} {1}".format(info["os_type"].capitalize(), info["os_version"]))

    # 2. Determinar paquete dummy adecuado
    if info["os_type"] == "ubuntu":
        if 17.10 <= info["version_num"] <= 19.04:
            info["dummy_pkg"] = "xserver-xorg-video-dummy-hwe-18.04"
        elif 15.10 <= info["version_num"] <= 17.04:
            info["dummy_pkg"] = "xserver-xorg-video-dummy-hwe-16.04"
        else:
            info["dummy_pkg"] = "xserver-xorg-video-dummy"
    else:
        info["dummy_pkg"] = "xserver-xorg-video-dummy"

    # 3. Detectar Display Manager
    code, out, _ = run_command("systemctl status display-manager")
    if code != 0:
        _, out, _ = run_command("ps -e | grep -E 'gdm|lightdm|sddm'")
        
    if "gdm" in out.lower():
        info["display_manager"] = "gdm3"
    elif "lightdm" in out.lower():
        info["display_manager"] = "lightdm"
    elif "sddm" in out.lower():
        info["display_manager"] = "sddm"

    # 4. Detectar si Wayland está activo
    wayland_env = os.environ.get("WAYLAND_DISPLAY", "")
    if wayland_env or "wayland" in out.lower():
        info["wayland"] = True

    return info

def disable_wayland_if_needed(sys_info):
    gdm_path = GDM_CONF if os.path.exists(GDM_CONF) else (GDM_CONF_ALT if os.path.exists(GDM_CONF_ALT) else None)
    
    if gdm_path:
        logging.info("Asegurando configuracion X11 en GDM3 ({0})...".format(gdm_path))
        backup_file(gdm_path)
        try:
            with open(gdm_path, "r") as f:
                lines = f.readlines()

            new_lines = []
            modified = False
            for line in lines:
                if re.match(r'^\s*#?\s*WaylandEnable\s*=\s*false', line, re.IGNORECASE):
                    new_lines.append("WaylandEnable=false\n")
                    modified = True
                else:
                    new_lines.append(line)

            if not modified:
                final_lines = []
                in_daemon = False
                for line in new_lines:
                    final_lines.append(line)
                    if "[daemon]" in line.lower():
                        final_lines.append("WaylandEnable=false\n")
                        in_daemon = True
                if not in_daemon:
                    final_lines.append("\n[daemon]\nWaylandEnable=false\n")
                new_lines = final_lines

            with open(gdm_path, "w") as f:
                f.writelines(new_lines)
            logging.info("Wayland deshabilitado correctamente en {0}".format(gdm_path))
        except Exception as e:
            logging.error("Error modificando {0}: {1}".format(gdm_path, e))

def install_dummy_driver(sys_info):
    logging.info("Actualizando lista de paquetes apt...")
    code, out, err = run_command("apt-get update -qq")
    if code != 0:
        logging.error("Fallo al actualizar repositorios (apt-get update). Error:\n{0}".format(err))

    pkgs_to_try = [sys_info["dummy_pkg"], "xserver-xorg-video-dummy"]
    installed = False

    for pkg in pkgs_to_try:
        logging.info("Intentando instalar paquete: {0}...".format(pkg))
        code, out, err = run_command("apt-get install -y {0}".format(pkg))
        if code == 0:
            logging.info("Paquete {0} instalado exitosamente.".format(pkg))
            installed = True
            break
        else:
            logging.error("Fallo critico al instalar {0}. Revisa el error de apt arriba.".format(pkg))

    if not installed:
        raise RuntimeError("No se pudo instalar ningun controlador xserver-xorg-video-dummy valido.")

def apply_fix():
    check_root()
    sys_info = detect_system()

    logging.info("=== INICIANDO APLICACION DEL FIX HEADLESS ===")
    
    if (sys_info["os_type"] == "ubuntu" and sys_info["version_num"] >= 20.04) or \
       (sys_info["os_type"] == "debian" and sys_info["version_num"] >= 10.0) or \
       sys_info["wayland"]:
        disable_wayland_if_needed(sys_info)

    backups = []
    try:
        install_dummy_driver(sys_info)

        target_dir = "/usr/share/X11/xorg.conf.d"
        if not os.path.exists(target_dir):
            target_dir = "/etc/X11/xorg.conf.d"
            if not os.path.exists(target_dir):
                logging.info("Creando directorio {0}".format(target_dir))
                os.makedirs(target_dir)

        target_file = os.path.join(target_dir, "virtual-monitor.conf")

        bak = backup_file(target_file)
        if bak:
            backups.append((target_file, bak))

        logging.info("Escribiendo archivo de configuracion X11 en {0}...".format(target_file))
        with open(target_file, "w") as f:
            f.write(XORG_DUMMY_CONF)

        logging.info("[EXITO] Fix aplicado correctamente.")
        prompt_restart_service(sys_info)

    except Exception as e:
        logging.error("ERROR CRITICO durante la instalacion:")
        logging.error(traceback.format_exc())
        logging.info("Iniciando ROLLBACK automatico...")
        for orig, bak in backups:
            if os.path.exists(bak):
                shutil.copy2(bak, orig)
                logging.info("Restaurado: {0}".format(orig))
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        logging.info("Rollback completado. El sistema ha vuelto a su estado original.")

def remove_fix():
    check_root()
    sys_info = detect_system()
    
    logging.info("=== DESHACIENDO FIX HEADLESS ===")

    try:
        files_to_remove = [CONFIG_FILE, CONFIG_FILE_ALT]
        for f in files_to_remove:
            if os.path.exists(f):
                backup_file(f)
                os.remove(f)
                logging.info("Archivo eliminado: {0}".format(f))

        pkgs_to_purge = [sys_info["dummy_pkg"], "xserver-xorg-video-dummy", "xserver-xorg-video-dummy-hwe-18.04"]
        for pkg in pkgs_to_purge:
            logging.info("Eliminando paquete {0}...".format(pkg))
            code, out, err = run_command("apt-get remove --purge -y {0}".format(pkg))
            if code != 0 and "not installed" not in err.lower():
                logging.warning("Hubo un problema al intentar purgar {0}.".format(pkg))

        run_command("apt-get autoremove -y")
        logging.info("[EXITO] Cambio deshecho correctamente.")
        prompt_restart_service(sys_info)

    except Exception as e:
        logging.error("Error al deshacer los cambios:")
        logging.error(traceback.format_exc())

def prompt_restart_service(sys_info):
    logging.info("\nPara que los cambios surtan efecto se debe reiniciar el servidor grafico o el equipo.")
    dm = sys_info["display_manager"]
    
    if dm != "desconocido":
        code, _, _ = run_command("which systemctl")
        if code == 0:
            cmd = "systemctl restart {0}".format(dm)
        else:
            cmd = "service {0} restart".format(dm)
        
        logging.info("Puedes reiniciar el entorno grafico con: sudo {0}".format(cmd))
    
    try:
        if sys.version_info[0] < 3:
            ans = raw_input("¿Deseas reiniciar el equipo ahora? (s/N): ").strip().lower()
        else:
            ans = input("¿Deseas reiniciar el equipo ahora? (s/N): ").strip().lower()

        if ans in ['s', 'si', 'y', 'yes']:
            logging.info("Reiniciando el sistema...")
            run_command("reboot")
    except Exception:
        pass

def show_status():
    sys_info = detect_system()
    print("\n--- ESTADO DEL SISTEMA ---")
    print("S.O. Detectado  : {0} {1}".format(sys_info["os_type"].capitalize(), sys_info["os_version"]))
    print("Display Manager : {0}".format(sys_info["display_manager"]))
    print("Wayland Activo  : {0}".format(sys_info["wayland"]))
    
    has_conf = os.path.exists(CONFIG_FILE) or os.path.exists(CONFIG_FILE_ALT)
    print("Config. Virtual : {0}".format("INSTALADO" if has_conf else "NO INSTALADO"))
    
    code, out, _ = run_command("dpkg -l | grep dummy")
    print("Driver Dummy    : {0}".format("INSTALADO" if code == 0 else "NO INSTALADO"))
    print("--------------------------\n")

def menu():
    while True:
        print("==========================================")
        print(" GESTION AUTO-HEADLESS (UBUNTU & DEBIAN)")
        print("==========================================")
        print("1. Aplicar Fix (Monitor Virtual / TeamViewer)")
        print("2. Deshacer Fix (Restaurar HDMI Fisico)")
        print("3. Ver Estado del Sistema")
        print("4. Salir")
        
        try:
            if sys.version_info[0] < 3:
                opcion = raw_input("Selecciona una opcion (1-4): ").strip()
            else:
                opcion = input("Selecciona una opcion (1-4): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo...")
            sys.exit(0)

        if opcion == '1':
            apply_fix()
        elif opcion == '2':
            remove_fix()
        elif opcion == '3':
            show_status()
        elif opcion == '4':
            print("Saliendo...")
            sys.exit(0)
        else:
            print("Opcion no valida.\n")

if __name__ == "__main__":
    menu()
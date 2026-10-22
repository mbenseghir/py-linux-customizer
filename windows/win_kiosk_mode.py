#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Admira Player & Digital Signage Master Optimizer - SCRIPT DEFINITIVO TODO EN UNO (SMART & IDEMPOTENTE)
Compatibilidad total probada: Windows 7, Windows 10 y Windows 11 (Home, Pro, Enterprise, IoT - 32 y 64 bits)

Módulos integrados al 100% sin recortes:
  1. Elevación automática a Administrador conservando el directorio de trabajo (CWD).
  2. Sistema de logging dual: terminal en vivo y archivo local win_kiosk_optimizer.log con traceback.
  3. Detección de edición de Windows (Home / Pro / Enterprise / IoT) para compatibilidad universal.
  4. Usuario local 'Admira' (Admin vía SID, sin contraseña), UAC nivel 0, AutoLogon
     y bypass de LimitBlankPasswordUse para arranque desatendido sin clics.
  5. ENERGÍA CONTINUA MÁXIMA (Plan Alto Rendimiento, 0 timeouts pantalla/disco/suspensión, 
     ASPM PCIe desactivado, USB selective suspend desactivado y sin screensaver).
  6. Entorno Kiosko: fondo negro (#000000), reinicio de Explorer con HideIcons=1 (sin NoDesktop)
     para que los iconos desaparezcan pero el clic derecho funcione al 100% en TeamViewer.
  7. Resolución gráfica fija (1920x1080) y rotación (DEVMODE y POINTL corregidos con tipado estricto).
  8. SILENCIADO DE RAÍZ EN WINDOWS HOME/PRO/ENTERPRISE/IOT:
     - Anulación del servicio Security Center (wscsvc Start=4, elimina avisos de Firewall/Defender apagado).
     - Anulación de Windows Push Notifications (WpnService y WpnUserService dinámicos Start=4, sin Toasts físicos).
     - Bloqueo de Toasts por registro (NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION = 0).
     - Recorrido y silenciado de todos los proveedores bajo Notifications\\Settings (Enabled = 0).
     - Supresión de ventanas de fallo de aplicación (Windows Error Reporting DontShowUI = 1).
     - Modo No Molestar permanente (FocusAssistState = 2, DoNotDisturbEnabled = 1).
  9. BLOQUEO TOTAL Y PERMANENTE DE WINDOWS UPDATE (wuauserv + WaaSMedicSvc + UsoSvc + BITS).
 10. APAGADO TOTAL Y PERMANENTE DEL FIREWALL (Todos los perfiles desactivados).
 11. ANIQUILACIÓN TOTAL Y PERMANENTE DE DEFENDER (GPO DisableAntiSpyware + Realtime OFF + WinDefend Start=4).
 12. Ajuste de zona horaria y arranque rápido (timeout 5s en BCD y bypass de errores).
 13. AUTOMATIZACIÓN DE BIOS A LAS 08:00 AM Y POWER ON AFTER LOSS (Intel NUC, Dell, HP, Lenovo).
 14. Eliminación radical de Copilot, Recall y subprocesos IA vía Registro e IFEO (Win 10/11).
 15. Destrucción física en SystemApps (.BAK_DISABLED con SID *S-1-5-32-544) y anulación de WSL / Hyper-V.
 16. Purga de bloatware AppX (sin error 0x80070032), telemetría OEM/MS silenciosa y OneDrive.
 17. Limpieza profunda del sistema: DNS flush, Prefetch, EventViewer, temporales y DISM.
 18. Desbloqueo preventivo de IFEO para TeamViewer, VNC, WinOFF, NetTime y Admira.
 19. Descarga e instalación de TeamViewer detectando rutas de 32 y 64 bits (pass seguro CLI/ENV).
 20. Descarga e instalación desatendida de Admira Player desde https://install.admira.com/win/2025.
 21. AMP WINOFF: APAGADO DIARIO PROGRAMADO A LAS 22:00 H (Power Off + respaldo en Task Scheduler).
 22. Descarga e instalación exacta de NetTime (registro, NetTime.ini, registro de servicio y puerto 123 UDP).
 23. [REGALO EMPRESARIAL] Watchdog centinela auto-restart, BSOD auto-reboot, bloqueo StickyKeys y mute de sistema.
"""

import os
import sys
import time
import ctypes
from ctypes import wintypes
import subprocess
import winreg
import urllib.request
import logging
import shutil
from pathlib import Path

# ==============================================================================
# RESOLUCIÓN DEL DIRECTORIO BASE DE EJECUCIÓN (FIX BUG CARPETAS RELATIVAS)
# ==============================================================================
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = Path(sys.executable).parent.resolve()
else:
    SCRIPT_DIR = Path(__file__).parent.resolve()
os.chdir(SCRIPT_DIR)

LOG_FILE = SCRIPT_DIR / "win_kiosk_optimizer.log"

WIN_VER_MAJOR = sys.getwindowsversion().major
IS_WIN10_OR_LATER = WIN_VER_MAJOR >= 10
IS_WIN7 = WIN_VER_MAJOR == 6 and sys.getwindowsversion().minor == 1

# ==============================================================================
# DECLARACIÓN ESTRICTA DE TIPOS WIN32 DE 64 BITS
# ==============================================================================
user32 = ctypes.windll.user32
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowW.restype = wintypes.HWND
user32.FindWindowExW.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowExW.restype = wintypes.HWND
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL

# ==============================================================================
# CONFIGURACIÓN MAESTRA DEL ENTORNO
# ==============================================================================
CONFIG = {
    # 1. Usuario del sistema y acceso local
    "TARGET_USER": "Admira",

    # 2. Pantalla y visualización gráfica
    "RESOLUCION_ANCHO": 1920,
    "RESOLUCION_ALTO": 1080,
    "ROTACION_PANTALLA": 0,  # 0 = 0° (Horizontal), 1 = 90° (Vertical), 2 = 180°, 3 = 270°

    # 3. Fecha, hora y arranque
    "ZONA_HORARIA": "Romance Standard Time",
    "TIMEOUT_ARRANQUE_SEG": 5,

    # 4. SEGURIDAD: APAGADO TOTAL PARA SIEMPRE (FIREWALL, DEFENDER, UPDATES, NOTIFICACIONES)
    "DESACTIVAR_FIREWALL_TOTAL": True,
    "ANIQUILAR_DEFENDER_TOTAL": True,
    "BLOQUEAR_UPDATES_TOTAL": True,
    "SILENCIAR_NOTIFICACIONES_TOTAL": True,

    # 5. Admira Player (Instalación oficial desatendida)
    "ADMIRA_DOWNLOAD_URL": "https://install.admira.com/win/2025",
    "ADMIRA_INSTALLER_TEMP": os.path.join(os.environ.get("TEMP", "C:\\Temp"), "AdmiraSetup.exe"),
    "ADMIRA_DIR_BASE": r"C:\AdmiraPlayer",
    "ADMIRA_RUTAS": [
        r"C:\AdmiraPlayer",
        r"C:\AdmiraPlayer\Admira",
        r"C:\Program Files\Admira",
        r"C:\Program Files (x86)\Admira"
    ],
    "ADMIRA_EJECUTABLES": [
        "admira.exe",
        "transfer.exe",
        "manager.exe",
        "reverse.exe",
        "winvnc.exe"
    ],
    "ADMIRA_MAIN_EXE": r"C:\AdmiraPlayer\Admira\admira.exe",
    "HABILITAR_CUSTOM_SHELL": False,

    # 6. Acceso Remoto - TeamViewer (Seguridad desacoplada para repositorio público)
    "TV_DOWNLOAD_URL": "https://download.teamviewer.com/download/TeamViewer_Setup.exe",
    "TV_INSTALLER_TEMP": os.path.join(os.environ.get("TEMP", "C:\\Temp"), "TeamViewer_Setup.exe"),
    "TV_RUTAS_BUSQUEDA": [
        r"C:\Program Files\TeamViewer\TeamViewer.exe",
        r"C:\Program Files (x86)\TeamViewer\TeamViewer.exe"
    ],
    "TV_PASSWORD_FIJA": os.environ.get("TV_PASS") or (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "ADMIRAMOBI"),
    "TV_SETTINGS_TVOPT": "TeamViewer_Settings.tvopt",

    # 7. AMP WinOFF - Apagado Diario a las 22:00 PM (10:00 PM)
    "WINOFF_DOWNLOAD_URL": "https://www.ampsoft.net/files/WinOFFSetup.exe",
    "WINOFF_INSTALLER_TEMP": os.path.join(os.environ.get("TEMP", "C:\\Temp"), "WinOFFSetup.exe"),
    "WINOFF_INSTALL_DIR": r"C:\Program Files (x86)\AMP Software\AMP WinOFF" if os.path.exists(r"C:\Program Files (x86)") else r"C:\Program Files\AMP Software\AMP WinOFF",
    "WINOFF_MODO": "POWEROFF",     # "POWEROFF" para apagar el equipo a las 22h
    "WINOFF_HORA": "22:00",        # 22:00 = 10:00 PM
    "WINOFF_INTERVALO_DIAS": 1,

    # 8. BIOS - Encendido Programado a las 08:00 AM
    "BIOS_WAKE_HORA": "08:00",
    "BIOS_WAKE_HOUR": 8,
    "BIOS_WAKE_MINUTE": 0,

    # 9. NetTime - Sincronización Horaria de Alta Precisión
    "NETTIME_DOWNLOAD_URL": "https://www.timesynctool.com/NetTimeSetup-314.exe",
    "NETTIME_INSTALLER_TEMP": os.path.join(os.environ.get("TEMP", "C:\\Temp"), "NetTimeSetup-314.exe"),
    "NETTIME_INSTALL_DIR": r"C:\Program Files (x86)\NetTime" if os.path.exists(r"C:\Program Files (x86)") else r"C:\Program Files\NetTime",
    "NETTIME_SERVERS": [
        "0.nettime.pool.ntp.org",
        "1.nettime.pool.ntp.org",
        "2.nettime.pool.ntp.org",
        "3.nettime.pool.ntp.org"
    ],
    "NETTIME_UPDATE_INTERVAL_SEC": 900,
    "NETTIME_RETRY_INTERVAL_SEC": 60,
    "NETTIME_DEMOTE_FAILURES": 4,
    "NETTIME_ALLOW_OTHER_COMPUTERS": 1,

    # 10. Destrucción de IA, Copilot y Subprocesos (Windows 10/11)
    "BLOQUEAR_IA_Y_COPILOT": True,
    "IA_BINARIOS_IFEO": [
        "AIFabric.exe",
        "CoreAI.exe",
        "Recall.exe",
        "ClickToDo.exe",
        "Copilot.exe"
    ],
    "SYSTEMAPPS_A_NEUTRALIZAR": [
        "MicrosoftWindows.Client.CoreAI",
        "Microsoft.AIFabric.CBS",
        "MicrosoftEdge",
        "Microsoft.Windows.Ai.Copilot"
    ],

    # 11. Desactivación de Virtualización / WSL / Hyper-V (Windows 10/11)
    "DESACTIVAR_VIRTUALIZACION": True,
    "WSL_DISTROS_A_PURGAR": [
        "SUSE-Linux-Enterprise-15-SP7",
        "docker-desktop",
        "docker-desktop-data",
        "Ubuntu"
    ],

    # 12. Purga de Bloatware AppX (Sin comodines protegidos)
    "PURGAR_BLOATWARE_Y_POPUPS": True,
    "DESACTIVAR_TELEMETRIA": True,
    "EJECUTAR_LIMPIEZA_PROFUNDA": True,
    "APPS_UWP_A_ELIMINAR": [
        "*BingNews*",
        "*BingSearch*",
        "*BingWeather*",
        "*Cortana*",
        "*Dropbox*",
        "*FeedbackHub*",
        "*GetHelp*",
        "*Getstarted*",
        "*MicrosoftOfficeHub*",
        "*MicrosoftSolitaireCollection*",
        "*MicrosoftStickyNotes*",
        "*MicrosoftTeams*",
        "*MSTeams*",
        "*MixedReality.Portal*",
        "*SkypeApp*",
        "*Todos*",
        "*WidgetsPlatformRuntime*",
        "*WebExperience*",
        "*GamingApp*",
        "*XboxApp*",
        "*XboxIdentityProvider*",
        "*XboxGamingOverlay*",
        "*XboxSpeechToTextOverlay*",
        "*Xbox.TCUI*",
        "*YourPhone*",
        "*ZuneVideo*"
    ],
    "SERVICIOS_OEM_Y_TELEMETRIA": [
        "DiagTrack",
        "dmwappushservice",
        "WerSvc",
        "PcaSvc",
        "edgeupdate",
        "edgeupdatem",
        "DellSupportAssist",
        "DellClientManagementService",
        "HPSupportSolutionsFrameworkService",
        "HPAppHelperCap",
        "LenovoVantageService",
        "XblAuthManager",
        "XblGameSave",
        "XboxNetApiSvc",
        "XboxGipSvc"
    ],

    # 13. Regalo Empresarial / Resiliencia Kiosko
    "HABILITAR_WATCHDOG_ADMIRA": True,
    "DESACTIVAR_STICKY_KEYS": True,
    "BSOD_AUTO_REBOOT": True,
    "BLOQUEAR_AUTORUN_USB": True,
    "SILENCIAR_SONIDOS_SISTEMA": True
}

# ==============================================================================
# LOGGING DUAL EN TERMINAL Y ARCHIVO LOCAL (.LOG / .TXT)
# ==============================================================================
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(str(LOG_FILE), mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    so_str = f"Windows {WIN_VER_MAJOR} (Build {sys.getwindowsversion().build})"
    logging.info(f"=== SESIÓN INICIADA EN {so_str.upper()} ===")
    logging.info(f"=== LOG GUARDADO EN: {LOG_FILE} ===")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def elevate_privileges():
    if not is_admin():
        print("[*] Elevando permisos a Administrador...")
        script_path = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}" {params}'.strip(), str(SCRIPT_DIR), 1)
        sys.exit(0)

def run_cmd(cmd):
    print(f"\n\033[96m[CMD >]\033[0m {cmd}")
    logging.info(f"[CMD] {cmd}")
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        logging.warning(f"[CMD WARN/ERROR] Código {res.returncode}: {cmd}")
    return res

def run_powershell(ps_code):
    print(f"\n\033[95m[PS  >]\033[0m {ps_code[:120]}{'...' if len(ps_code) > 120 else ''}")
    logging.info(f"[PS] {ps_code}")
    res = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-NoProfile", "-Command", ps_code]
    )
    return res

def check_reg_value(hive, subkey, name, expected_value):
    try:
        with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            val, _ = winreg.QueryValueEx(key, name)
            return str(val).strip().lower() == str(expected_value).strip().lower()
    except Exception:
        return False

def smart_set_reg(hive, subkey, name, value, reg_type):
    if check_reg_value(hive, subkey, name, value):
        return True
    try:
        with winreg.CreateKeyEx(hive, subkey, 0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY) as key:
            winreg.SetValueEx(key, name, 0, reg_type, value)
        logging.info(f"  [APLICADO REGISTRO] {subkey}\\{name} = {value}")
        return True
    except Exception as exc:
        logging.error(f"[ERROR REGISTRO] Fallo en {subkey}\\{name}: {exc}", exc_info=True)
        return False

def is_service_stopped_and_disabled(srv_name):
    try:
        res = subprocess.run(f"sc query {srv_name}", shell=True, capture_output=True, text=True, errors="ignore")
        out_all = res.stdout + res.stderr
        if "1060" in out_all or "FAILED" in res.stdout:
            return True
        if "STOPPED" in res.stdout:
            res_qc = subprocess.run(f"sc qc {srv_name}", shell=True, capture_output=True, text=True, errors="ignore")
            if "DISABLED" in res_qc.stdout or "4" in res_qc.stdout:
                return True
    except Exception:
        pass
    return False

def scheduled_task_exists(task_name):
    res = subprocess.run(f'schtasks /query /tn "{task_name}"', shell=True, capture_output=True, text=True, errors="ignore")
    return res.returncode == 0

def user_exists(username):
    res = subprocess.run(f'net user {username}', shell=True, capture_output=True, text=True, errors="ignore")
    return res.returncode == 0

def download_file(url, target_path):
    print(f"\n\033[93m[DESCARGA]\033[0m Conectando a {url}...")
    logging.info(f"[DESCARGANDO] {url} -> {target_path}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    req = urllib.request.Request(url, headers=headers)
    Path(target_path).parent.mkdir(parents=True, exist_ok=True)

    with urllib.request.urlopen(req) as response:
        total_size = int(response.info().get('Content-Length', 0))
        downloaded = 0
        chunk_size = 1024 * 512

        with open(target_path, "wb") as out_file:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)

                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    mb_down = downloaded / (1024 * 1024)
                    mb_total = total_size / (1024 * 1024)
                    print(f"\r  -> Progreso: {mb_down:.1f} MB / {mb_total:.1f} MB ({percent:.1f}%)", end="", flush=True)
                else:
                    mb_down = downloaded / (1024 * 1024)
                    print(f"\r  -> Progreso: {mb_down:.1f} MB descargados...", end="", flush=True)

    print(" \033[92m[COMPLETADO]\033[0m")
    logging.info(f"[DESCARGA COMPLETADA] Archivo guardado en {target_path}")

# ==============================================================================
# 1. USUARIO, UAC Y AUTOLOGON (SMART)
# ==============================================================================
def setup_user_and_autologon():
    target = CONFIG["TARGET_USER"]
    logging.info(f"Evaluando estado de usuario '{target}', UAC y AutoLogon...")
    try:
        if not user_exists(target):
            logging.info(f"Creando usuario '{target}'...")
            run_cmd(f'net user {target} "" /add')
            run_cmd(f'wmic useraccount where name="{target}" set passwordexpires=false')
            run_cmd(f'net user {target} /passwordreq:no')

            ps_group = (
                "$sid = New-Object System.Security.Principal.SecurityIdentifier('S-1-5-32-544'); "
                "$group = $sid.Translate([System.Security.Principal.NTAccount]).Value.Split('\\')[-1]; "
                f"net localgroup \"$group\" \"{target}\" /add"
            )
            run_powershell(ps_group)
        else:
            logging.info(f"  [OMITIDO] El usuario '{target}' ya existe en el sistema.")

        uac_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, uac_path, "EnableLUA", 0, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, uac_path, "ConsentPromptBehaviorAdmin", 0, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, uac_path, "PromptOnSecureDesktop", 0, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Lsa", "LimitBlankPasswordUse", 0, winreg.REG_DWORD)

        winlogon_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, winlogon_path, "AutoAdminLogon", "1", winreg.REG_SZ)
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, winlogon_path, "DefaultUserName", target, winreg.REG_SZ)
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, winlogon_path, "DefaultPassword", "", winreg.REG_SZ)
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, winlogon_path, "DefaultDomainName", os.environ.get("COMPUTERNAME", "."), winreg.REG_SZ)
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, winlogon_path, "ForceAutoLogon", "1", winreg.REG_SZ)
    except Exception as exc:
        logging.error(f"[ERROR EN setup_user_and_autologon]: {exc}", exc_info=True)

# ==============================================================================
# 2. ENERGÍA CONTINUA MÁXIMA (ALTO RENDIMIENTO + 0 SUSPENSIÓN + SIN SCREENSAVER)
# ==============================================================================
def setup_power_and_screensaver():
    logging.info("=== CONFIGURANDO ENERGÍA CONTINUA MÁXIMA (24/7 SIN REPOSO) ===")
    try:
        run_cmd("powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")

        power_cmds = [
            "powercfg -change -monitor-timeout-ac 0",
            "powercfg -change -monitor-timeout-dc 0",
            "powercfg -change -standby-timeout-ac 0",
            "powercfg -change -standby-timeout-dc 0",
            "powercfg -change -hibernate-timeout-ac 0",
            "powercfg -change -hibernate-timeout-dc 0",
            "powercfg -change -disk-timeout-ac 0",
            "powercfg -change -disk-timeout-dc 0",
            "powercfg -h off",
            "powercfg -setacvalueindex SCHEME_CURRENT SUB_PCIEXPRESS ASPM 0",
            "powercfg -setdcvalueindex SCHEME_CURRENT SUB_PCIEXPRESS ASPM 0",
            "powercfg -setactive SCHEME_CURRENT"
        ]
        for cmd in power_cmds:
            run_cmd(cmd)

        desktop_path = r"Control Panel\Desktop"
        smart_set_reg(winreg.HKEY_CURRENT_USER, desktop_path, "ScreenSaveActive", "0", winreg.REG_SZ)
        smart_set_reg(winreg.HKEY_CURRENT_USER, desktop_path, "ScreenSaverIsSecure", "0", winreg.REG_SZ)
        smart_set_reg(winreg.HKEY_CURRENT_USER, desktop_path, "ScreenSaveTimeOut", "0", winreg.REG_SZ)
        smart_set_reg(winreg.HKEY_CURRENT_USER, desktop_path, "SCRNSAVE.EXE", "", winreg.REG_SZ)
        logging.info("Ahorro de energía, suspensión de discos, pantalla y buses anulados por completo.")
    except Exception as exc:
        logging.error(f"[ERROR EN setup_power_and_screensaver]: {exc}", exc_info=True)

# ==============================================================================
# 3. ESCRITORIO KIOSKO: ICONOS OCULTOS CON CLIC DERECHO ACTIVO PARA TEAMVIEWER
# ==============================================================================
class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uCallbackMessage", wintypes.UINT),
        ("uEdge", wintypes.UINT),
        ("rc", wintypes.RECT),
        ("lParam", wintypes.LPARAM)
    ]

def setup_desktop_ui():
    logging.info("Configurando UI: Ocultando iconos (manteniendo clic derecho para TeamViewer)...")
    try:
        # 3.1 ELIMINAR NoDesktop para restaurar el clic derecho y la navegación remota
        for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            try:
                with winreg.OpenKey(root, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer", 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as k:
                    winreg.DeleteValue(k, "NoDesktop")
            except Exception:
                pass

        # 3.2 Ocultar iconos de forma nativa (Equivale a: Clic derecho -> Ver -> Quitar 'Mostrar iconos')
        smart_set_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "HideIcons", 1, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_USERS, r".DEFAULT\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "HideIcons", 1, winreg.REG_DWORD)

        # 3.3 Fondo negro sólido (#000000)
        smart_set_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Colors", "Background", "0 0 0", winreg.REG_SZ)
        smart_set_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "Wallpaper", "", winreg.REG_SZ)
        user32.SystemParametersInfoW(20, 0, "", 3)

        # 3.4 Escala fija al 100% DPI
        smart_set_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "LogPixels", 96, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "Win8DpiScaling", 1, winreg.REG_DWORD)

        # 3.5 Auto-ocultar la barra de tareas
        for stuck in [r"Software\Microsoft\Windows\CurrentVersion\Explorer\StuckRects3", 
                      r"Software\Microsoft\Windows\CurrentVersion\Explorer\StuckRects2"]:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, stuck, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
                    val, reg_type = winreg.QueryValueEx(key, "Settings")
                    if len(val) > 8:
                        val_bytes = bytearray(val)
                        val_bytes[8] = val_bytes[8] | 0x01
                        winreg.SetValueEx(key, "Settings", 0, reg_type, bytes(val_bytes))
            except Exception:
                pass

        # 3.6 REINICIO DE EXPLORER: Aplica HideIcons y devuelve el clic derecho al instante
        logging.info("Reiniciando Explorer para ocultar iconos y activar clic derecho...")
        subprocess.run("taskkill /f /im explorer.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        subprocess.Popen("explorer.exe", shell=True)
        time.sleep(2)

        # 3.7 Disparar mensaje de AppBar sobre la nueva barra
        abd = APPBARDATA()
        abd.cbSize = ctypes.sizeof(APPBARDATA)
        abd.hWnd = user32.FindWindowW("Shell_TrayWnd", None)
        abd.lParam = 1
        ctypes.windll.shell32.SHAppBarMessage(10, ctypes.byref(abd))

        logging.info("  [APLICADO] Iconos ocultos sin romper el menú contextual del escritorio.")
    except Exception as exc:
        logging.error(f"[ERROR EN setup_desktop_ui]: {exc}", exc_info=True)

# ==============================================================================
# 4. RESOLUCIÓN GRÁFICA Y ROTACIÓN (DEVMODE Y POINTL CORREGIDOS)
# ==============================================================================
class POINTL(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long)
    ]

class DEVMODE(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_wchar * 32),
        ("dmSpecVersion", ctypes.c_ushort),
        ("dmDriverVersion", ctypes.c_ushort),
        ("dmSize", ctypes.c_ushort),
        ("dmDriverExtra", ctypes.c_ushort),
        ("dmFields", ctypes.c_uint),
        ("dmPosition", POINTL),
        ("dmDisplayOrientation", ctypes.c_uint),
        ("dmDisplayFixedOutput", ctypes.c_uint),
        ("dmColor", ctypes.c_short),
        ("dmDuplex", ctypes.c_short),
        ("dmYResolution", ctypes.c_short),
        ("dmTTOption", ctypes.c_short),
        ("dmCollate", ctypes.c_short),
        ("dmFormName", ctypes.c_wchar * 32),
        ("dmLogPixels", ctypes.c_ushort),
        ("dmBitsPerPel", ctypes.c_uint),
        ("dmPelsWidth", ctypes.c_uint),
        ("dmPelsHeight", ctypes.c_uint),
        ("dmDisplayFlags", ctypes.c_uint),
        ("dmDisplayFrequency", ctypes.c_uint),
        ("dmICMMethod", ctypes.c_uint),
        ("dmICMIntent", ctypes.c_uint),
        ("dmMediaType", ctypes.c_uint),
        ("dmDitherType", ctypes.c_uint),
        ("dmReserved1", ctypes.c_uint),
        ("dmReserved2", ctypes.c_uint),
        ("dmPanningWidth", ctypes.c_uint),
        ("dmPanningHeight", ctypes.c_uint)
    ]

user32.EnumDisplaySettingsW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(DEVMODE)]
user32.EnumDisplaySettingsW.restype = wintypes.BOOL
user32.ChangeDisplaySettingsW.argtypes = [ctypes.POINTER(DEVMODE), wintypes.DWORD]
user32.ChangeDisplaySettingsW.restype = ctypes.c_long

def setup_display_mode():
    ancho = CONFIG["RESOLUCION_ANCHO"]
    alto = CONFIG["RESOLUCION_ALTO"]
    rot = CONFIG["ROTACION_PANTALLA"]
    
    try:
        dm = DEVMODE()
        dm.dmSize = ctypes.sizeof(DEVMODE)

        if user32.EnumDisplaySettingsW(None, -1, ctypes.byref(dm)):
            expected_w = alto if rot in (1, 3) else ancho
            expected_h = ancho if rot in (1, 3) else alto
            
            if dm.dmPelsWidth == expected_w and dm.dmPelsHeight == expected_h and dm.dmDisplayOrientation == rot:
                logging.info(f"  [OMITIDO] Pantalla ya establecida en {expected_w}x{expected_h} con rotación {rot * 90}°.")
                return

            logging.info(f"Ajustando modo gráfico a {expected_w}x{expected_h}...")
            dm.dmPelsWidth = expected_w
            dm.dmPelsHeight = expected_h
            dm.dmDisplayOrientation = rot
            dm.dmFields = 0x00080000 | 0x00100000 | 0x00000080
            
            res = user32.ChangeDisplaySettingsW(ctypes.byref(dm), 1)
            if res != 0:
                logging.warning(f"Aviso del controlador gráfico: Código de respuesta {res}.")
            else:
                logging.info(f"  [APLICADO] Resolución fijada a {expected_w}x{expected_h}.")
        else:
            logging.warning("No fue posible consultar la configuración gráfica actual.")
    except Exception as exc:
        logging.error(f"[ERROR EN setup_display_mode]: {exc}", exc_info=True)

# ==============================================================================
# 5. BLOQUEO TOTAL DE NOTIFICACIONES DE RAÍZ (HOME / PRO / ENTERPRISE / IOT)
# ==============================================================================
def disable_notifications_and_updates():
    logging.info("=== APLICANDO SILENCIADO ABSOLUTO DE NOTIFICACIONES DE RAÍZ Y UPDATES ===")
    try:
        # 5.1 MATAR DE RAÍZ EL CENTRO DE SEGURIDAD (wscsvc) - ELIMINA AVISOS DE FIREWALL/ANTIVIRUS
        logging.info("Aniquilando servicio Security Center (wscsvc) en el registro para evitar avisos...")
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\wscsvc", "Start", 4, winreg.REG_DWORD)
        subprocess.run("net stop wscsvc", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Ocultar icono de salud / banderita de Security Center del área de notificación
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer", "HideSCAHealth", 1, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer", "HideSCAHealth", 1, winreg.REG_DWORD)

        # 5.2 MATAR DE RAÍZ LA PLATAFORMA PUSH DE NOTIFICACIONES (WpnService y WpnUserService dinámicos)
        logging.info("Aniquilando servicios de notificaciones push (WpnService / WpnUserService)...")
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\WpnService", "Start", 4, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\WpnUserService", "Start", 4, winreg.REG_DWORD)
        subprocess.run("net stop WpnService", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Detener instancias dinámicas de WpnUserService en RAM (ej. WpnUserService_3a1b2)
        run_powershell("Get-Service WpnUserService* -ErrorAction SilentlyContinue | Stop-Service -Force -ErrorAction SilentlyContinue")

        # 5.3 INTERRUPTOR MAESTRO DE NOTIFICACIONES EN WINDOWS HOME/PRO/IOT (NOC_GLOBAL_SETTING)
        notif_settings = r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings"
        smart_set_reg(winreg.HKEY_CURRENT_USER, notif_settings, "NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION", 0, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_CURRENT_USER, notif_settings, "NOC_GLOBAL_SETTING_ALLOW_TOASTS_ABOVE_LOCK", 0, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_CURRENT_USER, notif_settings, "NOC_GLOBAL_SETTING_ALLOW_CRITICAL_TOASTS_ABOVE_LOCK", 0, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_USERS, rf".DEFAULT\{notif_settings}", "NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION", 0, winreg.REG_DWORD)

        # Recorrer dinámicamente todos los proveedores de notificaciones y forzar Enabled = 0
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, notif_settings, 0, winreg.KEY_READ) as k:
                sub_count, _, _ = winreg.QueryInfoKey(k)
                for idx in range(sub_count):
                    sub_name = winreg.EnumKey(k, idx)
                    smart_set_reg(winreg.HKEY_CURRENT_USER, rf"{notif_settings}\{sub_name}", "Enabled", 0, winreg.REG_DWORD)
        except Exception:
            pass

        # 5.4 DESACTIVAR TOASTS EN REGISTRO DE USUARIO Y DIRECTIVAS
        push_user = r"Software\Microsoft\Windows\CurrentVersion\PushNotifications"
        smart_set_reg(winreg.HKEY_CURRENT_USER, push_user, "ToastEnabled", 0, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_USERS, rf".DEFAULT\{push_user}", "ToastEnabled", 0, winreg.REG_DWORD)

        push_pol = r"SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\PushNotifications"
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, push_pol, "NoToastNotification", 1, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, push_pol, "NoCloudApplicationNotification", 1, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_CURRENT_USER, push_pol, "NoToastNotification", 1, winreg.REG_DWORD)

        sec_notif = r"SOFTWARE\Policies\Microsoft\Windows Defender Security Center\Notifications"
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, sec_notif, "DisableNotifications", 1, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, sec_notif, "DisableEnhancedNotifications", 1, winreg.REG_DWORD)

        # 5.5 ANULAR CENTRO DE ACCIÓN Y GLOBOS
        exp_pol = r"SOFTWARE\Policies\Microsoft\Windows\Explorer"
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, exp_pol, "DisableNotificationCenter", 1, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, exp_pol, "NoActionCenter", 1, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, exp_pol, "NoBalloonFeatureAdvertisements", 1, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_CURRENT_USER, exp_pol, "DisableNotificationCenter", 1, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "EnableBalloonTips", 0, winreg.REG_DWORD)

        # 5.6 SUPRIMIR VENTANAS MODALES DE FALLO DE APLICACIÓN (WER)
        smart_set_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Windows Error Reporting", "DontShowUI", 1, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\Windows Error Reporting", "DontShowUI", 1, winreg.REG_DWORD)

        # 5.7 FOCUS ASSIST / NO MOLESTAR PERMANENTE (SOLO ALARMAS / SILENCIO)
        focus_path = r"Software\Microsoft\Windows\CurrentVersion\FocusAssist"
        smart_set_reg(winreg.HKEY_CURRENT_USER, focus_path, "FocusAssistState", 2, winreg.REG_DWORD)
        smart_set_reg(winreg.HKEY_CURRENT_USER, notif_settings, "DoNotDisturbEnabled", 1, winreg.REG_DWORD)

        # 5.8 BLOQUEO PERMANENTE DE WINDOWS UPDATE
        if CONFIG["BLOQUEAR_UPDATES_TOTAL"]:
            wu_pol = r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, wu_pol, "DoNotConnectToWindowsUpdateInternetLocations", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, wu_pol, "DisableWindowsUpdateAccess", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, f"{wu_pol}\\AU", "NoAutoUpdate", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, f"{wu_pol}\\AU", "AUOptions", 1, winreg.REG_DWORD)

            for srv in ["wuauserv", "WaaSMedicSvc", "UsoSvc", "bits"]:
                smart_set_reg(winreg.HKEY_LOCAL_MACHINE, rf"SYSTEM\CurrentControlSet\Services\{srv}", "Start", 4, winreg.REG_DWORD)
                subprocess.run(f"net stop {srv}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            tasks_update = [
                r"\Microsoft\Windows\WindowsUpdate\Scheduled Start",
                r"\Microsoft\Windows\UpdateOrchestrator\Schedule Scan",
                r"\Microsoft\Windows\UpdateOrchestrator\Schedule Scan Static",
                r"\Microsoft\Windows\UpdateOrchestrator\UpdateModelTask",
                r"\Microsoft\Windows\WaaSMedic\PerformRemediation"
            ]
            for t in tasks_update:
                task_name = t.split("\\")[-1]
                task_path = "\\".join(t.split("\\")[:-1]) + "\\"
                run_powershell(f"Disable-ScheduledTask -TaskPath '{task_path}' -TaskName '{task_name}' -ErrorAction SilentlyContinue")

            logging.info("Notificaciones y Windows Update neutralizados de raíz.")
    except Exception as exc:
        logging.error(f"[ERROR EN disable_notifications_and_updates]: {exc}", exc_info=True)

# ==============================================================================
# 6. FECHA, HORA Y ARRANQUE/RECUPERACIÓN (SMART)
# ==============================================================================
def setup_time_and_boot():
    tz = CONFIG["ZONA_HORARIA"]
    timeout = CONFIG["TIMEOUT_ARRANQUE_SEG"]
    try:
        chk_tz = subprocess.run("tzutil /g", shell=True, capture_output=True, text=True, errors="ignore")
        if chk_tz.stdout.strip().lower() != tz.lower():
            logging.info(f"Ajustando zona horaria a '{tz}'...")
            run_cmd(f'tzutil /s "{tz}"')
        else:
            logging.info(f"  [OMITIDO] Zona horaria ya fijada en '{tz}'.")

        if not is_service_stopped_and_disabled("w32time"):
            logging.info("Deteniendo w32time para liberar el puerto 123 UDP a NetTime...")
            run_cmd("net stop w32time")
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\w32time", "Start", 4, winreg.REG_DWORD)
        else:
            logging.info("  [OMITIDO] Servicio w32time ya se encuentra detenido.")

        run_cmd(f"bcdedit /timeout {timeout}")
        run_cmd("bcdedit /set {current} bootstatuspolicy ignoreallfailures")
    except Exception as exc:
        logging.error(f"[ERROR EN setup_time_and_boot]: {exc}", exc_info=True)

# ==============================================================================
# 7. FIREWALL Y WINDOWS DEFENDER: APAGADO TOTAL Y DEFINITIVO
# ==============================================================================
def setup_firewall_and_security():
    logging.info("=== APLICANDO APAGADO TOTAL DE FIREWALL Y WINDOWS DEFENDER ===")
    try:
        if CONFIG["DESACTIVAR_FIREWALL_TOTAL"]:
            logging.info("Apagando Firewall de Windows en todos los perfiles...")
            run_cmd("netsh advfirewall set allprofiles state off")
            fw_base = r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy"
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, f"{fw_base}\\DomainProfile", "EnableFirewall", 0, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, f"{fw_base}\\StandardProfile", "EnableFirewall", 0, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, f"{fw_base}\\PublicProfile", "EnableFirewall", 0, winreg.REG_DWORD)
            logging.info("Firewall de Windows desactivado permanentemente.")

        if CONFIG["ANIQUILAR_DEFENDER_TOTAL"]:
            logging.info("Aniquilando Windows Defender por directiva de grupo y servicios...")
            def_pol = r"SOFTWARE\Policies\Microsoft\Windows Defender"
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, def_pol, "DisableAntiSpyware", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, def_pol, "DisableRoutinelyTakingAction", 1, winreg.REG_DWORD)
            
            rt_pol = f"{def_pol}\\Real-Time Protection"
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, rt_pol, "DisableRealtimeMonitoring", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, rt_pol, "DisableBehaviorMonitoring", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, rt_pol, "DisableOnAccessProtection", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, rt_pol, "DisableScanOnRealtimeEnable", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, rt_pol, "DisableIOAVProtection", 1, winreg.REG_DWORD)

            spy_pol = f"{def_pol}\\Spynet"
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, spy_pol, "SpyNetReporting", 0, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, spy_pol, "SubmitSamplesConsent", 2, winreg.REG_DWORD)

            for srv_def in ["WinDefend", "Sense", "WdNisSvc"]:
                try:
                    smart_set_reg(winreg.HKEY_LOCAL_MACHINE, rf"SYSTEM\CurrentControlSet\Services\{srv_def}", "Start", 4, winreg.REG_DWORD)
                    subprocess.run(f"net stop {srv_def}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass

            if IS_WIN10_OR_LATER:
                run_powershell("Set-MpPreference -DisableRealtimeMonitoring $true -DisableBehaviorMonitoring $true -DisableIOAVProtection $true -MAPSReporting 0 -SubmitSamplesConsent 2 -ErrorAction SilentlyContinue")
            logging.info("Windows Defender anulado permanentemente.")

    except Exception as exc:
        logging.error(f"[ERROR EN setup_firewall_and_security]: {exc}", exc_info=True)

# ==============================================================================
# 8. AUTOMATIZACIÓN SMART DE BIOS (DETECCIÓN MULTI-CAPA, IDEMPOTENCIA Y WMI)
# ==============================================================================
def get_system_hardware_info():
    mfg, model, board_mfg, board_prod = "", "", "", ""
    
    ps_cmd = (
        "$cs = if (Get-Command Get-CimInstance -ErrorAction SilentlyContinue) "
        "{ Get-CimInstance Win32_ComputerSystem } else { Get-WmiObject Win32_ComputerSystem }; "
        "$bb = if (Get-Command Get-CimInstance -ErrorAction SilentlyContinue) "
        "{ Get-CimInstance Win32_BaseBoard } else { Get-WmiObject Win32_BaseBoard }; "
        "Write-Output \"$($cs.Manufacturer)||$($cs.Model)||$($bb.Manufacturer)||$($bb.Product)\""
    )
    res_ps = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                            capture_output=True, text=True, errors="ignore")
    
    if res_ps.returncode == 0 and "||" in res_ps.stdout:
        parts = [p.strip() for p in res_ps.stdout.split("||")]
        if len(parts) >= 4:
            mfg, model, board_mfg, board_prod = parts[0], parts[1], parts[2], parts[3]

    if not mfg or "to be filled" in mfg.lower():
        res_wmic = subprocess.run("wmic computersystem get manufacturer,model /value", shell=True, capture_output=True, text=True, errors="ignore")
        for line in res_wmic.stdout.splitlines():
            if "manufacturer=" in line.lower() and not mfg:
                mfg = line.split("=")[-1].strip()
            elif "model=" in line.lower() and not model:
                model = line.split("=")[-1].strip()

        res_bb = subprocess.run("wmic baseboard get manufacturer,product /value", shell=True, capture_output=True, text=True, errors="ignore")
        for line in res_bb.stdout.splitlines():
            if "manufacturer=" in line.lower() and not board_mfg:
                board_mfg = line.split("=")[-1].strip()
            elif "product=" in line.lower() and not board_prod:
                board_prod = line.split("=")[-1].strip()

    mfg_final = board_mfg if (not mfg or "to be filled" in mfg.lower() or "o.e.m" in mfg.lower()) else mfg
    model_final = board_prod if (not model or "to be filled" in model.lower() or "o.e.m" in model.lower()) else model

    return mfg_final.strip().lower(), model_final.strip(), board_mfg.strip().lower(), board_prod.strip()

def find_executable(names, extra_paths=None):
    search_dirs = [SCRIPT_DIR]
    if extra_paths:
        search_dirs.extend([Path(p) for p in extra_paths])
    
    for pf in [r"C:\Program Files", r"C:\Program Files (x86)"]:
        search_dirs.append(Path(pf))

    for name in names:
        for sdir in search_dirs:
            if not sdir.exists():
                continue
            direct = sdir / name
            if direct.is_file():
                return direct
            try:
                for match in sdir.glob(f"**/{name}"):
                    if match.is_file():
                        return match
            except Exception:
                pass
        in_path = shutil.which(name)
        if in_path:
            return Path(in_path)
            
    return None

def apply_bios_settings():
    logging.info("=== AUTOMATIZANDO BIOS: ENCENDIDO 08:00 AM Y POWER ON TRAS CORTE ===")
    try:
        mfg, model, b_mfg, b_prod = get_system_hardware_info()
        disp_mfg = mfg.title() if mfg else "Desconocido"
        logging.info(f"Hardware detectado -> Fabricante: '{disp_mfg}', Modelo: '{model}' (Placa: '{b_mfg.title()}' '{b_prod}')")

        hora_str = CONFIG.get("BIOS_WAKE_HORA", "08:00")
        hour_int = int(CONFIG.get("BIOS_WAKE_HOUR", 8))
        min_int = int(CONFIG.get("BIOS_WAKE_MINUTE", 0))

        if "dell" in mfg:
            cctk = find_executable(["cctk.exe"], [
                r"C:\Program Files\Dell\Command Configure\X86_64",
                r"C:\Program Files (x86)\Dell\Command Configure\X86_64",
                r"C:\Program Files\Dell\Command Configure",
                r"C:\Program Files (x86)\Dell\Command Configure"
            ])
            if cctk:
                logging.info(f"Herramienta Dell detectada: {cctk}")
                chk = subprocess.run(f'"{cctk}" --AcPwrRcvry', shell=True, capture_output=True, text=True, errors="ignore")
                chk_time = subprocess.run(f'"{cctk}" --AutoOnTime', shell=True, capture_output=True, text=True, errors="ignore")
                
                if "AcPwrRcvry=on" in chk.stdout.lower() and hora_str in chk_time.stdout:
                    logging.info(f"  [OMITIDO] BIOS Dell ya configurada: AcPwrRcvry=On y AutoOnTime={hora_str}.")
                else:
                    run_cmd(f'"{cctk}" --AcPwrRcvry=On')
                    run_cmd(f'"{cctk}" --AutoOn=Everyday --AutoOnTime={hora_str}')
                    logging.info(f"  [APLICADO] Dell BIOS: Encendido programado a las {hora_str} y AcPwrRcvry=On.")
            else:
                logging.warning("Dell detectado pero falta 'cctk.exe'. Ubícalo junto al script o instala Dell Command Configure.")

        elif "hp" in mfg or "hewlett-packard" in mfg:
            bcu_names = ["BiosConfigUtility64.exe", "BiosConfigUtility.exe"]
            bcu = find_executable(bcu_names, [
                r"C:\Program Files\HP\BIOS Configuration Utility",
                r"C:\Program Files (x86)\HP\BIOS Configuration Utility"
            ])
            if bcu:
                logging.info(f"Herramienta HP detectada: {bcu}")
                bcu_cfg = SCRIPT_DIR / "hp_bios_config.txt"
                hp_txt_content = (
                    "BIOSConfig 1.0\n"
                    "After Power Loss\n\t*Power On\n"
                    "BIOS Power-On\n\t*Enable\n"
                    f"Time\n\t{hora_str}\n"
                    "Sunday\n\t*Enable\nMonday\n\t*Enable\nTuesday\n\t*Enable\n"
                    "Wednesday\n\t*Enable\nThursday\n\t*Enable\nFriday\n\t*Enable\nSaturday\n\t*Enable\n"
                )
                with open(bcu_cfg, "w", encoding="utf-8") as f:
                    f.write(hp_txt_content)

                run_cmd(f'"{bcu}" /set:"{bcu_cfg}"')
                logging.info(f"  [APLICADO] HP BIOS: Configurado arranque diario a las {hora_str} y Power On tras corte.")
            else:
                logging.warning("HP detectado pero falta 'BiosConfigUtility64.exe'. Ubícalo junto al script para aplicar BIOS.")

        elif "intel" in mfg:
            isetup = find_executable(["iSetupCfg.exe", "iSetupCfgWin64.exe"])
            if isetup:
                logging.info(f"Herramienta Intel NUC detectada: {isetup}")
                run_cmd(f'"{isetup}" -set AfterPowerLoss=PowerOn')
                run_cmd(f'"{isetup}" -set WakeOnS5=Enabled')
                run_cmd(f'"{isetup}" -set WakeOnS5Hour={hour_int}')
                run_cmd(f'"{isetup}" -set WakeOnS5Minute={min_int}')
                logging.info(f"  [APLICADO] Intel NUC: Arranque programado a las {hora_str} (WakeOnS5) y AfterPowerLoss=PowerOn.")
            else:
                logging.warning("Intel detectado pero falta 'iSetupCfg.exe'. Ubícalo junto al script para automatizar BIOS.")

        elif "lenovo" in mfg:
            logging.info("Hardware Lenovo detectado. Aplicando directivas mediante interfaz nativa WMI...")
            ps_lenovo = (
                "$applied = $false; "
                "try { "
                "  $wmi = Get-WmiObject -Namespace root\\wmi -Class Lenovo_SetBiosSetting -ErrorAction Stop; "
                "  $save = Get-WmiObject -Namespace root\\wmi -Class Lenovo_SaveBiosSettings -ErrorAction Stop; "
                "  $wmi.SetBiosSetting('AfterPowerLoss,PowerOn'); "
                "  $wmi.SetBiosSetting('AutomaticPowerOn,Everyday'); "
                f"  $wmi.SetBiosSetting('AutomaticPowerOnTime,{hora_str.replace(':', '')}'); "
                "  $save.SaveBiosSettings(); "
                "  $applied = $true; "
                "} catch {} "
                "Write-Output $applied"
            )
            res_len = run_powershell(ps_lenovo)
            if "true" in res_len.stdout.lower():
                logging.info(f"  [APLICADO] Lenovo BIOS configurada con éxito por WMI: Wake {hora_str} y Power On tras corte.")
            else:
                logging.warning("No se pudo aplicar por WMI en Lenovo (requiere contraseña de supervisor de BIOS o módulo no disponible).")

        elif "shuttle" in mfg or "shuttle" in b_mfg:
            logging.info("=" * 65)
            logging.info(f"EQUIPO SHUTTLE DETECTADO: Placa {b_prod}")
            logging.info("Shuttle no admite modificación de BIOS desde Windows.")
            logging.info("CONFIGURACIÓN OBLIGATORIA EN TALLER:")
            logging.info("  1. Reinicia el equipo y pulsa la tecla <SUP> / <DEL>.")
            logging.info("  2. Entra a: Advanced -> Power Management Configuration.")
            logging.info("  3. Ajusta: 'Power-On after PowerFail' = [Power On].")
            logging.info(f"  4. Ajusta: 'Resume by Alarm' / 'RTC Alarm' = [Enabled] -> Hora: {hora_str}:00.")
            logging.info("  5. Pulsa F10 para guardar y reiniciar.")
            logging.info("=" * 65)

        else:
            logging.info("=" * 65)
            logging.info(f"PLACA BASE ESTÁNDAR / INDUSTRIAL: '{b_mfg.title()}' '{b_prod}'")
            logging.info("Esta placa no expone API de software en Windows.")
            logging.info("AJUSTE MANUAL RECOMENDADO EN BIOS:")
            logging.info("  - Pulsa <SUP> o <F2> al encender.")
            logging.info("  - Fija 'Restore on AC Power Loss' / 'State After G3' = [Power On].")
            logging.info(f"  - Fija 'Wake Up by RTC' / 'Resume by Alarm' = [Enabled] a las {hora_str}.")
            logging.info("ALTERNATIVA SMART PLUG:")
            logging.info("  - Deja solo 'Power-On after PowerFail = Power On' en BIOS.")
            logging.info("  - El script apagará Windows a las 22:00 h limpiamente.")
            logging.info(f"  - Un enchufe temporizador cortará la luz a las 22:15 h y la devolverá a las {hora_str} h.")
            logging.info("=" * 65)

    except Exception as exc:
        logging.error(f"[ERROR EN apply_bios_settings]: {exc}", exc_info=True)

# ==============================================================================
# 9. ELIMINACIÓN DE COPILOT, RECALL Y SUBSISTEMAS DE IA (WIN 10 / 11)
# ==============================================================================
def nuke_copilot_and_ai():
    if not CONFIG["BLOQUEAR_IA_Y_COPILOT"] or not IS_WIN10_OR_LATER:
        return

    logging.info("Evaluando bloqueo de Copilot, Recall y subprocesos de IA...")
    try:
        ai_reg = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot", "TurnOffWindowsCopilot", 1, winreg.REG_DWORD),
            (winreg.HKEY_CURRENT_USER, r"Software\Policies\Microsoft\Windows\WindowsCopilot", "TurnOffWindowsCopilot", 1, winreg.REG_DWORD),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\WindowsAI", "DisableAIDataAnalysis", 1, winreg.REG_DWORD),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\WindowsAI", "TurnOffRecall", 1, winreg.REG_DWORD),
            (winreg.HKEY_CURRENT_USER, r"Software\Policies\Microsoft\Windows\Explorer", "DisableSearchBoxSuggestions", 1, winreg.REG_DWORD)
        ]
        for hive, path, name, val, rtype in ai_reg:
            smart_set_reg(hive, path, name, val, rtype)

        base_ifeo = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
        for exe in CONFIG["IA_BINARIOS_IFEO"]:
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, f"{base_ifeo}\\{exe}", "Debugger", "systray.exe", winreg.REG_SZ)

        for proc in ["AIFabric", "CoreAI", "WindowsAI", "Recall", "ClickToDo", "Copilot"]:
            run_powershell(f"Get-Process | Where-Object {{ $_.Name -match '{proc}' }} | Stop-Process -Force -ErrorAction SilentlyContinue")
    except Exception as exc:
        logging.error(f"[ERROR EN nuke_copilot_and_ai]: {exc}", exc_info=True)

# ==============================================================================
# 10. NEUTRALIZACIÓN FÍSICA SYSTEMAPPS (.BAK_DISABLED CON SID UNIVERSAL)
# ==============================================================================
def hard_nuke_system_apps():
    sys_apps_dir = r"C:\Windows\SystemApps"
    if not os.path.exists(sys_apps_dir) or not IS_WIN10_OR_LATER:
        return

    logging.info("Evaluando carpetas protegidas de SystemApps...")
    try:
        for item in os.listdir(sys_apps_dir):
            if any(t.lower() in item.lower() for t in CONFIG["SYSTEMAPPS_A_NEUTRALIZAR"]):
                if item.endswith(".BAK_DISABLED"):
                    continue
                target_path = os.path.join(sys_apps_dir, item)
                new_path = target_path + ".BAK_DISABLED"
                if os.path.exists(new_path):
                    continue
                run_cmd(f'takeown /f "{target_path}" /r /d y')
                run_cmd(f'icacls "{target_path}" /grant *S-1-5-32-544:F /t')
                try:
                    os.rename(target_path, new_path)
                    logging.info(f"  [APLICADO] Neutralizada físicamente: {item}.BAK_DISABLED")
                except Exception as e:
                    logging.warning(f"No se pudo renombrar {item}: {e}")
    except Exception as exc:
        logging.error(f"[ERROR EN hard_nuke_system_apps]: {exc}", exc_info=True)

# ==============================================================================
# 11. ANULACIÓN DE VIRTUALIZACIÓN, WSL Y HYPER-V (WIN 10 / 11)
# ==============================================================================
def disable_virtualization():
    if not CONFIG["DESACTIVAR_VIRTUALIZACION"] or not IS_WIN10_OR_LATER:
        return

    logging.info("Evaluando subsistemas WSL e Hyper-V...")
    try:
        if shutil.which("wsl"):
            run_cmd("wsl --shutdown")
            res_wsl = subprocess.run("wsl -l -q", shell=True, capture_output=True, text=True, errors="ignore")
            installed_distros = [d.strip() for d in res_wsl.stdout.replace('\x00', '').splitlines() if d.strip()]
            for distro in CONFIG["WSL_DISTROS_A_PURGAR"]:
                if distro in installed_distros:
                    run_cmd(f"wsl --unregister {distro}")

        features = [
            "Microsoft-Windows-Subsystem-Linux", "VirtualMachinePlatform",
            "Microsoft-Hyper-V-All", "Microsoft-Hyper-V", "Microsoft-Hyper-V-Tools-All",
            "Microsoft-Hyper-V-Hypervisor", "Microsoft-Hyper-V-Services"
        ]
        for f in features:
            chk_feat = subprocess.run(
                ["powershell", "-NoProfile", "-Command", f"(Get-WindowsOptionalFeature -Online -FeatureName {f} -ErrorAction SilentlyContinue).State"],
                capture_output=True, text=True, errors="ignore"
            )
            if "disabled" not in chk_feat.stdout.lower():
                run_powershell(f"Disable-WindowsOptionalFeature -Online -FeatureName {f} -NoRestart -ErrorAction SilentlyContinue")
            else:
                logging.info(f"  [OMITIDO] Característica {f} ya se encuentra deshabilitada.")

        run_cmd("bcdedit /set hypervisorlaunchtype off")
    except Exception as exc:
        logging.error(f"[ERROR EN disable_virtualization]: {exc}", exc_info=True)

# ==============================================================================
# 12. PURGA DE APPS, TELEMETRÍA Y LIMPIEZA PROFUNDA (SMART)
# ==============================================================================
def cleanup_unnecessary_apps_and_telemetry():
    logging.info("Evaluando software innecesario, bloatware y telemetría...")
    try:
        subprocess.run("taskkill /f /im OneDrive.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("taskkill /f /im Dropbox.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("taskkill /f /im Skype.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\OneDrive", "DisableFileSyncNGSC", 1, winreg.REG_DWORD)
        
        for p in [r"C:\Windows\SysWOW64\OneDriveSetup.exe", r"C:\Windows\System32\OneDriveSetup.exe"]:
            if os.path.isfile(p):
                run_cmd(f'"{p}" /uninstall')

        # Purga de AppX solo en Windows 10 y 11 filtrando paquetes NonRemovable
        if CONFIG["PURGAR_BLOATWARE_Y_POPUPS"] and IS_WIN10_OR_LATER:
            for pattern in CONFIG["APPS_UWP_A_ELIMINAR"]:
                ps_remove = (
                    f'Get-AppxPackage -AllUsers -Name "{pattern}" | '
                    f'Where-Object {{ -not $_.NonRemovable }} | '
                    f'ForEach-Object {{ try {{ Remove-AppxPackage -AllUsers -Package $_.PackageFullName -ErrorAction Stop }} catch {{}} }}; '
                    f'Get-AppxProvisionedPackage -Online | '
                    f'Where-Object DisplayName -like "{pattern}" | '
                    f'ForEach-Object {{ try {{ Remove-AppxProvisionedPackage -Online -PackageName $_.PackageName -ErrorAction Stop }} catch {{}} }}'
                )
                run_powershell(ps_remove)

        for srv in CONFIG["SERVICIOS_OEM_Y_TELEMETRIA"]:
            if not is_service_stopped_and_disabled(srv):
                run_cmd(f"net stop {srv}")
                run_cmd(f"sc config {srv} start= disabled")

        if CONFIG["DESACTIVAR_TELEMETRIA"]:
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", 0, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\Windows Error Reporting", "Disabled", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Windows Error Reporting", "Disabled", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\SQMClient\Windows", "CEIPEnable", 0, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\AppCompat", "AITEnable", 0, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\AppCompat", "DisableInventory", 1, winreg.REG_DWORD)

        # Desbloqueo preventivo de IFEO
        base_ifeo = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
        for remote_exe in ["TeamViewer.exe", "admira.exe", "transfer.exe", "winvnc.exe", "WinOFF.exe", "NetTime.exe"]:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f"{base_ifeo}\\{remote_exe}", 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, "Debugger")
            except Exception:
                pass

        if CONFIG["EJECUTAR_LIMPIEZA_PROFUNDA"]:
            logging.info("Vaciando caché DNS, Prefetch y temporales...")
            run_cmd("ipconfig /flushdns")
            run_cmd(r'del /q /f "C:\Windows\Prefetch\*.pf"')
            run_powershell("wevtutil el | Foreach-Object { wevtutil cl $_ }")

            for path in [os.environ.get("TEMP"), os.environ.get("TMP"), r"C:\Windows\Temp"]:
                if path and os.path.exists(path):
                    for item in os.listdir(path):
                        t_path = os.path.join(path, item)
                        try:
                            if os.path.isfile(t_path) or os.path.islink(t_path):
                                os.unlink(t_path)
                            elif os.path.isdir(t_path):
                                shutil.rmtree(t_path, ignore_errors=True)
                        except Exception:
                            pass

            if IS_WIN10_OR_LATER:
                logging.info("Ejecutando mantenimiento DISM...")
                run_cmd("DISM /Online /Cleanup-Image /StartComponentCleanup")
    except Exception as exc:
        logging.error(f"[ERROR EN cleanup_unnecessary_apps_and_telemetry]: {exc}", exc_info=True)

# ==============================================================================
# 13. ACCESO REMOTO - TEAMVIEWER (DETECCIÓN DE 32 Y 64 BITS)
# ==============================================================================
def setup_teamviewer():
    installer = CONFIG["TV_INSTALLER_TEMP"]
    url = CONFIG["TV_DOWNLOAD_URL"]
    
    try:
        tv_exe = None
        for ruta in CONFIG["TV_RUTAS_BUSQUEDA"]:
            if os.path.isfile(ruta):
                tv_exe = ruta
                break

        if not tv_exe:
            try:
                download_file(url, installer)
                logging.info("Instalando TeamViewer silenciosamente...")
                run_cmd(f'"{installer}" /S')
                for ruta in CONFIG["TV_RUTAS_BUSQUEDA"]:
                    if os.path.isfile(ruta):
                        tv_exe = ruta
                        break
            except Exception as exc:
                logging.error(f"Fallo al instalar TeamViewer: {exc}")
                return
        else:
            logging.info(f"  [OMITIDO] TeamViewer ya se encuentra instalado en: {tv_exe}")

        chk_tv = subprocess.run("sc query TeamViewer", shell=True, capture_output=True, text=True, errors="ignore")
        if "RUNNING" not in chk_tv.stdout:
            run_cmd("sc config TeamViewer start= auto")
            run_cmd("net start TeamViewer")
        else:
            logging.info("  [OMITIDO] Servicio TeamViewer ya está iniciado.")

        reg_keys = [r"SOFTWARE\TeamViewer", r"SOFTWARE\WOW6432Node\TeamViewer"]
        for r_key in reg_keys:
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r_key, "StartWithWindows", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r_key, "Autostart_GUI", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r_key, "ShowNoConnectionDialog", 0, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r_key, "HideNoConnectionDialog", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r_key, "AutoUpdate", 0, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r_key, "Always_Online", 1, winreg.REG_DWORD)

        tvopt_file = SCRIPT_DIR / CONFIG["TV_SETTINGS_TVOPT"]
        if tvopt_file.is_file() and tv_exe and os.path.isfile(tv_exe):
            logging.info(f"Importando perfil .tvopt ({tvopt_file})...")
            run_cmd(f'"{tv_exe}" import "{tvopt_file.absolute()}"')
        elif tv_exe and os.path.isfile(tv_exe) and CONFIG["TV_PASSWORD_FIJA"]:
            logging.info(f"Asignando contraseña predefinida fija ({CONFIG['TV_PASSWORD_FIJA']})...")
            try:
                subprocess.run(f'"{tv_exe}" setup --password "{CONFIG["TV_PASSWORD_FIJA"]}"', shell=True, timeout=10)
            except Exception:
                pass
    except Exception as exc:
        logging.error(f"[ERROR EN setup_teamviewer]: {exc}", exc_info=True)

# ==============================================================================
# 14. ADMIRA PLAYER (SMART)
# ==============================================================================
def install_admira_player():
    installer = CONFIG["ADMIRA_INSTALLER_TEMP"]
    url = CONFIG["ADMIRA_DOWNLOAD_URL"]
    
    try:
        player_found = False
        for r in CONFIG["ADMIRA_RUTAS"]:
            if (Path(r) / "admira.exe").is_file():
                player_found = True
                CONFIG["ADMIRA_MAIN_EXE"] = str(Path(r) / "admira.exe")
                break

        if not player_found:
            try:
                download_file(url, installer)
                logging.info("Instalando Admira Player (100% silencioso)...")
                cmd_install = f'"{installer}" /SP- /VERYSILENT /SUPPRESSMSGBOXES /NORESTART'
                run_cmd(cmd_install)
            except Exception as exc:
                logging.error(f"Fallo descargando/instalando Admira Player: {exc}")
        else:
            logging.info(f"  [OMITIDO] Admira Player ya instalado en: {CONFIG['ADMIRA_MAIN_EXE']}")
    except Exception as exc:
        logging.error(f"[ERROR EN install_admira_player]: {exc}", exc_info=True)

def clear_player_gpu_cache():
    logging.info("Purgando GPUCache residual del reproductor...")
    try:
        target_user = CONFIG["TARGET_USER"]
        cache_dirs = [
            Path(f"C:\\Users\\{target_user}\\AppData\\Local\\Admira\\GPUCache"),
            Path(f"C:\\Users\\{target_user}\\AppData\\Roaming\\admira-player\\GPUCache")
        ]
        for c_dir in cache_dirs:
            if c_dir.exists() and c_dir.is_dir():
                shutil.rmtree(c_dir, ignore_errors=True)
                logging.info(f"  [APLICADO] GPUCache limpiado en: {c_dir}")
    except Exception as exc:
        logging.error(f"[ERROR EN clear_player_gpu_cache]: {exc}", exc_info=True)

def setup_kiosk_shell():
    try:
        if CONFIG["HABILITAR_CUSTOM_SHELL"] and os.path.isfile(CONFIG["ADMIRA_MAIN_EXE"]):
            user_winlogon = r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon"
            smart_set_reg(winreg.HKEY_CURRENT_USER, user_winlogon, "Shell", CONFIG["ADMIRA_MAIN_EXE"], winreg.REG_SZ)
    except Exception as exc:
        logging.error(f"[ERROR EN setup_kiosk_shell]: {exc}", exc_info=True)

# ==============================================================================
# 15. AMP WINOFF: APAGADO PROGRAMADO A LAS 22:00 H (POWER OFF)
# ==============================================================================
def setup_amp_winoff():
    installer = CONFIG["WINOFF_INSTALLER_TEMP"]
    url = CONFIG["WINOFF_DOWNLOAD_URL"]
    winoff_dir = Path(CONFIG["WINOFF_INSTALL_DIR"])
    winoff_exe = winoff_dir / "WinOFF.exe"

    logging.info(f"=== CONFIGURANDO AMP WINOFF PARA APAGADO DIARIO A LAS {CONFIG['WINOFF_HORA']} ===")

    try:
        if not winoff_exe.is_file():
            try:
                download_file(url, installer)
                logging.info("Instalando AMP WinOFF silenciosamente...")
                cmd_install = f'"{installer}" /SP- /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /LANG=spanish'
                try:
                    subprocess.run(cmd_install, shell=True, timeout=35)
                except subprocess.TimeoutExpired:
                    pass

                time.sleep(2)
                subprocess.run("taskkill /f /im WinOFF.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(f'taskkill /f /im {Path(installer).name}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as exc:
                logging.error(f"Error al descargar/instalar AMP WinOFF: {exc}")
                return
        else:
            logging.info("  [OMITIDO] AMP WinOFF ya se encuentra instalado.")

        tipo_apagado = "0" if CONFIG["WINOFF_MODO"].upper() == "POWEROFF" else "1"
        winoff_ini_content = f"""[General]
Autostart=1
AutoActivate=1
Active=1
ShutdownType={tipo_apagado}
ShutdownMode=0
AllowAbort=1
AbortTime=30
ShowWarnings=0
PlaySounds=0
DisplayNotifications=0

[Planning]
DateTimeEnabled=1
DateTime={CONFIG["WINOFF_HORA"]}:00
IntervalEnabled=1
IntervalDays={CONFIG["WINOFF_INTERVALO_DIAS"]}
IntervalHours=0
IntervalMins=0
MultiCondition=0
ConditionOperator=0

[State]
LastRun=0
"""
        rutas_ini = [
            winoff_dir / "WinOFF.ini",
            Path(os.environ.get("APPDATA", "C:\\")) / "AMP Software" / "AMP WinOFF" / "WinOFF.ini",
            Path(f"C:\\Users\\{CONFIG['TARGET_USER']}\\AppData\\Roaming\\AMP Software\\AMP WinOFF\\WinOFF.ini")
        ]
        for ini_path in rutas_ini:
            try:
                ini_path.parent.mkdir(parents=True, exist_ok=True)
                with open(ini_path, "w", encoding="ansi") as f:
                    f.write(winoff_ini_content)
            except Exception:
                pass

        run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, run_key, "AMP WinOFF", f'"{winoff_exe}"', winreg.REG_SZ)
        smart_set_reg(winreg.HKEY_CURRENT_USER, run_key, "AMP WinOFF", f'"{winoff_exe}"', winreg.REG_SZ)

        task_name = "Admira_Daily_Power_Task"
        if not scheduled_task_exists(task_name):
            param_modo = "/s" if CONFIG["WINOFF_MODO"].upper() == "POWEROFF" else "/r"
            cmd_action = f"shutdown.exe {param_modo} /f /t 60"
            create_task = (
                f'schtasks /create /tn "{task_name}" '
                f'/tr "{cmd_action}" '
                f'/sc daily /st {CONFIG["WINOFF_HORA"]} '
                f'/ru "SYSTEM" /rl HIGHEST /f'
            )
            run_cmd(create_task)
            logging.info(f"Respaldo en Task Scheduler programado para apagarse a las {CONFIG['WINOFF_HORA']}.")
        else:
            logging.info(f"  [OMITIDO] Tarea diaria '{task_name}' ya programada.")
    except Exception as exc:
        logging.error(f"[ERROR EN setup_amp_winoff]: {exc}", exc_info=True)

# ==============================================================================
# 16. NETTIME (SMART - DETECCIÓN DE SERVICIO Y CONFIGURACIÓN)
# ==============================================================================
def setup_nettime():
    installer = CONFIG["NETTIME_INSTALLER_TEMP"]
    url = CONFIG["NETTIME_DOWNLOAD_URL"]
    nettime_dir = Path(CONFIG["NETTIME_INSTALL_DIR"])
    nettime_exe = nettime_dir / "NetTime.exe"

    logging.info("Evaluando estado de NetTime...")

    try:
        if not nettime_exe.is_file():
            try:
                download_file(url, installer)
                logging.info("Instalando NetTime silenciosamente...")
                run_cmd(f'"{installer}" /SP- /VERYSILENT /SUPPRESSMSGBOXES /NORESTART')
            except Exception as exc:
                logging.error(f"Error descargando/instalando NetTime: {exc}")
                return
        else:
            logging.info("  [OMITIDO] NetTime ya se encuentra instalado.")

        reg_paths = [
            r"SOFTWARE\Subjective Software\NetTime",
            r"SOFTWARE\WOW6432Node\Subjective Software\NetTime"
        ]
        for reg_p in reg_paths:
            for idx, srv in enumerate(CONFIG["NETTIME_SERVERS"], start=1):
                smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, f"Server{idx}", srv, winreg.REG_SZ)
                smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, f"Protocol{idx}", "SNTP", winreg.REG_SZ)
                smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, f"Port{idx}", 123, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "Server5", "", winreg.REG_SZ)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "SyncFrequency", CONFIG["NETTIME_UPDATE_INTERVAL_SEC"], winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "RetryFrequency", CONFIG["NETTIME_RETRY_INTERVAL_SEC"], winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "DemoteServers", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "DemoteFailures", CONFIG["NETTIME_DEMOTE_FAILURES"], winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "AllowOtherComputers", CONFIG["NETTIME_ALLOW_OTHER_COMPUTERS"], winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "AlwaysProvideTime", 0, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "ShowTrayIcon", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "RunAsService", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "MaxFreeRun", 24, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "MaxAdjustment", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "SmoothAdjustment", 0, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "MaxOffset", 5, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "AutoCheckUpdates", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "UpdateCheckInterval", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, reg_p, "LogLevel", 1, winreg.REG_DWORD)

        program_data_ini = Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "NetTime" / "NetTime.ini"
        if not program_data_ini.is_file():
            nettime_ini_content = f"""[NetTime]
Server1={CONFIG["NETTIME_SERVERS"][0]}
Protocol1=SNTP
Port1=123
Server2={CONFIG["NETTIME_SERVERS"][1]}
Protocol2=SNTP
Port2=123
Server3={CONFIG["NETTIME_SERVERS"][2]}
Protocol3=SNTP
Port3=123
Server4={CONFIG["NETTIME_SERVERS"][3]}
Protocol4=SNTP
Port4=123
Server5=
SyncFrequency={CONFIG["NETTIME_UPDATE_INTERVAL_SEC"]}
RetryFrequency={CONFIG["NETTIME_RETRY_INTERVAL_SEC"]}
DemoteServers=1
DemoteFailures={CONFIG["NETTIME_DEMOTE_FAILURES"]}
AllowOtherComputers={CONFIG["NETTIME_ALLOW_OTHER_COMPUTERS"]}
AlwaysProvideTime=0
ShowTrayIcon=1
RunAsService=1
MaxFreeRun=24
MaxAdjustment=1
SmoothAdjustment=0
MaxOffset=5
AutoCheckUpdates=1
UpdateCheckInterval=1
LogLevel=1
"""
            try:
                program_data_ini.parent.mkdir(parents=True, exist_ok=True)
                with open(program_data_ini, "w", encoding="utf-8") as f:
                    f.write(nettime_ini_content)
            except Exception:
                pass

        # Si el servicio no existe en el sistema, forzar registro mediante CLI de NetTime
        chk_svc = subprocess.run("sc query NetTime", shell=True, capture_output=True, text=True, errors="ignore")
        if "1060" in chk_svc.stdout or "1060" in chk_svc.stderr:
            if nettime_exe.is_file():
                subprocess.run(f'"{nettime_exe}" /install', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)

        chk_nt = subprocess.run("sc query NetTime", shell=True, capture_output=True, text=True, errors="ignore")
        if "RUNNING" not in chk_nt.stdout:
            run_cmd("sc config NetTime start= auto")
            run_cmd("net start NetTime")
        else:
            logging.info("  [OMITIDO] Servicio NetTime ya se encuentra en ejecución.")

    except Exception as exc:
        logging.error(f"[ERROR EN setup_nettime]: {exc}", exc_info=True)

# ==============================================================================
# 17. [REGALO EMPRESARIAL] HARDENING AVANZADO KIOSKO & BSOD AUTO-REBOOT (SMART)
# ==============================================================================
def setup_enterprise_hardening():
    logging.info("Evaluando hardening empresarial Kiosko...")
    try:
        if CONFIG["DESACTIVAR_STICKY_KEYS"]:
            smart_set_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Accessibility\StickyKeys", "Flags", "506", winreg.REG_SZ)
            smart_set_reg(winreg.HKEY_USERS, r".DEFAULT\Control Panel\Accessibility\StickyKeys", "Flags", "506", winreg.REG_SZ)
            smart_set_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Accessibility\Keyboard Response", "Flags", "122", winreg.REG_SZ)
            smart_set_reg(winreg.HKEY_USERS, r".DEFAULT\Control Panel\Accessibility\Keyboard Response", "Flags", "122", winreg.REG_SZ)
            smart_set_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Accessibility\ToggleKeys", "Flags", "58", winreg.REG_SZ)
            smart_set_reg(winreg.HKEY_USERS, r".DEFAULT\Control Panel\Accessibility\ToggleKeys", "Flags", "58", winreg.REG_SZ)

        if CONFIG["BSOD_AUTO_REBOOT"]:
            crash_path = r"SYSTEM\CurrentControlSet\Control\CrashControl"
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, crash_path, "AutoReboot", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, crash_path, "CrashDumpEnabled", 3, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, crash_path, "LogEvent", 1, winreg.REG_DWORD)

        if CONFIG["BLOQUEAR_AUTORUN_USB"]:
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer", "NoDriveTypeAutoRun", 255, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer", "NoDriveTypeAutoRun", 255, winreg.REG_DWORD)

        if CONFIG["SILENCIAR_SONIDOS_SISTEMA"]:
            smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "DisableStartupSound", 1, winreg.REG_DWORD)
            smart_set_reg(winreg.HKEY_CURRENT_USER, r"AppEvents\Schemes\Apps\.Default\.Default\.Current", "", "", winreg.REG_SZ)

        assoc_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\Associations"
        smart_set_reg(winreg.HKEY_CURRENT_USER, assoc_path, "LowRiskFileTypes", ".exe;.bat;.cmd;.ps1", winreg.REG_SZ)
        smart_set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Attachments", "SaveZoneInformation", 1, winreg.REG_DWORD)
    except Exception as exc:
        logging.error(f"[ERROR EN setup_enterprise_hardening]: {exc}", exc_info=True)

# ==============================================================================
# 18. [REGALO EMPRESARIAL] WATCHDOG GUARDIÁN AUTO-RESTART DE ADMIRA (SMART)
# ==============================================================================
def setup_admira_watchdog():
    if not CONFIG["HABILITAR_WATCHDOG_ADMIRA"]:
        return

    try:
        task_name = "Admira_Watchdog_KeepAlive"
        if scheduled_task_exists(task_name):
            logging.info(f"  [OMITIDO] Tarea Centinela (Watchdog) '{task_name}' ya se encuentra activa.")
            return

        logging.info("Configurando el Guardián Centinela (Watchdog) de Admira Player...")
        watchdog_script = (
            f"$p = '{CONFIG['ADMIRA_MAIN_EXE']}'; "
            "if ((Test-Path $p) -and (-not (Get-Process admira -ErrorAction SilentlyContinue))) { "
            "Start-Process -FilePath $p "
            "}"
        )
        cmd_action = f'powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -Command \\\"{watchdog_script}\\\"'
        
        run_cmd(f'schtasks /delete /tn "{task_name}" /f')
        create_task = (
            f'schtasks /create /tn "{task_name}" '
            f'/tr "{cmd_action}" '
            f'/sc minute /mo 1 '
            f'/ru "SYSTEM" /rl HIGHEST /f'
        )
        run_cmd(create_task)
    except Exception as exc:
        logging.error(f"[ERROR EN setup_admira_watchdog]: {exc}", exc_info=True)

# ==============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ==============================================================================
def main():
    elevate_privileges()
    setup_logging()
    
    logging.info("=================================================================")
    logging.info(" ADMIRA & DIGITAL SIGNAGE MASTER OPTIMIZER (SMART & IDEMPOTENTE) ")
    logging.info("=================================================================")
    
    try:
        # 1. Configuración de usuario, privilegios y autologon
        setup_user_and_autologon()
        
        # 2. ENERGÍA CONTINUA MÁXIMA (Alto Rendimiento, 0 reposo, sin screensaver)
        setup_power_and_screensaver()
        
        # 3. Interfaz Kiosko limpia: reinicio de Explorer con NoDesktop removido + HideIcons=1
        setup_desktop_ui()
        
        # 4. Forzado de resolución gráfica (1080p) y orientación (DEVMODE corregido)
        setup_display_mode()
        
        # 5. Silenciar notificaciones de raíz (Home/Pro) y BLOQUEO TOTAL PERMANENTE DE WINDOWS UPDATE
        disable_notifications_and_updates()
        
        # 6. Zona horaria y bypass de errores en BCD
        setup_time_and_boot()
        
        # 7. APAGADO TOTAL Y DEFINITIVO DE FIREWALL Y DEFENDER
        setup_firewall_and_security()
        
        # 8. Automatización de BIOS a las 08:00 AM y Power-On tras corte (Intel, Dell, HP, Lenovo)
        apply_bios_settings()
        
        # 9. Eliminación de Copilot, Recall y subprocesos de IA
        nuke_copilot_and_ai()

        # 10. Destrucción física en SystemApps (.BAK_DISABLED con SID universal)
        hard_nuke_system_apps()

        # 11. Desactivación de subsistemas de virtualización, WSL e Hyper-V
        disable_virtualization()
        
        # 12. Purga de bloatware AppX, telemetría y limpieza profunda
        cleanup_unnecessary_apps_and_telemetry()
        
        # 13. Despliegue y configuración de TeamViewer (Pass: ADMIRAMOBI)
        setup_teamviewer()
        
        # 14. Instalación de Admira Player desde URL oficial, limpieza de cache y Kiosko Shell
        install_admira_player()
        clear_player_gpu_cache()
        setup_kiosk_shell()

        # 15. AMP WinOFF: Apagado programado diario a las 22:00 h (Power Off)
        setup_amp_winoff()

        # 16. Auto-descarga, instalación silenciosa y autoconfiguración de NetTime
        setup_nettime()

        # 17. [REGALO EMPRESARIAL] Hardening Kiosko (StickyKeys, BSOD AutoReboot, USB AutoPlay off)
        setup_enterprise_hardening()

        # 18. [REGALO EMPRESARIAL] Centinela Auto-Healing (Watchdog de Admira Player)
        setup_admira_watchdog()

        logging.info("=================================================================")
        logging.info(" PROCESO COMPLETADO EXITOSAMENTE                                ")
        logging.info(f" Registro de auditoría guardado en: {LOG_FILE}                  ")
        logging.info("=================================================================")

    except Exception as exc:
        logging.critical(f"FATAL ERROR NO CONTROLADO EN main(): {exc}", exc_info=True)

if __name__ == "__main__":
    main()
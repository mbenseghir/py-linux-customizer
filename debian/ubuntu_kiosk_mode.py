#!/usr/bin/env python3
import os
import shutil
import subprocess
from pathlib import Path

DEFAULT_TIMEOUT = int(os.environ.get("ADMIRA_CMD_TIMEOUT", "4"))
LOG_PATH = Path(os.environ.get("ADMIRA_ENV_OPTIMIZER_LOG", "/opt/Admira/share/log/env_optimizer.log"))
INSTALLER_USER_FILE = Path("/opt/Admira/share/installer_user")
CA_BUNDLE = Path("/etc/ssl/ca-bundle.pem")

def log(message):
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(f"{message}\n")
    except Exception:
        pass

def is_root():
    return hasattr(os, "geteuid") and os.geteuid() == 0

def current_user():
    for key in ("SUDO_USER", "USER", "LOGNAME"):
        value = os.environ.get(key)
        if value and value != "root":
            return value
    return "root" if is_root() else os.environ.get("USERNAME", "admira")

def detect_target_user():
    env_user = os.environ.get("ADMIRA_GRAPHICAL_USER")
    if env_user:
        return env_user.strip()
    try:
        if INSTALLER_USER_FILE.exists():
            value = INSTALLER_USER_FILE.read_text(encoding="utf-8").strip()
            if value:
                return value
    except Exception:
        pass
    return current_user() if current_user() != "root" else "admira"

TARGET_USER = detect_target_user()

def command_exists(binary):
    return shutil.which(binary) is not None

def get_uid(user):
    try:
        result = subprocess.run(
            ["id", "-u", user],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as exc:
        log(f"uid lookup failed for {user}: {exc}")
    return None

def base_env(uid=None):
    env = os.environ.copy()
    env.setdefault("DISPLAY", ":0")
    env.setdefault("GDK_BACKEND", "x11")
    if CA_BUNDLE.exists():
        env.setdefault("NODE_EXTRA_CA_CERTS", str(CA_BUNDLE))
    if uid:
        env["XDG_RUNTIME_DIR"] = f"/run/user/{uid}"
        env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path=/run/user/{uid}/bus"
    return env

def run_cmd(cmd, timeout=DEFAULT_TIMEOUT, root=False):
    if not cmd or not command_exists(cmd[0]):
        log(f"skip missing command: {cmd[0] if cmd else '<empty>'}")
        return None
    final_cmd = list(cmd)
    if root and not is_root():
        if not command_exists("sudo"):
            log(f"skip root command without sudo: {' '.join(cmd)}")
            return None
        final_cmd = ["sudo", "-n"] + final_cmd
    try:
        result = subprocess.run(
            final_cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=timeout,
            env=base_env(),
        )
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            log(f"command rc={result.returncode}: {' '.join(final_cmd)} {stderr}")
        return result.returncode
    except subprocess.TimeoutExpired:
        log(f"timeout after {timeout}s: {' '.join(final_cmd)}")
    except Exception as exc:
        log(f"command failed: {' '.join(final_cmd)}: {exc}")
    return None

def run_user_cmd(cmd, timeout=DEFAULT_TIMEOUT):
    uid = get_uid(TARGET_USER)
    if not uid:
        return None

    if current_user() == TARGET_USER and not is_root():
        final_cmd = list(cmd)
        env = base_env(uid)
    elif is_root():
        if not command_exists("sudo"):
            log(f"skip user command without sudo: {' '.join(cmd)}")
            return None
        env_parts = [
            f"DISPLAY={os.environ.get('DISPLAY', ':0')}",
            "GDK_BACKEND=x11",
            f"XDG_RUNTIME_DIR=/run/user/{uid}",
            f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus",
        ]
        final_cmd = ["sudo", "-n", "-u", TARGET_USER, "env"] + env_parts + list(cmd)
        env = base_env(uid)
    else:
        log(f"skip user command as {current_user()} for target {TARGET_USER}: {' '.join(cmd)}")
        return None

    try:
        result = subprocess.run(
            final_cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=timeout,
            env=env,
        )
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            log(f"user command rc={result.returncode}: {' '.join(final_cmd)} {stderr}")
        return result.returncode
    except subprocess.TimeoutExpired:
        log(f"user command timeout after {timeout}s: {' '.join(final_cmd)}")
    except Exception as exc:
        log(f"user command failed: {' '.join(final_cmd)}: {exc}")
    return None

def schema_exists(schema_name):
    uid = get_uid(TARGET_USER)
    if not uid: return False
    env = base_env(uid)
    cmd = ["sudo", "-n", "-u", TARGET_USER, "gsettings", "list-schemas"] if is_root() else ["gsettings", "list-schemas"]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True, env=env)
        return schema_name in result.stdout
    except Exception:
        return False

def install_ubuntu_dependencies():
    packages = []
    if not command_exists("unclutter"):
        packages.append("unclutter")
    if not command_exists("cpupower"):
        packages.extend(["linux-tools-common", "linux-tools-generic"])
    
    if packages and is_root():
        log(f"Installing missing Ubuntu dependencies: {', '.join(packages)}")
        run_cmd(["apt-get", "update", "-qq"], root=True, timeout=30)
        run_cmd(["apt-get", "install", "-y", "-qq"] + packages, root=True, timeout=60)

def hide_os_ui():
    commands = [
        # Interfaz Base GNOME
        ["gsettings", "set", "org.gnome.shell", "disable-user-extensions", "false"],
        ["gsettings", "set", "org.gnome.shell", "disable-extension-version-validation", "true"],
        ["gsettings", "set", "org.gnome.shell", "disabled-extensions", "['ubuntu-dock@ubuntu.com', 'apps-menu@gnome-shell-extensions.gcampax.github.com', 'places-menu@gnome-shell-extensions.gcampax.github.com', 'window-list@gnome-shell-extensions.gcampax.github.com', 'launch-new-instance@gnome-shell-extensions.gcampax.github.com', 'sle-classic@suse.com']"],
        
        # Bloqueo de atajos (Modo Kiosko)
        ["gsettings", "set", "org.gnome.mutter", "overlay-key", "''"], 
        ["gsettings", "set", "org.gnome.desktop.wm.keybindings", "panel-run-dialog", "[]"], 
        ["gsettings", "set", "org.gnome.desktop.wm.keybindings", "switch-applications", "[]"],
        
        # Ajustes nativos de Dash to Dock (Ubuntu Dock)
        ["gsettings", "set", "org.gnome.shell.extensions.dash-to-dock", "dock-fixed", "false"],
        ["gsettings", "set", "org.gnome.shell.extensions.dash-to-dock", "autohide", "true"],
        ["gsettings", "set", "org.gnome.shell.extensions.dash-to-dock", "intellihide", "false"],
        
        # Preferencias de ventanas y animaciones
        ["gsettings", "set", "org.gnome.desktop.background", "show-desktop-icons", "false"],
        ["gsettings", "set", "org.gnome.desktop.wm.preferences", "button-layout", "''"],
        ["gsettings", "set", "org.gnome.desktop.wm.preferences", "auto-raise", "false"],
        ["gsettings", "set", "org.gnome.desktop.interface", "enable-animations", "false"],
        ["gsettings", "set", "org.gnome.desktop.interface", "enable-hot-corners", "false"],
    ]

    # Validacion para evitar errores en el log si just-perfection no existe
    if schema_exists("org.gnome.shell.extensions.just-perfection"):
        commands.extend([
            ["gsettings", "set", "org.gnome.shell.extensions.just-perfection", "panel", "false"],
            ["gsettings", "set", "org.gnome.shell.extensions.just-perfection", "panel-in-fullscreen", "false"],
            ["gsettings", "set", "org.gnome.shell.extensions.just-perfection", "clock-menu", "false"],
            ["gsettings", "set", "org.gnome.shell.extensions.just-perfection", "notification-banner", "false"]
        ])

    for command in commands:
        run_user_cmd(command)

    if command_exists("gnome-extensions"):
        run_user_cmd(["gnome-extensions", "disable", "ubuntu-dock@ubuntu.com"])
        
        # Habilitar solo si estan en el sistema
        for ext in ("just-perfection-desktop@just-perfection", "ding@rastersoft.com", "desktop-icons@gnome-shell-extensions.gcampax.github.com"):
            # Intento de habilitar controlado
            uid = get_uid(TARGET_USER)
            if uid:
                env = base_env(uid)
                cmd = ["sudo", "-n", "-u", TARGET_USER, "gnome-extensions", "list"] if is_root() else ["gnome-extensions", "list"]
                try:
                    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True, env=env)
                    if ext in res.stdout:
                        run_user_cmd(["gnome-extensions", "enable", ext])
                except Exception:
                    pass

def disable_power_management():
    for command in (["xset", "s", "off"], ["xset", "s", "noblank"], ["xset", "-dpms"], ["xset", "dpms", "force", "on"]):
        run_cmd(command)

    for command in (
        ["gsettings", "set", "org.gnome.desktop.session", "idle-delay", "0"],
        ["gsettings", "set", "org.gnome.desktop.screensaver", "lock-enabled", "false"],
        ["gsettings", "set", "org.gnome.settings-daemon.plugins.power", "sleep-inactive-ac-type", "nothing"],
        ["gsettings", "set", "org.gnome.settings-daemon.plugins.power", "sleep-inactive-battery-type", "nothing"],
        ["gsettings", "set", "org.gnome.settings-daemon.plugins.power", "idle-dim", "false"],
    ):
        run_user_cmd(command)

def disable_notifications_and_updates():
    for command in (
        ["gsettings", "set", "org.gnome.desktop.notifications", "show-banners", "false"],
        ["gsettings", "set", "org.gnome.desktop.notifications", "show-in-lock-screen", "false"],
        ["gsettings", "set", "org.gnome.software", "download-updates", "false"],
        ["gsettings", "set", "org.gnome.software", "allow-updates", "false"],
        ["gsettings", "set", "org.gnome.settings-daemon.plugins.updates", "active", "false"],
        ["gsettings", "set", "org.gnome.desktop.privacy", "report-technical-problems", "false"],
    ):
        run_user_cmd(command)

def force_display_brightness():
    if not command_exists("xrandr"):
        return
    try:
        result = subprocess.run(
            ["xrandr", "--query"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=DEFAULT_TIMEOUT,
            env=base_env(),
        )
        if result.returncode != 0:
            log(f"xrandr query failed: {(result.stderr or '').strip()}")
            return
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "connected":
                run_cmd(["xrandr", "--output", parts[0], "--brightness", "1"])
    except subprocess.TimeoutExpired:
        log("xrandr query timeout")
    except Exception as exc:
        log(f"xrandr brightness failed: {exc}")

def hide_mouse_cursor():
    run_cmd(["killall", "unclutter"])
    if command_exists("unclutter"):
        try:
            subprocess.Popen(
                ["unclutter", "-idle", "2", "-root"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=base_env(),
            )
        except Exception as exc:
            log(f"unclutter start failed: {exc}")

def optimize_node_limits():
    run_cmd(["sysctl", "-w", "fs.inotify.max_user_watches=524288"], root=True)

def target_home():
    expanded = Path(f"~{TARGET_USER}").expanduser()
    if str(expanded).startswith("~"):
        try:
            result = subprocess.run(
                ["getent", "passwd", TARGET_USER],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=2,
            )
            if result.returncode == 0:
                return Path(result.stdout.split(":")[5])
        except Exception:
            pass
    return expanded

def clear_gpu_cache():
    cache_path = target_home() / ".config" / "admira-player" / "GPUCache"
    try:
        if cache_path.exists() and cache_path.is_dir():
            shutil.rmtree(cache_path, ignore_errors=True)
    except Exception as exc:
        log(f"gpu cache cleanup failed: {exc}")

def set_cpu_performance():
    binary = "cpupower" if command_exists("cpupower") else None
    if binary:
        run_cmd([binary, "frequency-set", "-g", "performance"], timeout=8, root=True)

def force_black_desktop():
    for command in (
        ["gsettings", "set", "org.gnome.desktop.background", "picture-options", "none"],
        ["gsettings", "set", "org.gnome.desktop.background", "primary-color", "#000000"],
        ["gsettings", "set", "org.gnome.desktop.background", "color-shading-type", "solid"],
    ):
        run_user_cmd(command)

if __name__ == "__main__":
    log(f"env_optimizer start target_user={TARGET_USER}")
    install_ubuntu_dependencies()
    hide_os_ui()
    disable_power_management()
    disable_notifications_and_updates()
    force_display_brightness()
    hide_mouse_cursor()
    optimize_node_limits()
    clear_gpu_cache()
    set_cpu_performance()
    force_black_desktop()
    log("env_optimizer done")
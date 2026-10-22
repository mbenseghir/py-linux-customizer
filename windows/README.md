# Windows Kiosk & Digital Signage Setup

Configurador automatizado para Windows 7, 10 y 11 (32 y 64 bits).

### Ejecución en 1 línea (PowerShell como Administrador)

No requiere instalar Python. Descarga el entorno portable en `%TEMP%`, te pide la contraseña de TeamViewer por pantalla y ejecuta todo:

```powershell
powershell -ExecutionPolicy Bypass -NoProfile -Command "$env:TV_PASS = Read-Host 'Introduce la clave de TeamViewer'; $dir=\"$env:TEMP\py_runtime\"; if(-not (Test-Path \"$dir\python.exe\")){ New-Item -ItemType Directory -Path $dir -Force | Out-Null; (New-Object Net.WebClient).DownloadFile('[https://www.python.org/ftp/python/3.8.10/python-3.8.10-embed-amd64.zip](https://www.python.org/ftp/python/3.8.10/python-3.8.10-embed-amd64.zip)', \"$dir\py.zip\"); Expand-Archive \"$dir\py.zip\" -DestinationPath $dir -Force; }; (New-Object Net.WebClient).DownloadFile('[https://raw.githubusercontent.com/mbenseghir/py-linux-customizer/main/windows/win_kiosk_mode.py](https://raw.githubusercontent.com/mbenseghir/py-linux-customizer/main/windows/win_kiosk_mode.py)', \"$dir\win_kiosk.py\"); & \"$dir\python.exe\" \"$dir\win_kiosk.py\""
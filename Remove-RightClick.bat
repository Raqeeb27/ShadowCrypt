@echo off
setlocal

set hide_shortcut_path=%APPDATA%\Microsoft\Windows\SendTo\Hide Selected Files.lnk
set recovery_shortcut_path=%APPDATA%\Microsoft\Windows\SendTo\Recover Selected Files.lnk

echo.
echo "[*] Removing registry entries for Hide File (Create lnk File) and Recover File (Extract File)..."
echo.

reg delete "HKEY_CLASSES_ROOT\*\shell\Hide File" /f
reg delete "HKEY_CLASSES_ROOT\Lnkfile\shell\Recover File" /f
reg delete "HKEY_CLASSES_ROOT\Directory\Background\shell\Recover All" /f
reg delete "HKEY_CLASSES_ROOT\Directory\Background\shell\Recover Files in This Folder" /f
reg delete "HKEY_CLASSES_ROOT\Directory\Background\shell\Recover Files Recursively" /f

if exist "%hide_shortcut_path%" (
    del "%hide_shortcut_path%"
)
if exist "%recovery_shortcut_path%" (
    del "%recovery_shortcut_path%"
)

pause
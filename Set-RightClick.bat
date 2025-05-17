@echo off
setlocal

SET shadowcrypt_path=%~dp0dist\ShadowCrypt.exe
SET hiding_path=%~dp0dist\hiding.exe
SET recovery_path=%~dp0dist\recovery.exe
SET sendto_path=%APPDATA%\Microsoft\Windows\SendTo
SET vbs_file=%TEMP%\create_shortcuts.vbs
SET hide_shortcut_name=Hide Selected Files.lnk
SET recover_shortcut_name=Recover Selected Files.lnk

echo.
echo "[*] Adding registry entries for Hide File (Create lnk File) and Recover File (Extract File)..."
echo.

reg add "HKEY_CLASSES_ROOT\*\shell\Hide File" /t REG_SZ /v "" /d "Hide File (Create lnk File)" /f
reg add "HKEY_CLASSES_ROOT\*\shell\Hide File" /v "MultiSelectModel" /t REG_SZ /d "Single" /f
reg add "HKEY_CLASSES_ROOT\*\shell\Hide File" /t REG_SZ /v "Icon" /d "%shadowcrypt_path%" /f
reg add "HKEY_CLASSES_ROOT\*\shell\Hide File\command" /t REG_SZ /v "" /d "\"%shadowcrypt_path%\" hide --files \"%%1\"" /f

reg add "HKEY_CLASSES_ROOT\Lnkfile\shell\Recover File" /t REG_SZ /v "" /d "Recover File (Extract File)" /f
reg add "HKEY_CLASSES_ROOT\Lnkfile\shell\Recover File" /v "MultiSelectModel" /t REG_SZ /d "Single" /f
reg add "HKEY_CLASSES_ROOT\Lnkfile\shell\Recover File" /t REG_SZ /v "Icon" /d "%shadowcrypt_path%" /f
reg add "HKEY_CLASSES_ROOT\Lnkfile\shell\Recover File\command" /t REG_SZ /v "" /d "\"%shadowcrypt_path%\" recover --link_files \"%%1\"" /f

reg add "HKEY_CLASSES_ROOT\Directory\Background\shell\Recover All" /t REG_SZ /v "" /d "Recover All (Extract All Files)" /f
reg add "HKEY_CLASSES_ROOT\Directory\Background\shell\Recover All" /t REG_SZ /v "Icon" /d "%shadowcrypt_path%" /f
reg add "HKEY_CLASSES_ROOT\Directory\Background\shell\Recover All\command" /t REG_SZ /v "" /d "\"%shadowcrypt_path%\" recover --all" /f

reg add "HKEY_CLASSES_ROOT\Directory\Background\shell\Recover Files in This Folder" /t REG_SZ /v "" /d "Recover Files in This Folder" /f
reg add "HKEY_CLASSES_ROOT\Directory\Background\shell\Recover Files in This Folder" /t REG_SZ /v "Icon" /d "%shadowcrypt_path%" /f
reg add "HKEY_CLASSES_ROOT\Directory\Background\shell\Recover Files in This Folder\command" /t REG_SZ /v "" /d "\"%shadowcrypt_path%\" recover --dir \"%%V\"" /f

reg add "HKEY_CLASSES_ROOT\Directory\Background\shell\Recover Files Recursively" /t REG_SZ /v "" /d "Recover Files Recursively (Include Subfolders)" /f
reg add "HKEY_CLASSES_ROOT\Directory\Background\shell\Recover Files Recursively" /t REG_SZ /v "Icon" /d "%shadowcrypt_path%" /f
reg add "HKEY_CLASSES_ROOT\Directory\Background\shell\Recover Files Recursively\command" /t REG_SZ /v "" /d "\"%shadowcrypt_path%\" recover --recursive --dir \"%%V\"" /f


echo Set oWS = WScript.CreateObject("WScript.Shell") > "%vbs_file%"
echo Set oLink = oWS.CreateShortcut("%sendto_path%\%hide_shortcut_name%") >> "%vbs_file%"
echo oLink.TargetPath = "%shadowcrypt_path%" >> "%vbs_file%"
echo oLink.Arguments = "hide --files" >> "%vbs_file%"
echo oLink.Save >> "%vbs_file%"

echo Set oLink = oWS.CreateShortcut("%sendto_path%\%recover_shortcut_name%") >> "%vbs_file%"
echo oLink.TargetPath = "%shadowcrypt_path%" >> "%vbs_file%"
echo oLink.Arguments = "recover --link_files" >> "%vbs_file%"
echo oLink.Save >> "%vbs_file%"
cscript //nologo "%vbs_file%"
del "%vbs_file%"

if not exist "%~dp0Uninstallation" mkdir "%~dp0Uninstallation"
copy "%~dp0Remove-RightClick.bat" "%~dp0Uninstallation\Remove-RightClickMenuOptions.bat"

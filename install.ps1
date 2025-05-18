<#
.SYNOPSIS
Installation script for ShadowCrypt.

.DESCRIPTION
This PowerShell script (install.ps1) is intended to automate the installation process for the ShadowCrypt application.

.NOTES
File: install.ps1
#>

echo "[*] Installing environment with uv.`n"
uv sync
echo "`n[+] Environment installation successfull.`n"
echo "`n---------------------------------`n"


echo "[*] Initializing databases.`n"
if ((Test-Path "db\enc_mapping.dll") -and (Test-Path "db\app_path.dll")) {
    $confirmation = Read-Host "Do you want to reinitialize the database?`n**Recommended** - Recover all the hidden files first!`nWarning: This will overwrite the existing databases.`nType 'yes' to continue "
} else {
    $confirmation = "yes"
}

if ($confirmation -ne "yes" -and $confirmation -ne "y") {
    Write-Host "`n[!] Aborting database initialization."
}
else {
    $output = uv run init_db.py | ForEach-Object { Write-Host $_; $_ }
    if ($output) {
        if ($output[-1] -eq "[-] PASSWORD ERROR" -or $output[-1] -eq "[-] Keyboard Interrupt" -or $output[-1] -eq "[-] PATH ERROR") {
            Write-Host "[!] Installation Failed!!!"
            Read-Host "`nPress any key to exit"
            exit 1
        }
    }
    else {
        Write-Host "`n[+] Databases initialization successfull."
    }
}

echo "`n---------------------------------`n"


echo "[*] Building executables.`n"

if (Test-Path "dist") {
    Remove-Item -Recurse -Force dist
}

uv run pyinstaller -F ShadowCrypt.py --uac-admin --manifest admin.manifest --icon=icon\ShadowCrypt.ico
uv run pyinstaller -F hiding.py --icon=icon\ShadowCrypt.ico
uv run pyinstaller -F recovery.py --icon=icon\ShadowCrypt.ico
uv run pyinstaller -F linker.py --icon=icon\ShadowCrypt.ico
uv run pyinstaller -F init_db.py --icon=icon\ShadowCrypt.ico --distpath=.
echo "`n---------------------------------`n"


echo "[*] Cleaning Up.`n"
rm *.spec
rm -r build/
echo "`n[+] Done"
echo "`n---------------------------------`n"

Write-Host "[+] Installation completed successfully.`n"

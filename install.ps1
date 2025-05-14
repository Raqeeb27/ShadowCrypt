# install.ps1

echo "[*] Installing environment with uv.`n"
uv sync
echo "`n[+] Environment installation successfull.`n"
echo "`n---------------------------------`n"


echo "[*] Initializing databases.`n"
$output = uv run init_db.py | ForEach-Object { Write-Host $_; $_ }
if ($output) {
    if ($output[-1] -eq "[-] PASSWORD ERROR" -or $output[-1] -eq "[-] Keyboard Interrupt" -or $output[-1] -eq "[-] PATH ERROR") {
        Write-Host "[!] Installation Failed!!!"
        exit 1
    }
}
else {
    Write-Host "`n[+] Databases initialization successfull."
}

echo "`n---------------------------------`n"


echo "[*] Building executables.`n"

if (Test-Path "dist") {
    Remove-Item -Recurse -Force dist
}

uv run pyinstaller -F ShadowCrypt.py --uac-admin --manifest admin.manifest
uv run pyinstaller -F hiding.py
uv run pyinstaller -F recovery.py
uv run pyinstaller -F linker.py
echo "`n---------------------------------`n"


echo "[*] Cleaning Up.`n"
rm *.spec
rm -r build/
echo "`n[+] Done`n"
echo "`n---------------------------------`n"

Write-Host "[+] Installation completed successfully.`n"

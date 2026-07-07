@echo off
:: Check for administrative permissions
openfiles >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process -FilePath '%0' -Verb RunAs"
    exit /b
)

echo ===================================================
echo   AUTOMATED MYSQL PASSWORD RESET FOR SMART LENDER  
echo ===================================================
echo.
echo Stopping MySQL service...
net stop MySQL80

echo Creating temporary password initialization file...
echo ALTER USER 'root'@'localhost' IDENTIFIED BY 'Kaladhar*011'; > "%TEMP%\mysql-init.txt"

echo Launching MySQL in password-reset mode...
start "" "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --defaults-file="C:\ProgramData\MySQL\MySQL Server 8.0\my.ini" --init-file="%TEMP%\mysql-init.txt" --console

echo Waiting for 8 seconds for password reset to apply...
timeout /t 8 /nobreak >nul

echo Stopping temporary MySQL server...
taskkill /f /im mysqld.exe

echo Cleaning up temporary files...
del "%TEMP%\mysql-init.txt"

echo Restarting MySQL service normally...
net start MySQL80

echo.
echo ===================================================
echo   SUCCESS! MySQL Root password is now: Kaladhar*011
echo ===================================================
pause

@echo off
cd /d "%~dp0"
echo SAPI Bridge (GeminiSapiBridge.dll) を解除しています...
C:\Windows\Microsoft.NET\Framework\v4.0.30319\RegAsm.exe GeminiSapiBridge.dll /unregister
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\RegAsm.exe GeminiSapiBridge.dll /unregister
echo.
echo 解除が完了しました。何かキーを押して終了してください。
pause >nul

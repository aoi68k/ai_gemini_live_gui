@echo off
cd /d "%~dp0"
echo SAPI Bridge (GeminiSapiBridge.dll) を登録しています...
C:\Windows\Microsoft.NET\Framework\v4.0.30319\RegAsm.exe GeminiSapiBridge.dll /codebase
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\RegAsm.exe GeminiSapiBridge.dll /codebase
echo.
echo 登録が完了しました。何かキーを押して終了してください。
pause >nul

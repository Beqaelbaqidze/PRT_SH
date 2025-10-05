@echo off
setlocal

:: Set base directory
set "base=%PRINT_SHIDA_PATH%\Exports"

:: Find the newest folder in the base directory
for /f "delims=" %%i in ('powershell -nologo -command ^
  "Get-ChildItem -Path '%base%' -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | ForEach-Object { $_.FullName }"') do (
  set "newest=%%i"
)

:: Open the newest folder in Explorer
if defined newest (
  echo Opening newest folder: %newest%
  start "" "%newest%"
) else (
  echo No folders found in %base%
)

endlocal

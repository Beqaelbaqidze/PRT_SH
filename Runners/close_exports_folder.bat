@echo off
setlocal

:: Define target folder substring to match
set "target=%PRINT_SHIDA_PATH%\Exports"

:: Use PowerShell to find and close matching Explorer windows
powershell -nologo -command ^
"Add-Type -AssemblyName 'Microsoft.VisualBasic'; ^
 $shell = New-Object -ComObject Shell.Application; ^
 $windows = $shell.Windows(); ^
 foreach ($win in $windows) { ^
   try { ^
     $path = $win.Document.Folder.Self.Path; ^
     if ($path -like '*%target%*') { ^
       Write-Host 'Closing:' $path; ^
       $win.Quit(); ^
     } ^
   } catch {} ^
 }"

endlocal

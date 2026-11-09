@echo off
setlocal
set "APP_DIR=%~dp0"
if exist "%APP_DIR%local-settings.bat" call "%APP_DIR%local-settings.bat"
if exist "%APP_DIR%xampp-path.bat" call "%APP_DIR%xampp-path.bat"
if defined XAMPP_HOME if not exist "%XAMPP_HOME%\php\php.exe" set "XAMPP_HOME="

rem Try common XAMPP locations before asking the user to browse.
if not defined XAMPP_HOME if exist "%SystemDrive%\xampp\php\php.exe" set "XAMPP_HOME=%SystemDrive%\xampp"
if not defined XAMPP_HOME if exist "%ProgramFiles%\xampp\php\php.exe" set "XAMPP_HOME=%ProgramFiles%\xampp"
if not defined XAMPP_HOME if exist "%ProgramFiles(x86)%\xampp\php\php.exe" set "XAMPP_HOME=%ProgramFiles(x86)%\xampp"
for %%D in (D E F G H I J K L M N O P) do if not defined XAMPP_HOME if exist "%%D:\xampp\php\php.exe" set "XAMPP_HOME=%%D:\xampp"

if not defined XAMPP_HOME (
 echo Select the XAMPP installation folder in the folder picker.
 for /f "usebackq delims=" %%I in (`powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "%APP_DIR%select-xampp.ps1"`) do set "XAMPP_HOME=%%I"
)
if not defined XAMPP_HOME (
 echo No XAMPP folder was selected. Run this launcher again and select the folder containing php\php.exe and htdocs.
 pause
 exit /b 1
)
if not exist "%XAMPP_HOME%\php\php.exe" (
 echo PHP was not found inside "%XAMPP_HOME%". Select the XAMPP installation folder, not its htdocs folder.
 pause
 exit /b 1
)
if not exist "%XAMPP_HOME%\htdocs" (
 echo The htdocs folder was not found inside "%XAMPP_HOME%".
 pause
 exit /b 1
)

rem Remember the selected location without changing other local settings.
>"%APP_DIR%xampp-path.bat" echo @echo off
>>"%APP_DIR%xampp-path.bat" echo set "XAMPP_HOME=%XAMPP_HOME%"

if not exist "%XAMPP_HOME%\htdocs\skillgraph" mkdir "%XAMPP_HOME%\htdocs\skillgraph"
xcopy "%APP_DIR%site\*" "%XAMPP_HOME%\htdocs\skillgraph\" /E /I /Y >nul
copy /Y "%APP_DIR%.htaccess" "%XAMPP_HOME%\htdocs\skillgraph\.htaccess" >nul
if not exist "%XAMPP_HOME%\htdocs\skillgraph\api" mkdir "%XAMPP_HOME%\htdocs\skillgraph\api"
xcopy "%APP_DIR%php-api\*" "%XAMPP_HOME%\htdocs\skillgraph\api\" /E /I /Y >nul
if not exist "%XAMPP_HOME%\htdocs\skillgraph\api\config.php" (
 copy "%APP_DIR%php-api\config.example.php" "%XAMPP_HOME%\htdocs\skillgraph\api\config.php" >nul
 echo Created API config. Edit the MySQL user/password and JWT secret, then run this launcher again.
 start "" notepad "%XAMPP_HOME%\htdocs\skillgraph\api\config.php"
 pause
 exit /b 1
)
"%XAMPP_HOME%\php\php.exe" "%XAMPP_HOME%\htdocs\skillgraph\api\setup.php"
if errorlevel 1 (
 echo Database initialization failed. Start MySQL in XAMPP Control Panel and check api\config.php.
 pause
 exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%APP_DIR%backend\start_backend.ps1"
if errorlevel 1 (
 echo SkillGraph API could not start. Check that MySQL is running in XAMPP.
 pause
 exit /b 1
)
start "" "http://localhost/skillgraph/"
echo SkillGraph is ready. Apache and MySQL must be running in XAMPP Control Panel.
endlocal



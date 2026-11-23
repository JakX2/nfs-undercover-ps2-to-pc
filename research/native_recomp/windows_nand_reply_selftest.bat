@echo off
setlocal EnableExtensions
rem Original-free Wii NAND / Starlet deferred reply test for Windows.
rem Does not read, modify or require a proprietary Undercover executable.

set "SOURCE=%~dp0test_wii_nand_ios_reply_v374.cpp"
set "INCLUDE=%~dp0"
if not exist "%SOURCE%" (
  echo ERROR: V374 C++ regression missing in this checkout.
  exit /b 2
)

set "BUILD=%TEMP%\undercover-nand-v374-%RANDOM%-%RANDOM%"
mkdir "%BUILD%" || exit /b 2
set "OUTPUT=%BUILD%\nand-v374-test.exe"
pushd "%BUILD%" || exit /b 2

where cl.exe >NUL 2>&1
if not errorlevel 1 goto :msvc
where g++.exe >NUL 2>&1
if not errorlevel 1 goto :mingw
echo ERROR: No C++20 compiler found on PATH.
echo Use a Visual Studio 2022 Developer Command Prompt or MinGW-w64 with g++.
goto :fail

:msvc
echo Building with MSVC...
cl.exe /nologo /std:c++20 /EHsc /W3 /WX /I "%INCLUDE%" "%SOURCE%" "/Fe:%OUTPUT%"
if errorlevel 1 goto :fail
goto :run

:mingw
echo Building with MinGW-w64 g++...
g++.exe -std=c++20 -O2 -Wall -Wextra -Werror -I "%INCLUDE%" "%SOURCE%" -o "%OUTPUT%"
if errorlevel 1 goto :fail
goto :run

:run
echo Running original-free deferred IOS reply regression...
"%OUTPUT%"
set "RESULT=%ERRORLEVEL%"
popd
rmdir /s /q "%BUILD%"
if not "%RESULT%"=="0" (
  echo FAIL: V374 Windows regression exit code %RESULT%.
  exit /b %RESULT%
)
echo PASS: Windows native C++20 V374 deferred reply regression.
exit /b 0

:fail
popd
rmdir /s /q "%BUILD%"
echo FAIL: V374 Windows test could not compile or execute.
exit /b 1

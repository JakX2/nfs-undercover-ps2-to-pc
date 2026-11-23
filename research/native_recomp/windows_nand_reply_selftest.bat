@echo off
setlocal EnableExtensions
rem Original-free Wii NAND IPC/IOS and PowerPC exception self-test on Windows.
rem No proprietary Need for Speed: Undercover executable or game data needed.

set "INCLUDE=%~dp0"
set "SOURCE374=%~dp0test_wii_nand_ios_reply_v374.cpp"
set "SOURCE376=%~dp0test_wii_nand_y1_exception_v376.cpp"
if not exist "%SOURCE374%" (
  echo ERROR: V374 source missing from this checkout.
  exit /b 2
)
if not exist "%SOURCE376%" (
  echo ERROR: V376 source missing from this checkout.
  exit /b 2
)

set "BUILD=%TEMP%\undercover-nand-v374-v376-%RANDOM%-%RANDOM%"
mkdir "%BUILD%" || exit /b 2
set "OUTPUT374=%BUILD%\nand-v374-test.exe"
set "OUTPUT376=%BUILD%\nand-v376-test.exe"
pushd "%BUILD%" || exit /b 2

where cl.exe >NUL 2>&1
if not errorlevel 1 goto :msvc
where g++.exe >NUL 2>&1
if not errorlevel 1 goto :mingw
echo ERROR: Neither MSVC cl.exe nor MinGW-w64 g++.exe is on PATH.
echo Use a Visual Studio 2022 Developer Command Prompt or MinGW-w64 terminal.
goto :fail

:msvc
echo Building V374 and V376 using MSVC C++20...
cl.exe /nologo /std:c++20 /EHsc /W3 /WX /I "%INCLUDE%" "%SOURCE374%" "/Fe:%OUTPUT374%"
if errorlevel 1 goto :fail
cl.exe /nologo /std:c++20 /EHsc /W3 /WX /I "%INCLUDE%" "%SOURCE376%" "/Fe:%OUTPUT376%"
if errorlevel 1 goto :fail
goto :run

:mingw
echo Building V374 and V376 using MinGW-w64 C++20...
g++.exe -std=c++20 -O2 -Wall -Wextra -Werror -I "%INCLUDE%" "%SOURCE374%" -o "%OUTPUT374%"
if errorlevel 1 goto :fail
g++.exe -std=c++20 -O2 -Wall -Wextra -Werror -I "%INCLUDE%" "%SOURCE376%" -o "%OUTPUT376%"
if errorlevel 1 goto :fail
goto :run

:run
echo Running V374 native Starlet ACK and queued reply regression...
"%OUTPUT374%"
if errorlevel 1 goto :fail
echo Running V376 genuine Y1 PowerPC exception-entry regression...
"%OUTPUT376%"
if errorlevel 1 goto :fail
popd
rmdir /s /q "%BUILD%"
echo PASS: Windows C++20 V374 and V376 native IPC/IRQ regressions.
exit /b 0

:fail
popd
rmdir /s /q "%BUILD%"
echo FAIL: V374/V376 Windows compilation or native execution.
exit /b 1

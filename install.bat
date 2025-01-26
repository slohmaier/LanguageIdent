REM Description: Build Install the add-on
REM Author: Stefan Lohmaier stefan@slohmaier.de

REM Clean all nvda-addon files
del *.nvda-addon /F

REM Build the add-on
scons

@echo off
echo Install the add-on...
for %%a in (*.nvda-addon) do (
  start %%a
  goto :eof
)
echo No .nvda-addon files found.
pause

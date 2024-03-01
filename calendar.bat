@echo off

:: Open a new console window to run the Python script
start "Python Script" cmd /k "ical_to_gcal_sync.py"

:: Open another new console window to tail the logger file
start "Log File" cmd /k "powershell -Command "ical_to_gcal_sync.log -Wait""
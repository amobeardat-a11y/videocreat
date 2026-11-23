@echo off
title Mo Chrome Ket Noi Veo AI
echo Dang khoi dong Google Chrome voi cong dieu khien 9222...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\AutomationData" "https://flow.google.com"
exit

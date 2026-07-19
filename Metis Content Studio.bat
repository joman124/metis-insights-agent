@echo off
REM ===================================================================
REM  Metis Content Studio -- both agents on one page.
REM
REM  Double-click this file. A black console window opens, and after a
REM  few seconds a browser tab opens at http://localhost:8501 showing a
REM  sidebar with two entries:
REM      Insights Engine   (essays + field notes for the website)
REM      Viral Agent       (LinkedIn posts + approval queue)
REM
REM  To STOP the app: close this black console window (or press Ctrl+C
REM  in it). Closing just the browser tab does NOT stop it -- the
REM  console window is the app; the browser is only the view.
REM ===================================================================

setlocal
cd /d "%~dp0"

REM Streamlit's first-ever launch pauses to ask for an email in the
REM console, which looks like a hang. Writing a blank credentials file
REM once skips that prompt forever.
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    echo [general]> "%USERPROFILE%\.streamlit\credentials.toml"
    echo email = "">> "%USERPROFILE%\.streamlit\credentials.toml"
)

echo Starting Metis Content Studio... a browser tab will open shortly.
echo Leave this window open while you use the app. Close it to stop.
echo.

REM Use "python -m streamlit" -- the bare "streamlit" command is only on
REM PATH inside a virtualenv, but "python -m streamlit" always works as
REM long as Streamlit is installed for this Python.
python -m streamlit run dashboard.py

REM If Python itself is missing you will see an error above; press a key
REM to keep this window open so you can read it.
if errorlevel 1 pause
endlocal

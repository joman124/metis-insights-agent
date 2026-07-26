@echo off
REM Opens JUST the viral content dashboard (app.py) at
REM http://localhost:8502, without the essays side.
REM
REM Most of the time you want the whole studio instead: double-click
REM "Metis Content Studio.bat" in the folder above, which puts Viral
REM Content and Essays & Field Notes behind one sidebar on port 8501.
REM
REM To stop the app: close this black console window (or press Ctrl+C in it).
REM Closing just the browser tab does NOT stop it - the console window is
REM the app; the browser is only the view.

setlocal
cd /d "%~dp0"

REM One virtualenv serves both apps, and it lives in the parent folder.
REM Keeping a second copy here only invited version drift between the
REM studio and this standalone run.
set PY=..\.venv\Scripts\python.exe
if not exist "%PY%" (
    echo Could not find the virtualenv at %PY%
    echo Set it up from the parent folder:
    echo     python -m venv .venv
    echo     .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    endlocal & exit /b 1
)

REM Streamlit's very first launch stops to ask for an email address in the
REM console, which looks like a hang if you double-clicked this file. Writing
REM a blank credentials file once skips that prompt forever.
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    echo [general]> "%USERPROFILE%\.streamlit\credentials.toml"
    echo email = "">> "%USERPROFILE%\.streamlit\credentials.toml"
)

echo Starting the viral dashboard... a browser tab will open in a few seconds.
echo Leave this window open while you use the app. Close it to stop the app.
"%PY%" -m streamlit run app.py

endlocal

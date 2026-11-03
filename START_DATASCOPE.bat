@echo off
cd /d "%~dp0"
title DataScope - Python Streamlit
echo ===========================================
echo          DataScope - Starting
echo ===========================================
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 --version
  if errorlevel 1 goto python_missing
  py -3 -m pip install --upgrade pip
  py -3 -m pip install -r requirements.txt
  if errorlevel 1 goto install_failed
  py -3 -m streamlit run app.py
  goto end
)
where python >nul 2>&1
if %errorlevel%==0 (
  python --version
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
  if errorlevel 1 goto install_failed
  python -m streamlit run app.py
  goto end
)
:python_missing
echo.
echo Python was not found.
echo Install Python 3.10 or newer from https://www.python.org/downloads/
echo IMPORTANT: select "Add python.exe to PATH" during installation.
start "" "https://www.python.org/downloads/"
pause
goto end
:install_failed
echo.
echo Package installation failed. Check your internet connection and try again.
pause
:end

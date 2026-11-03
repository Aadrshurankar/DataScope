@echo off
cd /d "%~dp0"
echo === Python ===
where py
py -3 --version
echo.
echo === pip ===
py -3 -m pip --version
echo.
echo === Streamlit ===
py -3 -m streamlit --version
echo.
pause

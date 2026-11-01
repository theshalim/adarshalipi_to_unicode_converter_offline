@echo off
rem Builds dist\AdarshaLipi-Unicode-Converter.exe
cd /d "%~dp0"
python -m pip install -r requirements.txt || exit /b 1
python test.py || exit /b 1

rem Nikosh is bundled only if you place Nikosh.ttf next to this file
set EXTRA=
if exist Nikosh.ttf set EXTRA=--add-data "Nikosh.ttf;."

python -m PyInstaller --noconfirm --onefile --windowed --name "AdarshaLipi-Unicode-Converter" ^
  --icon icon.ico --add-data "icon.ico;." --add-data "icon.png;." %EXTRA% app.py || exit /b 1
echo.
echo Built: dist\AdarshaLipi-Unicode-Converter.exe

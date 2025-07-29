@echo off
nuitka --onefile --windows-console-mode=disable --enable-plugins=pyside6 --windows-icon-from-ico=mohseni.ico --output-dir=dist --remove-output main.py -o MMImageOptimizer.exe
pause
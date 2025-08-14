@echo off
setlocal
set PY=python

%PY% compiler.py --target windows-x86_64
endlocal

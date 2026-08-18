@echo off
setlocal
cd /d "%~dp0.."

for %%P in (py python python3) do (
  where %%P >nul 2>nul && (
    %%P -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul && (
      %%P -m benchmeter.cli --web
      goto :done
    )
  )
)

echo benchmeter needs Python 3.9 or newer.
echo.
echo Install it from https://python.org/downloads and make sure you tick
echo "Add Python to PATH" during setup, then run this file again.
echo.
pause

:done
endlocal

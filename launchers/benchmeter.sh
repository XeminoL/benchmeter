#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
      exec "$candidate" -m benchmeter.cli --web
    fi
  fi
done

echo "benchmeter needs Python 3.9 or newer."
echo "Install it from https://python.org/downloads, then run this file again."
exit 1
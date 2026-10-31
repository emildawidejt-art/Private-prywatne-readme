"""Uruchomienie dla użytkownika — Python 3.11 lub nowszy."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import urllib.request
import venv
import webbrowser

root = Path(__file__).resolve().parent
os.chdir(root)
if sys.version_info < (3,11):
    sys.exit('Zainstaluj Python 3.11 lub nowszy ze strony https://www.python.org/downloads/')
python = root / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
print('Łowca Maszyn — przygotowanie do uruchomienia…', flush=True)
if not python.exists():
    venv.create(root / '.venv', with_pip=True)
digest = hashlib.sha256((root / 'requirements.txt').read_bytes()).hexdigest()
stamp = root / '.venv' / 'lowca-dependencies'
if not stamp.exists() or stamp.read_text() != digest:
    print('Pierwsze uruchomienie: pobieranie składników. Potrzebne jest połączenie z internetem.', flush=True)
    try:
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
    except subprocess.CalledProcessError:
        input('Nie udało się pobrać składników. Sprawdź internet. Naciśnij Enter, aby zamknąć.')
        sys.exit(1)
    stamp.write_text(digest)


def open_browser():
    for _ in range(40):
        try:
            urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=1)
            webbrowser.open('http://127.0.0.1:8000')
            return
        except Exception:
            time.sleep(.5)


threading.Thread(target=open_browser, daemon=True).start()
print('Adres aplikacji: http://127.0.0.1:8000\nPozostaw to okno otwarte. Zamknięcie okna zatrzyma aplikację.', flush=True)
try:
    subprocess.run([str(python), '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--workers', '1'])
except KeyboardInterrupt:
    print('\nZatrzymano Łowcę Maszyn.')

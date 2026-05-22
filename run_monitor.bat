@echo off
cd /d "C:\Users\Isaac.DESKTOP-PMB3RF0.000\Documents\tennis"
set PYTHONPATH=C:\Users\Isaac.DESKTOP-PMB3RF0.000\Documents\tennis
C:\Python314\python.exe src/main.py >> logs\monitor.log 2>&1
C:\Python314\python.exe generate_dashboard.py >> logs\monitor.log 2>&1
git fetch origin >> logs\monitor.log 2>&1
git checkout --theirs src/dashboard/data.js 2>nul
git checkout --theirs data/price_history.json 2>nul
git checkout --theirs data/ticketmaster_state.json 2>nul
git add -f data/price_history.json data/ticketmaster_state.json src/dashboard/data.js
git diff --cached --quiet || git commit -m "chore: price check local run [skip ci]" >> logs\monitor.log 2>&1
git push origin main >> logs\monitor.log 2>&1

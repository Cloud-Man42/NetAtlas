# NetAtlas

NetAtlas is a stripped-down Zyxel log viewer focused only on inbound WAN source IP activity.

This project:

- listens for syslog over UDP
- extracts the source IP and WAN interface from Zyxel-style syslog messages
- enriches public source IPs with GeoIP data
- stores WAN hits in SQLite
- exposes a small API for a map and list view
- renders the data with OpenStreetMap + Leaflet

## Project Layout

- `backend` - FastAPI API, UDP receiver, SQLite storage, GeoIP enrichment
- `frontend` - React + Vite dashboard for the NetAtlas map and source IP/country views

## Backend Setup

```powershell
cd C:\Users\hm\ip-source-map\backend
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

## Frontend Setup

```powershell
cd C:\Users\hm\ip-source-map\frontend
npm install
Copy-Item .env.example .env
```

## Start The App

Backend:

```powershell
cd C:\Users\hm\ip-source-map\backend
.\.venv\Scripts\python -m app.launcher
```

Frontend:

```powershell
cd C:\Users\hm\ip-source-map\frontend
npm run dev
```

The local launcher starts NetAtlas over `https://localhost:8443`.

On first run, NetAtlas creates a self-signed certificate in `backend\storage\tls` for local HTTPS. Your browser may show a local certificate warning until that certificate is trusted on your machine.

## Build The MSI

```powershell
cd C:\Users\hm\ip-source-map
powershell -ExecutionPolicy Bypass -File .\scripts\build-msi.ps1
```

The build produces `build\dist\NetAtlas-0.1.0.msi`. The installer packages a local NetAtlas launcher, the built frontend, and an empty `netatlas.db`.
It also installs `Installation Instructions.txt` and offers an exit-screen checkbox to open that file when setup finishes.

## Unit Tests

Run frontend unit tests:

```powershell
cd C:\Users\hm\ip-source-map\frontend
npm test
```

Run backend unit tests:

```powershell
cd C:\Users\hm\ip-source-map\backend
.\.venv\Scripts\python -m pytest
```

All new functionality should include unit tests, including negative cases for failure and invalid-input paths.

## Syslog Notes

By default the UDP receiver listens on `5140`.

Point your Zyxel device syslog target to:

- host: the machine running the backend
- port: `5140`
- protocol: UDP

Only messages identified as inbound WAN hits are stored. The default WAN interface keywords are `wan,internet,pppoe`.

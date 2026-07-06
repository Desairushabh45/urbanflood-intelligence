# 🌊 UrbanFlood Intelligence

> **AI-powered urban flood risk monitoring and early-warning dashboard for Hubballi city, Karnataka, India.**

UrbanFlood Intelligence is a full-stack web application that combines **real-time rainfall data**, **zone-based flood risk scoring**, and **Google Gemini AI** to help city authorities and residents understand and respond to flooding threats — before they happen.

---

## 📸 Screenshots

> The dashboard renders live on `http://localhost:8000/app/index.html` once the backend is running.

---

## 🏗️ Architecture

```
urbanflood-intelligence/
├── backend/                  # FastAPI Python backend
│   ├── main.py               # All API routes & AI integration
│   ├── zones.json            # Zone definitions (lat/lon + flood weights)
│   ├── requirements.txt      # Python dependencies
│   ├── apprunner.yaml        # AWS App Runner deployment config
│   └── .env.example          # Environment variable template
├── frontend/
│   └── index.html            # Single-page map dashboard (served by backend)
└── data/                     # (Reserved for datasets)
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 🗺️ **Live Risk Map** | Interactive map showing real-time flood risk per zone |
| 🌧️ **Rainfall Forecasting** | Pulls live hourly precipitation data from Open-Meteo API |
| 🔴 **Risk Scoring** | Per-zone risk score (Low / Medium / High) based on rainfall + flood weight |
| 📅 **3-Day Forecast** | Daily rainfall totals and projected risk for the next 3 days |
| 🤖 **Gemini AI Explanations** | Natural-language risk summaries and ranked action plans |
| 📷 **Photo Analysis** | Upload a site photo and get an AI-powered waterlogging assessment |
| 📋 **Citizen Reports** | Submit and view on-ground flood incident reports |
| 💬 **Q&A Assistant** | Ask natural-language questions about current zone risk |
| 🎛️ **Scenario Simulation** | Simulate arbitrary rainfall for any zone to model worst-case scenarios |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- A **Google Gemini API key** ([get one free](https://aistudio.google.com/app/apikey))

### 1. Clone the repository

```bash
git clone https://github.com/your-username/urbanflood-intelligence.git
cd urbanflood-intelligence
```

### 2. Set up the Python environment

```bash
cd backend
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS / Linux)
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `backend/.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

### 4. Run the server

```bash
# From the backend/ directory (with venv active)
uvicorn main:app --reload
```

The app will be available at:

- 🌐 **Dashboard** → `http://localhost:8000/app/index.html`
- 📖 **API Docs (Swagger)** → `http://localhost:8000/docs`

---

## 🌐 API Reference

All endpoints are served from the FastAPI backend.

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/rainfall` | Raw hourly precipitation for Hubballi |
| `GET` | `/risk-zones` | Current risk score for all zones |
| `GET` | `/risk-zones/forecast` | 3-day rainfall forecast per zone |
| `GET` | `/incidents` | Known historical flood incidents |

### AI-Powered Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/explain` | Gemini AI risk summary for High/Medium zones |
| `GET` | `/explain/ranked` | Priority-ranked action plan for city authorities |
| `GET` | `/ask?q=...` | Natural-language Q&A about current risk |
| `POST` | `/ask` | Same as above (JSON body: `{"q": "..."}`) |
| `POST` | `/analyze-photo` | Multipart upload — AI assessment of a site photo |

### Citizen Reporting

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/reports` | Submit a flood incident report |
| `GET` | `/reports` | List all submitted reports |

### Simulation Parameters

Append `?simulate_zone=<name>&simulate_mm=<value>` to `/risk-zones`, `/explain`, `/explain/ranked`, or `/ask` to override live rainfall for a zone.

**Example:**
```
GET /risk-zones?simulate_zone=Ganesh%20Nagar&simulate_mm=25
```

---

## 🏙️ Monitored Zones — Hubballi

| Zone | Lat | Lon | Flood Weight |
|------|-----|-----|-------------|
| Ganesh Nagar | 15.3480 | 75.1420 | 0.90 (Very High) |
| Old Hubballi | 15.3547 | 75.1367 | 0.85 (High) |
| Rayanal (HDB bypass) | 15.4050 | 75.1000 | 0.80 (High) |
| Unkal | 15.3850 | 75.1150 | 0.60 (Medium) |
| Vidyanagar | 15.3550 | 75.1250 | 0.50 (Medium) |
| Keshwapur | 15.3600 | 75.1300 | 0.50 (Medium) |

**Flood weight** reflects historical vulnerability — a zone with weight `0.9` reaches High risk at lower rainfall than a zone with weight `0.5`.

---

## 🤖 AI Integration

This project uses **Google Gemini 2.5 Flash** via the `google-genai` Python SDK for:

- **Risk explanations** — concise, zone-by-zone plain-English summaries
- **Ranked action plans** — priority-ordered response checklist for city staff
- **Photo assessment** — multimodal image analysis for waterlogging/drainage issues
- **Q&A assistant** — conversational flood risk advisor grounded in live data

---

## ☁️ Deployment (AWS App Runner)

The `backend/apprunner.yaml` is pre-configured for **AWS App Runner** (Python 3.11 runtime):

```yaml
version: 1.0
runtime: python311
build:
  commands:
    build:
      - pip install -r requirements.txt
run:
  command: uvicorn main:app --host 0.0.0.0 --port 8080
  network:
    port: 8080
```

Set `GEMINI_API_KEY` as an environment variable in your App Runner service configuration.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| AI | [Google Gemini 2.5 Flash](https://ai.google.dev/) via `google-genai` |
| Weather | [Open-Meteo API](https://open-meteo.com/) (free, no key required) |
| Frontend | Vanilla HTML/CSS/JS (served as static files by FastAPI) |
| HTTP client | [httpx](https://www.python-httpx.org/) (async) |
| Deployment | AWS App Runner |

---

## 📁 Data Sources

- **Rainfall / Forecast** — [Open-Meteo](https://open-meteo.com/en/docs) hourly precipitation forecast API (free, no API key required)
- **Flood risk zones** — Manually curated from HDMC (Hubballi-Dharwad Municipal Corporation) public incident records and 2024 monsoon reports
- **Historical incidents** — Sourced from news reports of 2024 Hubballi flood events

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push and open a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

- [Open-Meteo](https://open-meteo.com/) for the free weather forecast API
- [Google DeepMind](https://deepmind.google/) for the Gemini AI models
- HDMC and local Hubballi news sources for historical flood data

---

<p align="center">
  Built with ❤️ to help protect lives and property from urban flooding.
</p>

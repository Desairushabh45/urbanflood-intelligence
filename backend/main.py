from dotenv import load_dotenv
import os
import json
import asyncio
from datetime import datetime
import mimetypes
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")
_gemini_client = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HUBBALLI_LAT = 15.36
HUBBALLI_LON = 75.12

INCIDENTS = [
    {
        "name": "Ganesh Nagar",
        "lat": 15.3480,
        "lon": 75.1420,
        "date": "2024 monsoon season",
        "description": "Recurring severe flooding, poor drainage causing water to enter homes"
    },
    {
        "name": "Old Hubballi",
        "lat": 15.3547,
        "lon": 75.1367,
        "date": "2024 monsoon season",
        "description": "Rainwater seeping into houses during heavy rainfall"
    },
    {
        "name": "Rayanal underpass (HDB bypass)",
        "lat": 15.4050,
        "lon": 75.1000,
        "date": "2024",
        "description": "Underpass flooded, vehicle with 13 passengers got stuck"
    }
]

# In-memory prototype store. Reports reset whenever the server restarts.
citizen_reports = []
next_report_id = 1


def load_zones():
    with open(BASE_DIR / "zones.json") as f:
        return json.load(f)


def classify_risk(risk_score):
    if risk_score >= 0.5:
        return "High"
    if risk_score >= 0.25:
        return "Medium"
    return "Low"


def calculate_risk(rainfall_sum, flood_weight, max_possible):
    rain_factor = min(rainfall_sum / max_possible, 1.0)
    risk_score = round(rain_factor * flood_weight, 2)
    return risk_score, classify_risk(risk_score)


def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def parse_json_or_raw(text, raw_key):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {raw_key: text}


@app.get("/")
def root():
    return {"status": "UrbanFlood Intelligence API running"}


@app.get("/rainfall")
async def get_rainfall():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": HUBBALLI_LAT,
        "longitude": HUBBALLI_LON,
        "hourly": "precipitation",
        "forecast_days": 1
    }
    timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10.0)
    async with httpx.AsyncClient(timeout=timeout) as http_client:
        response = await http_client.get(url, params=params)
        return response.json()


async def fetch_zone_risk(http_client, zone, simulate_zone, simulate_mm):
    simulated = False
    if simulate_zone and zone["name"].lower() == simulate_zone.lower() and simulate_mm is not None:
        rainfall_sum = simulate_mm
        simulated = True
    else:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": zone["lat"],
            "longitude": zone["lon"],
            "hourly": "precipitation",
            "forecast_days": 1
        }
        try:
            response = await http_client.get(url, params=params)
            data = response.json()
            next_3hrs = data["hourly"]["precipitation"][:3]
            rainfall_sum = sum(next_3hrs)
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError):
            # Network hiccup for this zone only — don't crash the whole response.
            # Falls back to a safe "Low" reading so the demo keeps working.
            return {
                "zone": zone["name"],
                "lat": zone["lat"],
                "lon": zone["lon"],
                "rainfall_next_3hrs_mm": 0,
                "risk_score": 0,
                "risk_level": "Low",
                "simulated": False,
                "data_unavailable": True
            }

    risk_score, level = calculate_risk(rainfall_sum, zone["flood_weight"], 15)

    return {
        "zone": zone["name"],
        "lat": zone["lat"],
        "lon": zone["lon"],
        "rainfall_next_3hrs_mm": round(rainfall_sum, 2),
        "risk_score": risk_score,
        "risk_level": level,
        "simulated": simulated
    }


async def fetch_zone_forecast(http_client, zone):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": zone["lat"],
        "longitude": zone["lon"],
        "hourly": "precipitation",
        "forecast_days": 3
    }
    try:
        response = await http_client.get(url, params=params)
        data = response.json()
        times = data["hourly"]["time"]
        precipitation = data["hourly"]["precipitation"]
    except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError):
        return {
            "zone": zone["name"],
            "lat": zone["lat"],
            "lon": zone["lon"],
            "daily_forecast": [],
            "data_unavailable": True
        }

    daily_totals = {}
    for timestamp, rainfall in zip(times, precipitation):
        date = timestamp.split("T", 1)[0]
        daily_totals[date] = daily_totals.get(date, 0) + (rainfall or 0)

    daily_forecast = []
    for date, rainfall_sum in list(daily_totals.items())[:3]:
        risk_score, level = calculate_risk(rainfall_sum, zone["flood_weight"], 40)
        daily_forecast.append({
            "date": date,
            "rainfall_mm": round(rainfall_sum, 2),
            "risk_score": risk_score,
            "risk_level": level
        })

    return {
        "zone": zone["name"],
        "lat": zone["lat"],
        "lon": zone["lon"],
        "daily_forecast": daily_forecast
    }


@app.get("/risk-zones")
async def get_risk_zones(simulate_zone: str | None = None, simulate_mm: float | None = None):
    zones = load_zones()
    timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10.0)
    async with httpx.AsyncClient(timeout=timeout) as http_client:
        results = await asyncio.gather(
            *[fetch_zone_risk(http_client, zone, simulate_zone, simulate_mm) for zone in zones]
        )
    return list(results)


@app.get("/risk-zones/forecast")
async def get_risk_zones_forecast():
    zones = load_zones()
    timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10.0)
    async with httpx.AsyncClient(timeout=timeout) as http_client:
        results = await asyncio.gather(
            *[fetch_zone_forecast(http_client, zone) for zone in zones]
        )
    return list(results)


@app.get("/incidents")
async def get_incidents():
    return INCIDENTS


@app.get("/explain")
async def explain_risk(simulate_zone: str | None = None, simulate_mm: float | None = None):
    zones = await get_risk_zones(simulate_zone=simulate_zone, simulate_mm=simulate_mm)
    high_or_medium = [z for z in zones if z["risk_level"] in ("High", "Medium")]
    summary_data = high_or_medium if high_or_medium else zones

    prompt = f"""You are a flood risk advisor for Hubballi city authorities.
Given this zone risk data: {summary_data}
For each zone, write one short sentence explaining why it's at that risk level,
and one practical recommendation. Keep it concise and actionable."""

    try:
        response = get_gemini_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return {"explanation": response.text}
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
            return {
                "explanation": "API quota exceeded. Please try again later. Fallback analysis: " + 
                               "Based on current zone data, High and Medium risk areas require immediate drainage assessment and citizen notification.",
                "error": "API quota exceeded (free tier limit reached)",
                "zones_analyzed": len(summary_data)
            }
        else:
            return {
                "explanation": f"Error analyzing zones: {error_msg}",
                "error": str(type(e).__name__)
            }


@app.get("/explain/ranked")
async def explain_ranked(simulate_zone: str | None = None, simulate_mm: float | None = None):
    zones = await get_risk_zones(simulate_zone=simulate_zone, simulate_mm=simulate_mm)

    prompt = f"""You are an emergency response coordinator for Hubballi city.
Given this zone risk data: {zones}
Produce a numbered, priority-ranked action list (most urgent first) for city authorities to act on right now.
Each item must include one action and one short reason. Keep it to a maximum of 6 items.
Return only the numbered list with no introduction or closing note."""

    try:
        response = get_gemini_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return {"ranked_actions": response.text, "action_plan": response.text}
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
            fallback_actions = """1. Issue flood alert for High risk zones (Ganesh Nagar, Rayanal underpass) - water levels rising
2. Clear drainage systems in Medium risk areas - prevent waterlogging
3. Position rescue equipment near flood-prone zones - emergency preparedness
4. Notify residents in flood-prone areas - ensure evacuation routes ready
5. Increase monitoring frequency of weather forecasts - track rainfall trends
6. Set up emergency response centers - coordinate relief activities"""
            return {
                "ranked_actions": fallback_actions,
                "action_plan": fallback_actions,
                "error": "API quota exceeded (free tier limit reached)",
                "zones_analyzed": len(zones)
            }
        else:
            return {
                "ranked_actions": f"Error generating action plan: {error_msg}",
                "action_plan": f"Error generating action plan: {error_msg}",
                "error": str(type(e).__name__)
            }


@app.post("/analyze-photo")
async def analyze_photo(
    photo: UploadFile = File(...),
    zone_name: str | None = Form(None),
    notes: str | None = Form(None)
):
    image_bytes = await photo.read()
    detected_mime_type = (
        photo.content_type
        or mimetypes.guess_type(photo.filename or "")[0]
        or "image/jpeg"
    )

    text_prompt = f"""You are a flood-risk visual assessor for Hubballi city.
Assess this location photo for visible flood or waterlogging risk.
Look for standing water, blocked drains, low-lying terrain, visible damage, poor drainage, and access hazards.
Zone name: {zone_name or "not provided"}
Additional notes: {notes or "none"}
Return only valid JSON in this exact shape:
{{"visible_risk":"Low|Medium|High","observations":"...","recommendation":"..."}}"""

    try:
        response = get_gemini_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=detected_mime_type),
                text_prompt
            ]
        )
        assessment = parse_json_or_raw(response.text, "raw_assessment")
        return {
            "filename": photo.filename,
            "mime_type": detected_mime_type,
            **assessment
        }
    except Exception as exc:
        error_msg = str(exc)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
            return {
                "filename": photo.filename,
                "mime_type": detected_mime_type,
                "visible_risk": "Medium",
                "observations": "Photo analysis temporarily unavailable due to API quota limits",
                "recommendation": "Please try again later or contact system administrator",
                "error": "API quota exceeded"
            }
        else:
            return {
                "filename": photo.filename,
                "mime_type": detected_mime_type,
                "raw_assessment": f"Photo analysis unavailable: {exc}"
            }


@app.post("/reports")
async def create_report(request: Request):
    global next_report_id

    body = await request.json()
    try:
        lat = float(body.get("lat"))
        lon = float(body.get("lon"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="lat and lon are required numeric values")

    description = str(body.get("description", "")).strip()
    if not description:
        raise HTTPException(status_code=400, detail="description is required")

    report = {
        "id": next_report_id,
        "zone_name": str(body.get("zone_name", "")).strip(),
        "description": description,
        "lat": lat,
        "lon": lon,
        "timestamp": datetime.utcnow().isoformat()
    }
    next_report_id += 1
    citizen_reports.append(report)
    return report


@app.get("/reports")
async def get_reports():
    return sorted(citizen_reports, key=lambda report: report["timestamp"], reverse=True)


async def answer_question(question, simulate_zone=None, simulate_mm=None):
    if not question:
        return {"answer": "Ask a flood-risk question about Hubballi zones, rainfall, or city response actions."}

    zones = await get_risk_zones(simulate_zone=simulate_zone, simulate_mm=simulate_mm)
    prompt = f"""You are a flood risk assistant for Hubballi city.
Given this current zone risk data: {zones}
Answer this question from a city official or resident: {question}
Keep the answer concise, practical, and grounded in the provided risk data."""

    try:
        response = get_gemini_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return {"answer": response.text}
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
            return {
                "answer": "AI advisory service temporarily unavailable due to API quota limits. Based on current data: High risk zones need immediate attention for drainage assessment.",
                "error": "API quota exceeded",
                "zones_analyzed": len(zones)
            }
        else:
            return {"answer": f"Error processing question: {str(e)}", "error": str(type(e).__name__)}


@app.get("/ask")
async def ask_get(
    q: str | None = None,
    question: str | None = None,
    query: str | None = None,
    simulate_zone: str | None = None,
    simulate_mm: float | None = None
):
    return await answer_question(q or question or query, simulate_zone, simulate_mm)


@app.post("/ask")
async def ask_post(request: Request, simulate_zone: str | None = None, simulate_mm: float | None = None):
    try:
        body = await request.json()
    except json.JSONDecodeError:
        body = {}

    question = body.get("q") or body.get("question") or body.get("query")
    return await answer_question(question, simulate_zone, simulate_mm)


# Serves your map dashboard at http://127.0.0.1:8000/app/index.html
app.mount("/app", StaticFiles(directory=BASE_DIR.parent / "frontend", html=True), name="frontend")

"""Meteo — Open-Meteo (https://open-meteo.com/), gratuita e senza chiave,
verificata a mano prima di integrarla:
- geocoding: https://geocoding-api.open-meteo.com/v1/search?name=Milano
  → {"results": [{"latitude": ..., "longitude": ..., ...}]}
- previsioni (attuale + orarie + giornaliere in una sola chiamata):
  https://api.open-meteo.com/v1/forecast?latitude=...&longitude=...
    &current=temperature_2m,weather_code
    &hourly=temperature_2m,weather_code,precipitation_probability
    &daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max
    &forecast_days=3
  → {"current": {...}, "hourly": {"time": [...], ...}, "daily": {"time": ["2026-08-24", ...], ...}}
  (array paralleli — "daily.time" sono date, non date-ora, e il primo
  elemento è sempre oggi; verificato a mano).

"weather_code" è lo standard WMO (stessa codifica ovunque): mappato qui a
una breve descrizione in italiano (tabella ufficiale Open-Meteo)."""

from datetime import date, datetime, timedelta

import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CONDITIONS: dict[int, str] = {
    0: "Sereno",
    1: "Prevalentemente sereno",
    2: "Parzialmente nuvoloso",
    3: "Nuvoloso",
    45: "Nebbia",
    48: "Nebbia con brina",
    51: "Pioviggine leggera",
    53: "Pioviggine moderata",
    55: "Pioviggine intensa",
    56: "Pioviggine gelata leggera",
    57: "Pioviggine gelata intensa",
    61: "Pioggia leggera",
    63: "Pioggia moderata",
    65: "Pioggia intensa",
    66: "Pioggia gelata leggera",
    67: "Pioggia gelata intensa",
    71: "Neve leggera",
    73: "Neve moderata",
    75: "Neve intensa",
    77: "Granelli di neve",
    80: "Rovesci leggeri",
    81: "Rovesci moderati",
    82: "Rovesci violenti",
    85: "Rovesci di neve leggeri",
    86: "Rovesci di neve intensi",
    95: "Temporale",
    96: "Temporale con grandine leggera",
    99: "Temporale con grandine forte",
}

RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}
SNOW_CODES = {71, 73, 75, 77, 85, 86}

# Finestra "giornata attiva" in cui ha senso avvisare di pioggia/neve in
# arrivo (fuori da qui, es. di notte, l'avviso non serve a preparare nulla).
DAY_WINDOW_START_HOUR = 8
DAY_WINDOW_END_HOUR = 22


async def geocode_city(city: str) -> tuple[float, float] | None:
    """Coordinate di una città, una tantum (non cambiano: il chiamante mette
    in cache il risultato a lungo, vedi services/aggregator.py)."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            GEOCODING_URL, params={"name": city, "count": 1, "language": "it", "format": "json"}
        )
        response.raise_for_status()
        data = response.json()
    results = data.get("results")
    if not results:
        return None
    return results[0]["latitude"], results[0]["longitude"]


async def fetch_weather_snapshot(latitude: float, longitude: float) -> dict:
    """Meteo attuale + previsioni orarie + giornaliere (oggi e i 2 giorni
    successivi), in un'unica chiamata. Ritorna dati grezzi (dict);
    services/aggregator.py li elabora in HourlyForecast/DailyForecast/
    l'avviso pioggia-neve, per tenere questo adapter semplice e senza
    logica di dominio."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,weather_code",
                "hourly": "temperature_2m,weather_code,precipitation_probability",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": 3,
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        return response.json()


def condition_label(code: int | None) -> str | None:
    return WMO_CONDITIONS.get(code) if code is not None else None


def parse_hourly(raw: dict, now: datetime, count: int) -> list[dict]:
    """Le prossime `count` ore da adesso in poi (ora corrente inclusa se non
    ancora passata), come lista di dict pronti per HourlyForecast."""
    hourly = raw.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    codes = hourly.get("weather_code", [])
    probs = hourly.get("precipitation_probability", [])

    result = []
    for i, time_str in enumerate(times):
        hour_dt = datetime.fromisoformat(time_str)
        if hour_dt < now.replace(minute=0, second=0, microsecond=0):
            continue
        result.append(
            {
                "time": hour_dt,
                "temperature_c": temps[i] if i < len(temps) else None,
                "condition": condition_label(codes[i] if i < len(codes) else None),
                "precipitation_probability": probs[i] if i < len(probs) else None,
            }
        )
        if len(result) >= count:
            break
    return result


def parse_daily(raw: dict, today: date, count: int) -> list[dict]:
    """I prossimi `count` giorni DA DOMANI in poi (oggi è già coperto dalla
    card principale + dalle prossime ore, qui evitiamo di ripeterlo) come
    lista di dict pronti per DailyForecast. "daily.time" sono date pure
    (YYYY-MM-DD), non date-ora."""
    daily = raw.get("daily", {})
    dates = daily.get("time", [])
    codes = daily.get("weather_code", [])
    temps_max = daily.get("temperature_2m_max", [])
    temps_min = daily.get("temperature_2m_min", [])
    probs_max = daily.get("precipitation_probability_max", [])

    result = []
    for i, date_str in enumerate(dates):
        day = date.fromisoformat(date_str)
        if day <= today:
            continue
        result.append(
            {
                "date": day,
                "condition": condition_label(codes[i] if i < len(codes) else None),
                "temperature_min": temps_min[i] if i < len(temps_min) else None,
                "temperature_max": temps_max[i] if i < len(temps_max) else None,
                "precipitation_probability_max": probs_max[i] if i < len(probs_max) else None,
            }
        )
        if len(result) >= count:
            break
    return result


def precipitation_alert(raw: dict, now: datetime, current_code: int | None) -> str | None:
    """Se non sta già piovendo/nevicando adesso, ma pioggia o neve sono
    previste più tardi oggi (tra le DAY_WINDOW_START_HOUR e le
    DAY_WINDOW_END_HOUR), un breve avviso da mostrare in Home."""
    if current_code in RAIN_CODES or current_code in SNOW_CODES:
        return None

    hourly = raw.get("hourly", {})
    times = hourly.get("time", [])
    codes = hourly.get("weather_code", [])
    today = now.date()

    will_rain = False
    will_snow = False
    for i, time_str in enumerate(times):
        hour_dt = datetime.fromisoformat(time_str)
        if hour_dt.date() != today or hour_dt < now:
            continue
        if not (DAY_WINDOW_START_HOUR <= hour_dt.hour <= DAY_WINDOW_END_HOUR):
            continue
        code = codes[i] if i < len(codes) else None
        if code in SNOW_CODES:
            will_snow = True
        elif code in RAIN_CODES:
            will_rain = True

    if will_snow:
        return "Possibile neve più tardi"
    if will_rain:
        return "Possibile pioggia più tardi"
    return None

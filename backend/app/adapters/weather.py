"""Meteo — Open-Meteo (https://open-meteo.com/), gratuita e senza chiave,
verificata a mano prima di integrarla:
- geocoding: https://geocoding-api.open-meteo.com/v1/search?name=Milano
  → {"results": [{"latitude": ..., "longitude": ..., ...}]}
- previsioni: https://api.open-meteo.com/v1/forecast?latitude=...&longitude=...&current=temperature_2m,weather_code
  → {"current": {"temperature_2m": 29.2, "weather_code": 3}}

"weather_code" è lo standard WMO (stessa codifica ovunque): mappato qui a
una breve descrizione in italiano (tabella ufficiale Open-Meteo)."""

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


async def fetch_current_weather(latitude: float, longitude: float) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,weather_code",
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        data = response.json()
    current = data.get("current", {})
    code = current.get("weather_code")
    return {
        "temperature_c": current.get("temperature_2m"),
        "condition": WMO_CONDITIONS.get(code),
    }

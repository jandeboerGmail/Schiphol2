"""Small client for the Schiphol Public Flight API."""

import hashlib
import json

import requests
from django.conf import settings
from django.core.cache import cache

from .normalize import normalize_flights

BASE_URL = "https://api.schiphol.nl/public-flights/flights"
DIRECTIONS = {"departures": "D", "arrivals": "A"}


class SchipholConfigError(Exception):
    """app_id / app_key are not configured."""


class SchipholAPIError(Exception):
    """The API could not be reached or returned an error."""


def fetch_flights(direction, page=0, schedule_date=None, airline=None, destination=None):
    """Return {"flights": [...], "has_next": bool} for one page of results.

    direction: "departures" or "arrivals"
    schedule_date: "YYYY-MM-DD" (defaults to today on Schiphol's side)
    airline: IATA airline code, e.g. "KL"
    destination: IATA airport code, e.g. "LHR"
    """
    if not settings.SCHIPHOL_APP_ID or not settings.SCHIPHOL_APP_KEY:
        raise SchipholConfigError("SCHIPHOL_APP_ID / SCHIPHOL_APP_KEY are not set.")

    params = {
        "flightDirection": DIRECTIONS[direction],
        "includedelays": "false",
        "page": page,
        "sort": "+scheduleTime",
    }
    if schedule_date:
        params["scheduleDate"] = schedule_date
    if airline:
        params["airline"] = airline
    if destination:
        params["route"] = destination

    key_source = json.dumps(params, sort_keys=True)
    cache_key = "schiphol:" + hashlib.sha1(key_source.encode()).hexdigest()
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            BASE_URL,
            params=params,
            headers={
                "Accept": "application/json",
                "app_id": settings.SCHIPHOL_APP_ID,
                "app_key": settings.SCHIPHOL_APP_KEY,
                "ResourceVersion": "v4",
            },
            timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise SchipholAPIError(str(exc)) from exc

    result = {
        "flights": normalize_flights(payload.get("flights")),
        # The API paginates with a Link header; rel="next" means more pages exist.
        "has_next": 'rel="next"' in resp.headers.get("Link", ""),
    }
    cache.set(cache_key, result, settings.SCHIPHOL_CACHE_SECONDS)
    return result

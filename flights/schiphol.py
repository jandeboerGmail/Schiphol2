"""Client for the Schiphol Public Flight API using OAuth 2.0 client credentials.

Flow (per developer.schiphol.nl):
  1. POST client_id / client_secret / audience to the token endpoint.
  2. Receive a bearer token valid for ~30 minutes (expires_in = 1800).
  3. Send it as "Authorization: Bearer <token>" and cache it until shortly before it expires.
"""

import hashlib
import json

import requests
from django.conf import settings
from django.core.cache import cache

from .normalize import normalize_flights

DIRECTIONS = {"departures": "D", "arrivals": "A"}
TOKEN_CACHE_KEY = "schiphol:oauth:token"
TOKEN_EXPIRY_MARGIN = 60  # refresh a minute early
REQUEST_TIMEOUT = 10


class SchipholConfigError(Exception):
    """client_id / client_secret are not configured."""


class SchipholAPIError(Exception):
    """The API or the token endpoint could not be reached or returned an error."""


def _request_new_token():
    """Fetch a token from the OAuth endpoint and cache it. Returns the token string."""
    try:
        resp = requests.post(
            settings.SCHIPHOL_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.SCHIPHOL_CLIENT_ID,
                "client_secret": settings.SCHIPHOL_CLIENT_SECRET,
                "audience": settings.SCHIPHOL_AUDIENCE,
            },
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
        token = payload["access_token"]
        expires_in = int(payload.get("expires_in", 1800))
    except (requests.RequestException, ValueError, KeyError) as exc:
        # Don't include the response body or request data: it may echo credentials.
        raise SchipholAPIError(f"Token request failed: {type(exc).__name__}") from exc

    cache.set(TOKEN_CACHE_KEY, token, max(expires_in - TOKEN_EXPIRY_MARGIN, 1))
    print('Token:',token)
    return token


def get_access_token(force_refresh=False):
    if not settings.SCHIPHOL_CLIENT_ID or not settings.SCHIPHOL_CLIENT_SECRET:
        raise SchipholConfigError("SCHIPHOL_CLIENT_ID / SCHIPHOL_CLIENT_SECRET are not set.")
    if not force_refresh:
        token = cache.get(TOKEN_CACHE_KEY)
        if token:
            return token
    return _request_new_token()


def _get_flights(params):
    """GET the flights endpoint; on a 401 refresh the token once and retry."""
    for attempt in (1, 2):
        token = get_access_token(force_refresh=(attempt == 2))
        try:
            resp = requests.get(
                settings.SCHIPHOL_FLIGHTS_URL,
                params=params,
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise SchipholAPIError(f"Flights request failed: {type(exc).__name__}") from exc
        if resp.status_code == 401 and attempt == 1:
            cache.delete(TOKEN_CACHE_KEY)
            continue
        try:
            resp.raise_for_status()
            return resp, resp.json()
        except (requests.RequestException, ValueError) as exc:
            raise SchipholAPIError(f"Flights request failed: {type(exc).__name__}") from exc
    raise SchipholAPIError("Flights request failed: unauthorized")


def fetch_flights(direction, page=0, schedule_date=None, airline=None, destination=None):
    """Return {"flights": [...], "has_next": bool} for one page of results.

    direction: "departures" or "arrivals"
    schedule_date: "YYYY-MM-DD" (defaults to today on Schiphol's side)
    airline: IATA airline code, e.g. "KL"
    destination: IATA airport code, e.g. "LHR"
    """
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
    cache_key = "schiphol:flights:" + hashlib.sha1(key_source.encode()).hexdigest()
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    resp, payload = _get_flights(params)

    result = {
        "flights": normalize_flights(payload.get("flights")),
        # The API paginates with a Link header; rel="next" means more pages exist.
        "has_next": 'rel="next"' in resp.headers.get("Link", ""),
    }
    cache.set(cache_key, result, settings.SCHIPHOL_CACHE_SECONDS)
    return result

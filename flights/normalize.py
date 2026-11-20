"""Turn raw Schiphol API flight records into flat dicts for templates and JSON.

Kept free of Django imports so it can be tested on its own.
Field names follow the Schiphol Public Flight API (v4) as I know it; if the API
changes, this is the only place that needs updating.
"""

from datetime import datetime

# Flight state codes -> readable text (from the Schiphol API documentation).
STATE_LABELS = {
    "SCH": "Scheduled",
    "DEL": "Delayed",
    "WIL": "Wait in lounge",
    "GTO": "Gate opened",
    "BRD": "Boarding",
    "GCL": "Gate closing",
    "GTD": "Gate closed",
    "DEP": "Departed",
    "CNX": "Cancelled",
    "GCH": "Gate changed",
    "TOM": "Tomorrow",
    "ARR": "Arrived",
    "LND": "Landed",
    "FIR": "In Dutch airspace",
    "EXP": "Expected",
}


def _hhmm(value):
    """'2026-11-18T14:35:00.000+01:00' or '14:35:00' -> '14:35'. None if unparseable."""
    if not value:
        return None
    if "T" in value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%H:%M")
        except ValueError:
            return value[11:16] or None
    return value[:5] or None


def normalize_flight(raw):
    states = (raw.get("publicFlightState") or {}).get("flightStates") or []
    scheduled = _hhmm(raw.get("scheduleDateTime")) or _hhmm(raw.get("scheduleTime"))
    expected = _hhmm(raw.get("expectedTimeBoarding")) or _hhmm(raw.get("estimatedLandingTime"))
    actual = _hhmm(raw.get("actualOffBlockTime")) or _hhmm(raw.get("actualLandingTime"))
    destinations = (raw.get("route") or {}).get("destinations") or []
    codeshares = (raw.get("codeshares") or {}).get("codeshares") or []
    belts = (raw.get("baggageClaim") or {}).get("belts") or []
    belt = belts[0] if belts else None

    return {
        "id": raw.get("id"),
        "flight": raw.get("flightName") or "",
        "codeshares": codeshares,
        "airline": raw.get("prefixIATA") or "",
        "scheduled": scheduled,
        "expected": expected if expected and expected != scheduled else None,
        "actual": actual,
        "direction": raw.get("flightDirection"),
        "airports": destinations,
        "final_airport": destinations[-1] if destinations else "",
        "gate": raw.get("gate") or "",
        "terminal": raw.get("terminal"),
        "belt": belt,
        "state_codes": states,
        "status": ", ".join(STATE_LABELS.get(s, s) for s in states) or "—",
        "cancelled": "CNX" in states,
        "delayed": "DEL" in states,
    }


def normalize_flights(raw_flights):
    return [normalize_flight(f) for f in raw_flights or []]

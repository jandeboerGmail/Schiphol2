import re
from datetime import date

from django.http import Http404, JsonResponse
from django.shortcuts import render

from .schiphol import DIRECTIONS, SchipholAPIError, SchipholConfigError, fetch_flights

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
AIRLINE_RE = re.compile(r"^[A-Za-z0-9]{2,3}$")
AIRPORT_RE = re.compile(r"^[A-Za-z]{3}$")


def _parse_filters(request):
    """Validate query-string filters; invalid values are ignored rather than forwarded."""
    try:
        page = max(0, int(request.GET.get("page", 0)))
    except ValueError:
        page = 0

    schedule_date = request.GET.get("date", "").strip()
    if schedule_date:
        try:
            date.fromisoformat(schedule_date)
        except ValueError:
            schedule_date = ""
        if not DATE_RE.match(schedule_date):
            schedule_date = ""

    airline = request.GET.get("airline", "").strip().upper()
    if not AIRLINE_RE.match(airline):
        airline = ""

    destination = request.GET.get("airport", "").strip().upper()
    if not AIRPORT_RE.match(destination):
        destination = ""

    return {
        "page": page,
        "schedule_date": schedule_date or None,
        "airline": airline or None,
        "destination": destination or None,
    }


def _load(direction, filters):
    """Return (data, error_message). Never raises for expected failures."""
    try:
        return fetch_flights(direction, **filters), None
    except SchipholConfigError:
        return {"flights": [], "has_next": False}, (
            "Set SCHIPHOL_APP_ID and SCHIPHOL_APP_KEY (see README) to load live flights."
        )
    except SchipholAPIError:
        return {"flights": [], "has_next": False}, (
            "Could not load flights from the Schiphol API. Try again in a moment."
        )


def board(request, direction):
    if direction not in DIRECTIONS:
        raise Http404
    filters = _parse_filters(request)
    data, error = _load(direction, filters)
    return render(
        request,
        "flights/board.html",
        {
            "direction": direction,
            "flights": data["flights"],
            "has_next": data["has_next"],
            "error": error,
            "page": filters["page"],
            "prev_page": filters["page"] - 1 if filters["page"] > 0 else None,
            "next_page": filters["page"] + 1,
            "values": {
                "date": filters["schedule_date"] or "",
                "airline": filters["airline"] or "",
                "airport": filters["destination"] or "",
            },
        },
    )


def board_json(request, direction):
    if direction not in DIRECTIONS:
        raise Http404
    filters = _parse_filters(request)
    data, error = _load(direction, filters)
    status = 200 if error is None else (503 if "Could not" in error else 500)
    return JsonResponse(
        {"flights": data["flights"], "has_next": data["has_next"], "error": error},
        status=status,
    )

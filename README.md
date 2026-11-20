# Schiphol flight board (Django)
# Apluication against Schiphol API v4 with OATH validation 


A small Django app that shows live Schiphol departures and arrivals using the
[Schiphol Public Flight API](https://developer.schiphol.nl).

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export SCHIPHOL_APP_ID=your_app_id
export SCHIPHOL_APP_KEY=your_app_key

python manage.py runserver
```

Open http://127.0.0.1:8000/ (redirects to departures).

No database is used, so there are no migrations to run.

## URLs

| URL | What |
|---|---|
| `/departures/` | HTML board of departures |
| `/arrivals/` | HTML board of arrivals |
| `/api/departures/`, `/api/arrivals/` | Same data as JSON |

Query parameters on all of them: `page` (0-based), `date` (`YYYY-MM-DD`),
`airline` (IATA code, e.g. `KL`), `airport` (IATA code, e.g. `LHR`).

Example: `/departures/?airline=KL&airport=LHR&date=2026-11-19`

## How it works

- `flights/schiphol.py` calls the API and caches each distinct query for 60 s
  (`SCHIPHOL_CACHE_SECONDS`) so page loads and the auto-refresh don't burn your rate limit.
- `flights/normalize.py` turns the raw API records into flat dicts. If the API's
  field names change, this is the only file to touch.
- `flights/views.py` validates query parameters before passing them on.
- The board page re-fetches the JSON endpoint every 60 s and updates the table in place.

## Tests

```bash
python -m unittest flights.tests.test_normalize
```

These cover the normalizer and need neither Django nor network access.

## Before you rely on it

The API field names, the `ResourceVersion: v4` header, the `airline` / `route`
filter parameters and the `Link` header pagination are written from memory of the
API. Check them against the current documentation on the developer portal and
adjust `schiphol.py` / `normalize.py` if anything differs.

For production, set `DJANGO_DEBUG=0`, a real `DJANGO_SECRET_KEY`, and
`DJANGO_ALLOWED_HOSTS`, and use a shared cache (Redis/Memcached) instead of the
default per-process one.

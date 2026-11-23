"""Running queries against the flight database."""

import math
import re
from datetime import datetime


RECORD_KEYS = {
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price"
}

ALLOWED_KEYS = RECORD_KEYS | {
    "min_price",
    "sort_by",
    "order",
    "limit"
}

DATETIME_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}"
)


def _valid_datetime(value: str) -> bool:
    """Check that a datetime has the exact required format."""

    if not DATETIME_PATTERN.fullmatch(value):
        return False

    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False


def _valid_number(value) -> bool:
    """Check whether a value is a finite number, excluding booleans."""

    if isinstance(value, bool):
        return False

    if not isinstance(value, (int, float)):
        return False

    return math.isfinite(value)


def _validate_query(query: dict) -> bool:
    """Check whether all query keys and values are valid."""

    if not isinstance(query, dict):
        return False

    for key, value in query.items():

        if key not in ALLOWED_KEYS:
            return False

        if key in ("flight_id", "origin", "destination"):
            if not isinstance(value, str):
                return False

        elif key in ("departure_datetime", "arrival_datetime"):
            if not isinstance(value, str):
                return False

            if not _valid_datetime(value):
                return False

        elif key in ("price", "min_price"):
            if not _valid_number(value):
                return False

        elif key == "sort_by":
            if not isinstance(value, str):
                return False

            if value not in RECORD_KEYS:
                return False

        elif key == "order":
            if value not in ("asc", "desc"):
                return False

        elif key == "limit":
            if type(value) is not int:
                return False

            if value < 0:
                return False

    if "order" in query and "sort_by" not in query:
        return False

    return True


def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for one query object.

    Valid query:   {"query": query, "matches": [...]}
    Invalid query: {"query": query, "error": "INVALID_QUERY", "matches": []}
    """

    if not _validate_query(query):
        return {
            "query": query,
            "error": "INVALID_QUERY",
            "matches": []
        }

    matches = []

    for flight in db:

        # Exact match filters
        if "flight_id" in query:
            if flight["flight_id"] != query["flight_id"]:
                continue

        if "origin" in query:
            if flight["origin"] != query["origin"]:
                continue

        if "destination" in query:
            if flight["destination"] != query["destination"]:
                continue

        # Departure must be at or after the requested time
        if "departure_datetime" in query:
            if flight["departure_datetime"] < query["departure_datetime"]:
                continue

        # Arrival must be at or before the requested time
        if "arrival_datetime" in query:
            if flight["arrival_datetime"] > query["arrival_datetime"]:
                continue

        # Maximum price filter
        if "price" in query:
            if flight["price"] > query["price"]:
                continue

        # Minimum price filter
        if "min_price" in query:
            if flight["price"] < query["min_price"]:
                continue

        matches.append(flight)

    # Sort results when requested
    if "sort_by" in query:
        sort_key = query["sort_by"]
        reverse_order = query.get("order", "asc") == "desc"

        matches = sorted(
            matches,
            key=lambda flight: flight[sort_key],
            reverse=reverse_order
        )

    # Apply the result limit after sorting
    if "limit" in query:
        matches = matches[:query["limit"]]

    return {
        "query": query,
        "matches": matches
    }


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept one query object or a list of them; always return a list."""

    if isinstance(queries, dict):
        queries = [queries]

    results = []

    for query in queries:
        result = run_query(db, query)
        results.append(result)

    return results

"""Row validation: airport list loading, single-row checks, record building."""

import math
import re
from datetime import datetime


FLIGHT_ID_PATTERN = re.compile(r"[A-Za-z0-9]{2,8}")
AIRPORT_PATTERN = re.compile(r"[A-Z]{3}")
DATETIME_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}"
)


def _parse_datetime(value: str) -> datetime | None:
    """Parse a datetime only if it follows the exact required format."""

    if not DATETIME_PATTERN.fullmatch(value):
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def load_airports(path: str) -> set[str]:
    """Read an airport list file and return the set of codes.

    One code per line. Strip whitespace; skip blank lines and lines
    starting with '#'.
    """

    airports = set()

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            code = line.strip()

            if not code:
                continue

            if code.startswith("#"):
                continue

            airports.add(code)

    return airports


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Check one CSV row (fields as returned by csv.reader, not yet stripped).

    Return None if the row is valid, otherwise the error code of the
    FIRST failing check (checks 1-11 in the specification, in order).
    Does not check for duplicates.
    """

    # Check 1: Number of fields
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"

    values = [field.strip() for field in fields]

    # Check 2: Missing fields
    if any(not value for value in values):
        return "MISSING_FIELD"

    flight_id, origin, destination, departure, arrival, price = values

    # Check 3: Flight ID
    if not FLIGHT_ID_PATTERN.fullmatch(flight_id):
        return "INVALID_FLIGHT_ID"

    # Check 4: Origin airport
    if not AIRPORT_PATTERN.fullmatch(origin):
        return "INVALID_ORIGIN"

    if origin not in airports:
        return "INVALID_ORIGIN"

    # Check 5: Destination airport
    if not AIRPORT_PATTERN.fullmatch(destination):
        return "INVALID_DESTINATION"

    if destination not in airports:
        return "INVALID_DESTINATION"

    # Check 6: Same origin and destination
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    # Check 7: Departure datetime
    departure_time = _parse_datetime(departure)

    if departure_time is None:
        return "INVALID_DEPARTURE"

    # Check 8: Arrival datetime
    arrival_time = _parse_datetime(arrival)

    if arrival_time is None:
        return "INVALID_ARRIVAL"

    # Check 9: Arrival must be after departure
    if arrival_time <= departure_time:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    # Check 10: Price must be a finite number
    try:
        numeric_price = float(price)
    except (ValueError, OverflowError):
        return "INVALID_PRICE"

    if not math.isfinite(numeric_price):
        return "INVALID_PRICE"

    # Check 11: Price must be positive
    if numeric_price <= 0:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    """Turn a valid row into a flight record dictionary.

    Keys: flight_id, origin, destination, departure_datetime,
    arrival_datetime (stripped strings) and price (float).
    """

    values = [field.strip() for field in fields]

    record = {
        "flight_id": values[0],
        "origin": values[1],
        "destination": values[2],
        "departure_datetime": values[3],
        "arrival_datetime": values[4],
        "price": float(values[5])
    }

    return record

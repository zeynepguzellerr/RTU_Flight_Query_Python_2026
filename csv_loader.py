"""Reading CSV files into flight records and error messages."""

import csv
import os

from validator import validate_row, to_record


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Process the CSV files in the order given.

    Return (records, errors):
      records - valid flight records, in input order
      errors  - one message per invalid row, in input order, formatted as
                "<file name>:<line number>: <ERROR_CODE> | <free text>"
                (base file name only, no timestamp or level, no newline)

    Also performs the DUPLICATE_FLIGHT check across all the files.
    Does not write any files and does not log anything itself.
    """

    records = []
    errors = []
    seen_flights = set()

    for path in paths:
        filename = os.path.basename(path)

        with open(path, "r", encoding="utf-8", newline="") as file:

            for line_number, raw_line in enumerate(file, start=1):

                # Skip the CSV header
                if line_number == 1:
                    continue

                # Skip blank lines
                if not raw_line.strip():
                    continue

                # Skip comment lines
                if raw_line.lstrip().startswith("#"):
                    continue

                original_line = raw_line.rstrip("\r\n")

                # Parse the CSV row
                try:
                    fields = next(csv.reader([raw_line], strict=True), [])
                    error_code = validate_row(fields, airports)

                except csv.Error:
                    error_code = "WRONG_FIELD_COUNT"
                    fields = []

                # Process valid rows
                if error_code is None:
                    record = to_record(fields)

                    flight_key = (
                        record["flight_id"],
                        record["departure_datetime"]
                    )

                    # Check duplicates across all input files
                    if flight_key in seen_flights:
                        error_code = "DUPLICATE_FLIGHT"

                    else:
                        seen_flights.add(flight_key)
                        records.append(record)

                # Store invalid row information
                if error_code is not None:
                    error_message = (
                        f"{filename}:{line_number}: "
                        f"{error_code} | {original_line}"
                    )

                    errors.append(error_message)

    return records, errors

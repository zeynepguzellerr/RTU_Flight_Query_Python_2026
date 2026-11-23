"""Flight Schedule Parser and Query Tool - command-line entry point.

Run from the project folder, for example:
    python flight_parser.py -i data/db.csv -a data/airports.txt
"""

import argparse
import json
import logging
import sys

from datetime import datetime
from pathlib import Path

from validator import load_airports
from csv_loader import parse_files
from query import run_queries


# TODO: fill in your details: plain ASCII, no spaces or underscores.
STUDENT_ID = "231ADB274"
FIRST_NAME = "Zeynep"
LAST_NAME = "HaticeGuzeller"


def _reject_json_constant(value: str):
    """Reject non-standard JSON constants such as NaN and Infinity."""
    raise ValueError(f"Invalid JSON constant: {value}")


def _load_json(path: str):
    """Load a JSON file using strict JSON constant validation."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file, parse_constant=_reject_json_constant)


def main(argv: list[str] | None = None) -> int:
    """Run the whole program and return the exit code (0, 1 or 2).

    argv is the argument list without the program name.
    None means use sys.argv[1:] (argparse does this for you).
    Do not call sys.exit() inside main(); return the code instead.
    """

    # Configure command-line arguments
    parser = argparse.ArgumentParser(
        description="Flight Schedule Parser and Query Tool"
    )

    sources = parser.add_mutually_exclusive_group(required=True)

    sources.add_argument(
        "-i",
        dest="csv_file",
        metavar="FILE",
        help="Parse a single CSV file"
    )

    sources.add_argument(
        "-d",
        dest="csv_directory",
        metavar="FOLDER",
        help="Parse all CSV files in a folder"
    )

    sources.add_argument(
        "-j",
        dest="json_database",
        metavar="FILE",
        help="Load an existing JSON database"
    )

    parser.add_argument(
        "-a",
        dest="airports",
        metavar="FILE",
        help="Airport list file"
    )

    parser.add_argument(
        "-o",
        dest="output",
        metavar="FILE",
        help="Output JSON database path"
    )

    parser.add_argument(
        "-q",
        dest="queries",
        metavar="FILE",
        help="JSON query file"
    )

    parser.add_argument(
        "-r",
        dest="response_folder",
        metavar="FOLDER",
        default=".",
        help="Folder for query response files"
    )

    # Validate command-line argument combinations
    try:
        args = parser.parse_args(argv)

        using_csv = (
            args.csv_file is not None
            or args.csv_directory is not None
        )

        if using_csv and args.airports is None:
            parser.error("-a is required with -i or -d")

        if args.json_database is not None and args.output is not None:
            parser.error("-o cannot be used with -j")

    except SystemExit as error:
        return int(error.code)

    # Prepare logging
    logger = logging.getLogger("flight_parser")
    logger.setLevel(logging.INFO)

    handler = None

    try:
        # Load an existing JSON database
        if args.json_database is not None:

            db = _load_json(args.json_database)

            if not isinstance(db, list):
                raise ValueError(
                    "JSON database must be an array of objects"
                )

            if not all(isinstance(record, dict) for record in db):
                raise ValueError(
                    "JSON database must contain only objects"
                )

        # Parse CSV input files
        else:

            output_path = Path(
                args.output if args.output is not None else "db.json"
            )

            log_path = output_path.parent / "errors.log"

            # Configure the file logger
            handler = logging.FileHandler(
                log_path,
                mode="w",
                encoding="utf-8"
            )

            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            )

            logger.addHandler(handler)

            # Load valid airport codes
            airports = load_airports(args.airports)

            # Select the CSV files
            if args.csv_file is not None:

                paths = [args.csv_file]

            else:

                directory = Path(args.csv_directory)

                if not directory.is_dir():
                    raise FileNotFoundError(
                        f"Directory not found: {directory}"
                    )

                paths = [
                    str(path)
                    for path in sorted(
                        directory.iterdir(),
                        key=lambda item: item.name
                    )
                    if path.is_file()
                    and path.name.endswith(".csv")
                ]

                if not paths:
                    raise FileNotFoundError(
                        f"No CSV files found in: {directory}"
                    )

            # Validate and parse the CSV files
            db, errors = parse_files(paths, airports)

            # Write validation errors using the logging module
            for error_message in errors:
                logger.warning(error_message)

            # Save valid flight records
            with open(output_path, "w", encoding="utf-8") as file:
                json.dump(
                    db,
                    file,
                    indent=2,
                    ensure_ascii=False,
                    allow_nan=False
                )

        # Process queries when a query file is supplied
        if args.queries is not None:

            queries = _load_json(args.queries)

            if isinstance(queries, dict):
                pass

            elif isinstance(queries, list):
                if not all(isinstance(query, dict) for query in queries):
                    raise ValueError(
                        "Query array must contain only objects"
                    )

            else:
                raise ValueError(
                    "Query file must contain an object or an array of objects"
                )

            # Execute queries
            responses = run_queries(db, queries)

            # Generate the response filename using local time
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")

            response_filename = (
                f"response_{STUDENT_ID}_{FIRST_NAME}_"
                f"{LAST_NAME}_{timestamp}.json"
            )

            response_path = (
                Path(args.response_folder) / response_filename
            )

            # Save query responses
            with open(response_path, "w", encoding="utf-8") as file:
                json.dump(
                    responses,
                    file,
                    indent=2,
                    ensure_ascii=False,
                    allow_nan=False
                )

        return 0

    # Handle expected runtime problems without tracebacks
    except (OSError, ValueError, UnicodeError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    finally:
        # Always remove and close the logging handler
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    sys.exit(main())

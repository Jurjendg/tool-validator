from pathlib import Path

from toolvalidator.runner import run_validation

# Edit these values for each validation run.
XML_DIR = Path("xml-files")
OUT_DB = Path("out/toolvalidator.sqlite")
ADVIESTOOL_BASE_URL = "http://localhost:5000"

# File selection.
PATTERN = "*.xml"
LIMIT: int | None = None  # Set to None to process all matching files.

# Runtime options.
API_TIMEOUT_SECONDS = 60.0
HASH_FILES = False
NOTES: str | None = None


def main() -> None:
    run_id = run_validation(
        xml_dir=XML_DIR,
        out_db=OUT_DB,
        base_url=ADVIESTOOL_BASE_URL,
        pattern=PATTERN,
        limit=LIMIT,
        notes=NOTES,
        timeout=API_TIMEOUT_SECONDS,
        hash_files=HASH_FILES,
    )
    if run_id is None:
        print(f"No non-apartment XML files or extraction errors found; no run written to {OUT_DB}")
    else:
        print(f"Run {run_id} written to {OUT_DB}")


if __name__ == "__main__":
    main()

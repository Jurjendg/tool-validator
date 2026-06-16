from __future__ import annotations

import argparse
import hashlib
import sys
import warnings
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
XML_CONVERTER_SRC = ROOT / "xmlConverter" / "src"
if str(XML_CONVERTER_SRC) not in sys.path:
    sys.path.insert(0, str(XML_CONVERTER_SRC))

from xml_converter.extract.api_builder import build_api_input
from xml_converter.extract.xml_extractors import extract_required_fields
from xml_converter.io.xml_reader import parse_xml

from toolvalidator.adviestool_client import AdviestoolClient
from toolvalidator.database import ValidatorDatabase
from toolvalidator.labels import label_distance, label_from_beng2


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _float(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_payload_with_warnings(fields: Any) -> tuple[dict[str, Any], list[str]]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        payload = build_api_input(fields)
    return payload, [str(item.message) for item in caught]


def _is_apartment(fields: Any) -> bool:
    return str(getattr(fields, "building_category", "") or "").strip() == "7"


def _is_unsupported_installation_error(exc: Exception) -> bool:
    return str(exc).startswith("Installation mapping failed:")


def _installation_detail(fields: Any) -> str:
    heat = str(getattr(fields, "opwekkertype_verwarming", "") or "<missing>").strip()
    hotwater = str(getattr(fields, "opwekkertype_tapwater", "") or "<missing>").strip()
    return f"{heat}/{hotwater}"


def _normalize_key_part(value: Any) -> str:
    return str(value or "").replace(" ", "").strip().upper()


def _unique_address_key(fields: Any, fallback_filename: str) -> str:
    return _unique_address_key_from_values(
        zipcode=getattr(fields, "zipcode", None),
        number=getattr(fields, "house_number", None),
        annotation=getattr(fields, "building_annotation", None),
        bag_residence_id=getattr(fields, "bag_residence_id", None),
        fallback=fallback_filename,
    )


def _unique_address_key_from_values(
    zipcode: Any,
    number: Any,
    annotation: Any,
    bag_residence_id: Any,
    fallback: str,
) -> str:
    zipcode = _normalize_key_part(zipcode)
    number = str(number or "").strip()
    annotation = _normalize_key_part(annotation)
    bag_residence_id = str(bag_residence_id or "").strip()
    if zipcode and number:
        return f"TPG:{zipcode}:{number}:{annotation}"
    if bag_residence_id:
        return f"BAG:{bag_residence_id}"
    return f"FILE:{fallback}"


def _load_existing_unique_keys(conn: Any) -> set[str]:
    keys: set[str] = set()
    for row in conn.execute(
        """
        SELECT zipcode, house_number, building_annotation, bag_residence_id, xml_files.filename
        FROM xml_extracted
        JOIN xml_files ON xml_files.id = xml_extracted.xml_file_id
        """
    ):
        keys.add(
            _unique_address_key_from_values(
                zipcode=row["zipcode"],
                number=row["house_number"],
                annotation=row["building_annotation"],
                bag_residence_id=row["bag_residence_id"],
                fallback=row["filename"],
            )
        )
    for row in conn.execute(
        """
        SELECT detail
        FROM excluded_cases
        WHERE category = 'duplicate_address'
        """
    ):
        keys.add(str(row["detail"]))
    return keys


def run_validation(
    xml_dir: Path,
    out_db: Path,
    base_url: str,
    pattern: str = "*.xml",
    limit: int | None = None,
    notes: str | None = None,
    timeout: float = 60.0,
    hash_files: bool = True,
) -> int | None:
    xml_paths = sorted(xml_dir.glob(pattern))
    if limit is not None:
        xml_paths = xml_paths[:limit]

    db = ValidatorDatabase(out_db)
    client = AdviestoolClient(base_url=base_url, timeout=timeout)
    conn = None
    run_id: int | None = None
    existing_unique_keys: set[str] = set()
    seen_unique_keys: set[str] = set()

    def ensure_run() -> tuple[Any, int]:
        nonlocal conn, run_id
        if conn is None:
            conn = db.connect()
            db.initialize(conn)
        if run_id is None:
            run_id = db.create_run(conn, xml_dir, base_url, notes)
        return conn, run_id

    if out_db.exists():
        conn = db.connect()
        db.initialize(conn)
        existing_unique_keys = _load_existing_unique_keys(conn)
        if existing_unique_keys:
            print(f"Resume mode: loaded {len(existing_unique_keys)} existing address keys from {out_db}")

    try:
        for index, xml_path in enumerate(xml_paths, start=1):
            try:
                tree = parse_xml(xml_path)
                fields = extract_required_fields(tree)
            except Exception as exc:
                active_conn, active_run_id = ensure_run()
                file_hash = _sha256(xml_path) if hash_files else None
                xml_file_id = db.insert_xml_file(active_conn, active_run_id, xml_path, file_hash)
                db.mark_status(active_conn, xml_file_id, "error", "extract", str(exc))
                active_conn.commit()
                print(f"[{index}/{len(xml_paths)}] extract error: {xml_path.name}: {exc}")
                continue

            if _is_apartment(fields):
                print(f"[{index}/{len(xml_paths)}] skipped apartment: {xml_path.name}")
                continue

            unique_key = _unique_address_key(fields, xml_path.name)
            if unique_key in existing_unique_keys:
                if index == 1 or index % 500 == 0 or index == len(xml_paths):
                    print(f"[{index}/{len(xml_paths)}] skipped already in db: {xml_path.name}")
                continue

            if unique_key in seen_unique_keys:
                active_conn, active_run_id = ensure_run()
                db.increment_excluded_case(
                    active_conn,
                    active_run_id,
                    "duplicate_address",
                    unique_key,
                    xml_path.name,
                )
                active_conn.commit()
                print(f"[{index}/{len(xml_paths)}] skipped duplicate address ({unique_key}): {xml_path.name}")
                continue
            seen_unique_keys.add(unique_key)

            try:
                payload, mapping_warnings = _build_payload_with_warnings(fields)
            except Exception as exc:
                if _is_unsupported_installation_error(exc):
                    active_conn, active_run_id = ensure_run()
                    detail = _installation_detail(fields)
                    db.increment_excluded_case(
                        active_conn,
                        active_run_id,
                        "unsupported_installation",
                        detail,
                        xml_path.name,
                    )
                    active_conn.commit()
                    print(
                        f"[{index}/{len(xml_paths)}] skipped unsupported installation "
                        f"({detail}): {xml_path.name}"
                    )
                    continue

                active_conn, active_run_id = ensure_run()
                file_hash = _sha256(xml_path) if hash_files else None
                xml_file_id = db.insert_xml_file(active_conn, active_run_id, xml_path, file_hash)
                db.insert_extracted(active_conn, xml_file_id, fields)
                db.mark_status(active_conn, xml_file_id, "error", "map", str(exc))
                active_conn.commit()
                print(f"[{index}/{len(xml_paths)}] map error: {xml_path.name}: {exc}")
                continue

            active_conn, active_run_id = ensure_run()
            file_hash = _sha256(xml_path) if hash_files else None
            xml_file_id = db.insert_xml_file(active_conn, active_run_id, xml_path, file_hash)
            db.insert_extracted(active_conn, xml_file_id, fields)
            db.insert_request(active_conn, xml_file_id, payload, mapping_warnings)

            result = client.post_current(payload)
            if result.error_message is not None and result.response_json is None:
                db.insert_response(active_conn, xml_file_id, result.http_status, result.response_json)
                db.mark_status(active_conn, xml_file_id, "error", "api", result.error_message)
                active_conn.commit()
                print(f"[{index}/{len(xml_paths)}] api error: {xml_path.name}: {result.error_message}")
                continue

            if result.http_status != 200:
                db.insert_response(active_conn, xml_file_id, result.http_status, result.response_json)
                db.mark_status(
                    active_conn,
                    xml_file_id,
                    "error",
                    "api",
                    result.error_message or f"Unexpected HTTP status {result.http_status}",
                )
                active_conn.commit()
                print(f"[{index}/{len(xml_paths)}] api status {result.http_status}: {xml_path.name}")
                continue

            predicted_beng2, predicted_label = db.insert_response(
                active_conn,
                xml_file_id,
                result.http_status,
                result.response_json,
            )
            xml_beng2 = _float(fields.indicator_primaire_fossiele_energie)
            xml_label = label_from_beng2(xml_beng2)
            predicted_label_derived = label_from_beng2(predicted_beng2)
            db.insert_comparison(
                active_conn,
                xml_file_id,
                xml_beng2,
                predicted_beng2,
                xml_label,
                predicted_label_derived or predicted_label,
                label_distance(xml_label, predicted_label_derived or predicted_label),
            )
            db.mark_status(active_conn, xml_file_id, "ok")
            active_conn.commit()

            if index == 1 or index % 25 == 0 or index == len(xml_paths):
                print(f"[{index}/{len(xml_paths)}] processed")
    finally:
        if conn is not None:
            conn.close()

    return run_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate monitor XML-derived /current requests against a local adviestool API."
    )
    parser.add_argument("--xml-dir", type=Path, default=Path("xml-files"))
    parser.add_argument("--out-db", type=Path, default=Path("toolvalidator-results.sqlite"))
    parser.add_argument("--base-url", default="http://localhost:5000")
    parser.add_argument("--pattern", default="*.xml")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--notes", default=None)
    parser.add_argument("--no-hash", action="store_true", help="Skip SHA-256 file hashes for faster runs.")
    args = parser.parse_args(argv)

    run_id = run_validation(
        xml_dir=args.xml_dir,
        out_db=args.out_db,
        base_url=args.base_url,
        pattern=args.pattern,
        limit=args.limit,
        notes=args.notes,
        timeout=args.timeout,
        hash_files=not args.no_hash,
    )
    if run_id is None:
        print(f"No non-apartment XML files or extraction errors found; no run written to {args.out_db}")
    else:
        print(f"Run {run_id} written to {args.out_db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

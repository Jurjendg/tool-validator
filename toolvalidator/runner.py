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

from xml_converter.extract.api_builder import build_api_input, build_apartment_api_input
from xml_converter.extract.xml_extractors import extract_required_fields
from xml_converter.io.xml_reader import parse_xml

from toolvalidator.adviestool_client import AdviestoolClient
from toolvalidator.database import ValidatorDatabase
from toolvalidator.labels import label_distance, label_from_beng2

QUARANTINE_AREA_SHARE_THRESHOLD = 0.15


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


def _build_payload_with_warnings(fields: Any, building_kind: str) -> tuple[dict[str, Any], list[str]]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if building_kind == "apartment":
            payload = build_apartment_api_input(fields)
        else:
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


def _normalize_system_value(value: Any) -> str:
    return str(value or "").replace(" ", "").strip().lower()


def _quarantine_case(category: str, detail: str, **data: Any) -> dict[str, Any]:
    return {"category": category, "detail": detail, **data}


def _significant_area_share(area: float | None, living_area: float | None) -> float | None:
    if area is None or living_area is None or living_area <= 0:
        return None
    return area / living_area


def _system_differs_from_main(values: list[Any], main_value: Any) -> bool:
    normalized_main = _normalize_system_value(main_value)
    if not normalized_main:
        return False
    normalized_values = {
        _normalize_system_value(value)
        for value in values
        if _normalize_system_value(value)
    }
    if not normalized_values:
        return False
    return normalized_main not in normalized_values


def _quarantine_cases(fields: Any) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for raw_value in getattr(fields, "aantal_voorraadvaten", []) or []:
        value = _float(raw_value)
        if value is not None and value > 2:
            cases.append(
                _quarantine_case(
                    "too_many_storage_vessels",
                    f"AantalVoorraadvaten={raw_value}",
                    aantal_voorraadvaten=raw_value,
                )
            )

    living_area = _float(getattr(fields, "gebruiksoppervlakte", None))

    for idx, system in enumerate(getattr(fields, "verwarmingssystemen", []) or [], start=1):
        area = _float(system.get("aangesloten_oppervlak"))
        share = _significant_area_share(area, living_area)
        hoofdtypes = [
            str(value).strip()
            for value in system.get("hoofdtypes", [])
            if str(value).strip()
        ]
        if (
            share is not None
            and share > QUARANTINE_AREA_SHARE_THRESHOLD
            and _system_differs_from_main(hoofdtypes, getattr(fields, "opwekkertype_verwarming", None))
        ):
            cases.append(
                _quarantine_case(
                    "additional_heating_system",
                    (
                        f"Verwarmingssysteem[{idx}] area={area:g} "
                        f"share={share:.3f} types={','.join(hoofdtypes)}"
                    ),
                    system_index=idx,
                    area=area,
                    share=share,
                    main_type=getattr(fields, "opwekkertype_verwarming", None),
                    system_types=hoofdtypes,
                    system_id=system.get("id"),
                )
            )

    for idx, system in enumerate(getattr(fields, "tapwater_systemen", []) or [], start=1):
        area = _float(system.get("aangesloten_oppervlak"))
        share = _significant_area_share(area, living_area)
        toestellen = [
            str(value).strip()
            for value in system.get("toestellen", [])
            if str(value).strip()
        ]
        if (
            share is not None
            and share > QUARANTINE_AREA_SHARE_THRESHOLD
            and _system_differs_from_main(toestellen, getattr(fields, "opwekkertype_tapwater", None))
        ):
            cases.append(
                _quarantine_case(
                    "additional_hotwater_system",
                    (
                        f"Tapwatersysteem[{idx}] area={area:g} "
                        f"share={share:.3f} toestellen={','.join(toestellen)}"
                    ),
                    system_index=idx,
                    area=area,
                    share=share,
                    main_type=getattr(fields, "opwekkertype_tapwater", None),
                    system_types=toestellen,
                    system_id=system.get("id"),
                )
            )

    return cases


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


def _load_existing_unique_keys(conn: Any, building_kind: str) -> set[str]:
    keys: set[str] = set()
    for row in conn.execute(
        """
        SELECT zipcode, house_number, building_annotation, bag_residence_id, xml_files.filename
        FROM xml_extracted
        JOIN xml_files ON xml_files.id = xml_extracted.xml_file_id
        JOIN runs ON runs.id = xml_files.run_id
        WHERE COALESCE(runs.building_kind, 'house') = ?
        """,
        (building_kind,),
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
        JOIN runs ON runs.id = excluded_cases.run_id
        WHERE category = 'duplicate_address'
          AND COALESCE(runs.building_kind, 'house') = ?
        """,
        (building_kind,),
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
    building_kind: str = "house",
) -> int | None:
    if building_kind not in {"house", "apartment"}:
        raise ValueError(f"Unsupported building_kind '{building_kind}'.")

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
            run_id = db.create_run(conn, xml_dir, base_url, notes, building_kind)
        return conn, run_id

    if out_db.exists():
        conn = db.connect()
        db.initialize(conn)
        existing_unique_keys = _load_existing_unique_keys(conn, building_kind)
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

            if building_kind == "house" and _is_apartment(fields):
                print(f"[{index}/{len(xml_paths)}] skipped apartment: {xml_path.name}")
                continue
            if building_kind == "apartment" and not _is_apartment(fields):
                print(f"[{index}/{len(xml_paths)}] skipped non-apartment: {xml_path.name}")
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

            quarantine_cases = _quarantine_cases(fields)
            if quarantine_cases:
                active_conn, active_run_id = ensure_run()
                file_hash = _sha256(xml_path) if hash_files else None
                xml_file_id = db.insert_xml_file(active_conn, active_run_id, xml_path, file_hash)
                db.insert_extracted(active_conn, xml_file_id, fields)
                db.insert_quarantine_cases(active_conn, xml_file_id, quarantine_cases)
                details = "; ".join(case["detail"] for case in quarantine_cases)
                db.mark_status(active_conn, xml_file_id, "quarantined", "quarantine", details)
                active_conn.commit()
                print(f"[{index}/{len(xml_paths)}] quarantined: {xml_path.name}: {details}")
                continue

            try:
                payload, mapping_warnings = _build_payload_with_warnings(fields, building_kind)
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
    parser.add_argument(
        "--building-kind",
        choices=("house", "apartment"),
        default="house",
        help="Select the adviestool input builder and XML category filter.",
    )
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
        building_kind=args.building_kind,
    )
    if run_id is None:
        print(f"No {args.building_kind} XML files or extraction errors found; no run written to {args.out_db}")
    else:
        print(f"Run {run_id} written to {args.out_db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

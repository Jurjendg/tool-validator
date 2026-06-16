import csv
from pathlib import Path

from xml_converter.extract.mapper import map_monitorbestand
from xml_converter.extract.normalizer import normalize_record
from xml_converter.io.xml_reader import parse_xml
from xml_converter.validate.comparer import compare_prediction_to_xml


def run_batch_validation(xml_paths: list[Path], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for xml_path in xml_paths:
        tree = parse_xml(xml_path)
        record = normalize_record(map_monitorbestand(tree))
        comparison = compare_prediction_to_xml(record, prediction={})
        rows.append(comparison)

    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["bag_id", "xml_label_class", "predicted_label_class", "label_match"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

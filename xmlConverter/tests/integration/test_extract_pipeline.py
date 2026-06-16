import json
from pathlib import Path

from xml_converter.extract.export_prediction_input import export_prediction_input
from xml_converter.extract.mapper import map_monitorbestand
from xml_converter.extract.normalizer import normalize_record
from xml_converter.io.xml_reader import parse_xml


def test_extract_pipeline_writes_prediction_input(tmp_path: Path) -> None:
    xml_path = Path("tests/fixtures/sample_monitorbestand.xml")
    out_path = tmp_path / "prediction_input.json"

    tree = parse_xml(xml_path)
    record = normalize_record(map_monitorbestand(tree))
    export_prediction_input(record, out_path)

    payload = json.loads(out_path.read_text(encoding="utf-8"))

    assert payload["building"]["bag_id"] == "1234567890123456"
    assert payload["building"]["label_class"] == "A"

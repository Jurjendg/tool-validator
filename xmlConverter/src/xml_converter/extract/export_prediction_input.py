import json
from pathlib import Path

from xml_converter.domain.models import BuildingRecord


def export_prediction_input(record: BuildingRecord, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "building": record.to_dict(),
        "source": "monitorbestand",
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

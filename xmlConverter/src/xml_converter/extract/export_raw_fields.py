import json
from pathlib import Path

from xml_converter.extract.raw_fields import RawMonitorbestandFields


def export_raw_fields(fields: RawMonitorbestandFields, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(fields.to_dict(), indent=2), encoding="utf-8")

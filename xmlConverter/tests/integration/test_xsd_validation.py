from pathlib import Path

import pytest

from xml_converter.io.xsd_validator import validate_xml_against_xsd


@pytest.mark.xfail(
    reason=(
        "Current local schema chain does not validate provided anonymized XML due to namespace "
        "mismatch on nested elements (for example EPMeta)."
    ),
    strict=False,
)
def test_real_monitorbestand_xml_validates_against_real_schema() -> None:
    xml_path = Path("tests/fixtures/1216EZ-62-- (monitor)_anonymized.xml")
    xsd_path = Path("src/xml_converter/schemas/monitoringsbestand.xsd")

    validate_xml_against_xsd(xml_path, xsd_path)

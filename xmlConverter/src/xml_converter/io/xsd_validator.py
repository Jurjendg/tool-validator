from pathlib import Path

import lxml.etree as etree


def validate_xml_against_xsd(xml_path: Path, xsd_path: Path) -> None:
    xml_doc = etree.parse(str(xml_path))
    xsd_doc = etree.parse(str(xsd_path))
    schema = etree.XMLSchema(xsd_doc)

    if not schema.validate(xml_doc):
        details = "; ".join(error.message for error in schema.error_log)
        raise ValueError(f"XSD validation failed for {xml_path}: {details}")

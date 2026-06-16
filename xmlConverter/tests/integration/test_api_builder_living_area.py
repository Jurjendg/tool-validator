from pathlib import Path

from xml_converter.extract.api_builder import build_api_input
from xml_converter.extract.xml_extractors import extract_required_fields
from xml_converter.io.xml_reader import parse_xml


def test_build_api_input_maps_living_area_from_real_xml() -> None:
    xml_path = Path("tests/fixtures/1216EZ-62-- (monitor)_anonymized.xml")
    tree = parse_xml(xml_path)
    fields = extract_required_fields(tree)

    payload = build_api_input(fields)

    assert payload["LivingArea"] == 138.94
    assert payload["ConstructionYearCategory"] == 3
    assert payload["HousingType"] == 3
    assert payload["RoofType"] == 3
    assert payload["WallInsulation"] == 2
    assert payload["FloorInsulation"] == 1
    assert payload["FlatRoofInsulation"] == 2
    assert payload["SlopedRoofInsulation"] == 1
    assert payload["GlassBedroomArea"] == 3
    assert payload["GlassLivingArea"] == 3
    assert payload["Installation"] == 4
    assert payload["ShowerHeatRecovery"] == 1
    assert payload["Cooling"] == 2
    assert payload["Ventilation"] == 1
    assert isinstance(payload["SolarPanels"], list)
    assert len(payload["SolarPanels"]) >= 1

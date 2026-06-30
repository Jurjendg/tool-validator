from pathlib import Path

from xml_converter.extract.xml_extractors import extract_required_fields
from xml_converter.io.xml_reader import parse_xml


def test_extract_required_fields_from_real_monitorbestand() -> None:
    xml_path = Path("tests/fixtures/1216EZ-62-- (monitor)_anonymized.xml")
    tree = parse_xml(xml_path)

    fields = extract_required_fields(tree)

    assert fields.epmeta_version == "10.00"
    assert fields.main_building_class == "residential"
    assert fields.zipcode == "1216EZ"
    assert fields.house_number == "62"
    assert fields.building_category == "2"
    assert fields.building_category_supplement is None
    assert fields.construction_year == "1963"
    assert fields.gebruiksoppervlakte == "138.94"
    assert fields.labelklasse == "C"
    assert fields.indicator_primaire_fossiele_energie == "192.83"
    assert fields.gebruiksfuncties == [
        {
            "rekenzone_idx": 1,
            "functie_idx": 1,
            "rekenzone_omschrijving": "Rekenzone 511305724",
            "type": "Woning",
        },
        {
            "rekenzone_idx": 2,
            "functie_idx": 1,
            "rekenzone_omschrijving": "Rekenzone 1224054303",
            "type": "Woning",
        },
    ]
    assert fields.rc_gevels is not None
    assert fields.aantal_voorraadvaten
    assert len(fields.verwarmingssystemen) > 0
    assert fields.verwarmingssystemen[0]["aangesloten_oppervlak"] is not None
    assert len(fields.opwekkers) > 0
    assert len(fields.tapwater_systemen) > 0
    assert fields.tapwater_systemen[0]["aangesloten_oppervlak"] is not None
    assert len(fields.ventilatie_systemen) > 0
    assert len(fields.zonne_energie_systemen) > 0
    assert len(fields.raam_constructiedelen) > 0
    assert len(fields.dak_constructiedelen) > 0

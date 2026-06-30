from toolvalidator.runner import _quarantine_cases
from xml_converter.extract.raw_fields import RawMonitorbestandFields


def test_quarantine_cases_flags_storage_vessel_count_above_two() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="100",
        aantal_voorraadvaten=["1", "3"],
    )

    cases = _quarantine_cases(fields)

    assert [case["category"] for case in cases] == ["too_many_storage_vessels"]
    assert cases[0]["detail"] == "AantalVoorraadvaten=3"


def test_quarantine_cases_flags_additional_heating_system_over_area_threshold() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="100",
        opwekkertype_verwarming="HR107",
        verwarmingssystemen=[
            {
                "id": "1",
                "aangesloten_oppervlak": "85",
                "hoofdtypes": ["HR107"],
            },
            {
                "id": "2",
                "aangesloten_oppervlak": "16",
                "hoofdtypes": ["ElektrischeWarmtepomp"],
            },
        ],
    )

    cases = _quarantine_cases(fields)

    assert [case["category"] for case in cases] == ["additional_heating_system"]
    assert cases[0]["system_id"] == "2"


def test_quarantine_cases_ignores_matching_secondary_system() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="100",
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        verwarmingssystemen=[
            {
                "id": "2",
                "aangesloten_oppervlak": "16",
                "hoofdtypes": ["HR107"],
            },
        ],
        tapwater_systemen=[
            {
                "id": "3",
                "aangesloten_oppervlak": "16",
                "toestellen": ["CombiGKHRCW"],
            },
        ],
    )

    assert _quarantine_cases(fields) == []


def test_quarantine_cases_flags_additional_hotwater_system_over_area_threshold() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="100",
        opwekkertype_tapwater="CombiGKHRCW",
        tapwater_systemen=[
            {
                "id": "1",
                "aangesloten_oppervlak": "84",
                "toestellen": ["CombiGKHRCW"],
            },
            {
                "id": "2",
                "aangesloten_oppervlak": "16",
                "toestellen": ["ElektrischeBoiler"],
            },
        ],
    )

    cases = _quarantine_cases(fields)

    assert [case["category"] for case in cases] == ["additional_hotwater_system"]
    assert cases[0]["system_id"] == "2"

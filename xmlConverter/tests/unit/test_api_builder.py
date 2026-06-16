import pytest

from xml_converter.extract.api_builder import build_api_input
from xml_converter.extract.raw_fields import RawMonitorbestandFields

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:Installation mapping warning.*defaulting to 4\\.:UserWarning"
    ),
    pytest.mark.filterwarnings(
        "ignore:ShowerHeatRecovery mapping warning.*defaulting to 1\\.:UserWarning"
    ),
    pytest.mark.filterwarnings(
        "ignore:Cooling mapping warning.*defaulting to 1\\.:UserWarning"
    ),
]

ROOF_ITEMS_DEFAULT = [
    {"orientatie": "horizontaal", "oppervlakte": "10", "dicht_rc": "1.0"},
    {"orientatie": "ZW", "oppervlakte": "10", "dicht_rc": "1.0"},
]

DEFAULT_RC_VLOEREN = "1.0"
VENTILATIE_ITEMS_DEFAULT = [
    {"ventilatie_hoofdtype": "A", "ventilatie_subtype": "A.1", "wtw_aanwezig": "0"},
]
RAAM_ITEMS_DEFAULT = [
    {"oppervlakte": "8.0", "raam_beglazing": "HR++"},
    {"oppervlakte": "1.0", "raam_beglazing": "Dubbel"},
]


def test_build_api_input_maps_living_area_directly() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="184.49",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    payload = build_api_input(fields)

    assert payload["LivingArea"] == 184.49
    assert payload["ConstructionYearCategory"] == 4
    assert payload["RoofType"] == 3
    assert payload["WallInsulation"] == 2
    assert payload["FlatRoofInsulation"] == 2
    assert payload["SlopedRoofInsulation"] == 2


def test_build_api_input_raises_when_living_area_missing() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte=None,
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    with pytest.raises(ValueError, match="Gebruiksoppervlakte"):
        build_api_input(fields)


@pytest.mark.parametrize(
    ("construction_year", "expected_category"),
    [
        ("1924", 1),
        ("1925", 2),
        ("1945", 2),
        ("1946", 3),
        ("1964", 3),
        ("1965", 4),
        ("1974", 4),
        ("1975", 5),
        ("1991", 5),
        ("1992", 6),
        ("2005", 6),
        ("2006", 7),
        ("2014", 7),
        ("2015", 8),
    ],
)
def test_build_api_input_maps_construction_year_category(
    construction_year: str, expected_category: int
) -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year=construction_year,
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    payload = build_api_input(fields)

    assert payload["ConstructionYearCategory"] == expected_category


def test_build_api_input_raises_when_construction_year_missing() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year=None,
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    with pytest.raises(ValueError, match="ConstructionYear"):
        build_api_input(fields)


@pytest.mark.parametrize(
    ("building_category", "expected_housing_type"),
    [
        ("1", 1),
        ("12", 2),
        ("2", 3),
        ("3", 4),
    ],
)
def test_build_api_input_maps_housing_type(
    building_category: str, expected_housing_type: int
) -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category=building_category,
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    payload = build_api_input(fields)

    assert payload["HousingType"] == expected_housing_type


def test_build_api_input_raises_when_housing_type_missing() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category=None,
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    with pytest.raises(ValueError, match="BuildingCategory"):
        build_api_input(fields)


def test_build_api_input_apartment_category_warns_and_raises_not_implemented() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="7",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    with pytest.warns(UserWarning, match="not implemented"):
        with pytest.raises(NotImplementedError, match="apartment category"):
            build_api_input(fields)


def test_build_api_input_raises_for_unsupported_housing_type() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="8",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    with pytest.raises(ValueError, match="not supported"):
        build_api_input(fields)


def test_build_api_input_maps_roof_type_from_example_case_to_3() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=[
            {"hellingshoek": "0", "orientatie": "horizontaal", "oppervlakte": "6.14", "dicht_rc": "2.50"},
            {"hellingshoek": "0", "orientatie": "horizontaal", "oppervlakte": "12.77", "dicht_rc": "0.86"},
            {"hellingshoek": "30", "orientatie": "ZW", "oppervlakte": "30.01", "dicht_rc": "0.22"},
        ],
        rc_gevels="1.80",
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    payload = build_api_input(fields)

    assert payload["RoofType"] == 3


def test_build_api_input_maps_roof_type_to_2_when_horizontal_over_75_pct() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=[
            {"orientatie": "horizontaal", "oppervlakte": "80"},
            {"orientatie": "ZW", "oppervlakte": "10", "dicht_rc": "1.0"},
        ],
        rc_gevels="1.80",
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    payload = build_api_input(fields)

    assert payload["RoofType"] == 2


def test_build_api_input_maps_roof_type_to_1_when_horizontal_not_over_25_pct() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=[
            {"orientatie": "horizontaal", "oppervlakte": "20", "dicht_rc": "1.0"},
            {"orientatie": "ZW", "oppervlakte": "80", "dicht_rc": "1.0"},
        ],
        rc_gevels="1.80",
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    payload = build_api_input(fields)

    assert payload["RoofType"] == 1


def test_build_api_input_raises_when_no_roofs_present_for_roof_insulation() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=[],
        rc_gevels="1.80",
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    with pytest.raises(ValueError, match="no roof entries"):
        build_api_input(fields)


def test_build_api_input_raises_when_weighted_roof_values_are_zero() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=[
            {"orientatie": "horizontaal", "oppervlakte": "0"},
            {"orientatie": "ZW", "oppervlakte": "0"},
        ],
        rc_gevels="1.80",
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
    )

    with pytest.raises(ValueError, match="weighted horizontal and sloped roof Rc values are 0"):
        build_api_input(fields)


@pytest.mark.parametrize(
    ("rc_gevels", "expected_wall_insulation"),
    [
        ("0.85", 1),
        ("0.86", 2),
        ("1.89", 2),
        ("1.90", 3),
        ("3.39", 3),
        ("3.40", 4),
    ],
)
def test_build_api_input_maps_wall_insulation(
    rc_gevels: str, expected_wall_insulation: int
) -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels=rc_gevels,
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    payload = build_api_input(fields)

    assert payload["WallInsulation"] == expected_wall_insulation


def test_build_api_input_raises_when_wall_insulation_source_missing() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels=None,
        rc_vloeren=DEFAULT_RC_VLOEREN,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    with pytest.raises(ValueError, match="RcGevels"):
        build_api_input(fields)


@pytest.mark.parametrize(
    ("rc_vloeren", "expected_floor_insulation"),
    [
        ("0.73", 1),
        ("0.74", 2),
        ("1.89", 2),
        ("1.90", 3),
        ("3.24", 3),
        ("3.25", 4),
    ],
)
def test_build_api_input_maps_floor_insulation(
    rc_vloeren: str, expected_floor_insulation: int
) -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren=rc_vloeren,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    payload = build_api_input(fields)

    assert payload["FloorInsulation"] == expected_floor_insulation


def test_build_api_input_raises_when_floor_insulation_source_missing() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren=None,
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    with pytest.raises(ValueError, match="RcVloeren"):
        build_api_input(fields)


def test_build_api_input_maps_flat_and_sloped_roof_insulation_from_example() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=[
            {"hellingshoek": "0", "orientatie": "horizontaal", "oppervlakte": "6.14", "dicht_rc": "2.50"},
            {"hellingshoek": "0", "orientatie": "horizontaal", "oppervlakte": "12.77", "dicht_rc": "0.86"},
            {"hellingshoek": "30", "orientatie": "ZW", "oppervlakte": "30.01", "dicht_rc": "0.22"},
        ],
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    payload = build_api_input(fields)

    assert payload["FlatRoofInsulation"] == 2
    assert payload["SlopedRoofInsulation"] == 1


def test_build_api_input_uses_available_weighted_value_when_other_side_missing() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=[
            {"orientatie": "horizontaal", "oppervlakte": "12.0", "dicht_rc": "2.10"},
            {"orientatie": "horizontaal", "oppervlakte": "8.0", "dicht_rc": "1.90"},
        ],
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
    )

    payload = build_api_input(fields)

    assert payload["FlatRoofInsulation"] == 2
    assert payload["SlopedRoofInsulation"] == 2


def test_build_api_input_maps_glass_fields_from_example_for_housing_type_2() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=[
            {"oppervlakte": "5.68", "raam_u": "1.80", "raam_g": "0.60", "raam_beglazing": "HR++"},
            {"oppervlakte": "1.22", "raam_u": "2.90", "raam_g": "0.75", "raam_beglazing": "Dubbel"},
            {"oppervlakte": "1.22", "raam_u": "2.90", "raam_g": "0.75", "raam_beglazing": "Dubbel"},
            {"oppervlakte": "2.39", "raam_u": "1.80", "raam_g": "0.60", "raam_beglazing": "HR++"},
            {"oppervlakte": "0.22", "raam_u": "5.10", "raam_g": "0.80", "raam_beglazing": "Enkel"},
        ],
    )

    payload = build_api_input(fields)

    assert payload["GlassBedroomArea"] == 3
    assert payload["GlassLivingArea"] == 2


def test_build_api_input_maps_glass_fields_from_example_for_housing_type_3() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="2",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=[
            {"oppervlakte": "5.68", "raam_u": "1.80", "raam_g": "0.60", "raam_beglazing": "HR++"},
            {"oppervlakte": "1.22", "raam_u": "2.90", "raam_g": "0.75", "raam_beglazing": "Dubbel"},
            {"oppervlakte": "1.22", "raam_u": "2.90", "raam_g": "0.75", "raam_beglazing": "Dubbel"},
            {"oppervlakte": "2.39", "raam_u": "1.80", "raam_g": "0.60", "raam_beglazing": "HR++"},
            {"oppervlakte": "0.22", "raam_u": "5.10", "raam_g": "0.80", "raam_beglazing": "Enkel"},
        ],
    )

    payload = build_api_input(fields)

    assert payload["GlassBedroomArea"] == 3
    assert payload["GlassLivingArea"] == 3


def test_build_api_input_sets_glass_fields_equal_when_only_one_category_present() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=[
            {"oppervlakte": "8.0", "raam_beglazing": "HR++"},
            {"oppervlakte": "4.0", "raam_beglazing": "HR+"},
        ],
    )

    payload = build_api_input(fields)

    assert payload["GlassBedroomArea"] == 3
    assert payload["GlassLivingArea"] == 3


def test_build_api_input_raises_when_no_raam_constructiedelen_present() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=[],
    )

    with pytest.raises(ValueError, match="raam_constructiedelen"):
        build_api_input(fields)


def test_build_api_input_maps_installation_to_4_for_hr107_combi_example() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        verwarming_collectief="0",
        opwekkertype_tapwater="CombiGKHRCW",
        tapwater_collectief="0",
        zonneboiler_aanwezig="0",
        hybride_warmtepomp_samenvatting="0",
        douche_wtw_aanwezig="0",
        type_verwarming="Individueel",
        hybride_warmtepomp_verwarmingssysteem="0",
        opwekkers=[{"HoofdtypeVerwarmingstoestel": "HR107"}],
        tapwater_systemen=[{"collectief": "false", "toestel": "CombiGKHRCW", "toestellen": ["CombiGKHRCW"]}],
    )

    payload = build_api_input(fields)

    assert payload["Installation"] == 4
    assert payload["ShowerHeatRecovery"] == 1


def test_build_api_input_maps_installation_to_7_for_external_heat_and_hotwater() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="ExterneWarmtelevering",
        opwekkertype_tapwater="ExterneWarmtelevering",
        douche_wtw_aanwezig="0",
    )

    payload = build_api_input(fields)

    assert payload["Installation"] == 7


def test_build_api_input_external_mixed_warns_and_raises() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="ExterneWarmtelevering",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig="0",
    )

    with pytest.warns(UserWarning, match="external heating"):
        with pytest.raises(ValueError, match="ExterneWarmtelevering"):
            build_api_input(fields)


def test_build_api_input_maps_installation_to_8_for_hybrid_multi_generator_case() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        zonneboiler_aanwezig="0",
        hybride_warmtepomp_samenvatting="1",
        douche_wtw_aanwezig="0",
        opwekkers=[
            {"HoofdtypeVerwarmingstoestel": "ElektrischeWarmtepomp"},
            {"HoofdtypeVerwarmingstoestel": "HR107"},
        ],
        tapwater_systemen=[{"collectief": "false", "toestel": "CombiGKHRCW", "toestellen": ["CombiGKHRCW"]}],
    )

    payload = build_api_input(fields)

    assert payload["Installation"] == 8


def test_build_api_input_maps_shower_heat_recovery_from_zero_to_1() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig="0",
        koeling_aanwezig="0",
    )

    payload = build_api_input(fields)

    assert payload["ShowerHeatRecovery"] == 1


def test_build_api_input_maps_shower_heat_recovery_from_one_to_2() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig="1",
        koeling_aanwezig="0",
    )

    payload = build_api_input(fields)

    assert payload["ShowerHeatRecovery"] == 2


@pytest.mark.filterwarnings(
    "default:ShowerHeatRecovery mapping warning.*defaulting to 1\\.:UserWarning"
)
def test_build_api_input_defaults_shower_heat_recovery_to_1_when_missing() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig=None,
        koeling_aanwezig="0",
    )

    with pytest.warns(UserWarning, match="missing 'DoucheWTWAanwezig'"):
        payload = build_api_input(fields)

    assert payload["ShowerHeatRecovery"] == 1


def test_build_api_input_maps_cooling_to_1_when_absent() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig="0",
        koeling_aanwezig="0",
    )

    payload = build_api_input(fields)

    assert payload["Cooling"] == 1


def test_build_api_input_maps_cooling_to_2_for_standard_configuration() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig="0",
        koeling_aanwezig="1",
        koelsystemen=[
            {
                "koudeopwekkers": [
                    {"type_koelsysteem": "Compressie", "energiedrager": "elektriciteit"}
                ],
                "distributie_medium": "directe expansie in de ruimte",
            }
        ],
    )

    payload = build_api_input(fields)

    assert payload["Cooling"] == 2


def test_build_api_input_warns_on_non_standard_cooling_but_keeps_value_2() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig="0",
        koeling_aanwezig="1",
        koelsystemen=[
            {
                "koudeopwekkers": [{"type_koelsysteem": "Absorptie", "energiedrager": "gas"}],
                "distributie_medium": "water",
            }
        ],
    )

    with pytest.warns(UserWarning, match="non-standard cooling configuration"):
        payload = build_api_input(fields)

    assert payload["Cooling"] == 2


@pytest.mark.parametrize(
    ("hoofdtype", "subtype", "expected"),
    [
        ("A", "A.1", 1),
        ("C", "C.1", 2),
        ("Dc", "D.2", 3),
        ("Dd", "D.5b", 4),
    ],
)
def test_build_api_input_maps_ventilation_main_cases(
    hoofdtype: str, subtype: str, expected: int
) -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=[{"ventilatie_hoofdtype": hoofdtype, "ventilatie_subtype": subtype}],
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig="0",
        koeling_aanwezig="0",
    )

    payload = build_api_input(fields)

    assert payload["Ventilation"] == expected


def test_build_api_input_warns_for_unsupported_dc_subtype_but_keeps_3() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=[{"ventilatie_hoofdtype": "Dc", "ventilatie_subtype": "D.9"}],
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig="0",
        koeling_aanwezig="0",
    )

    with pytest.warns(UserWarning, match="not supported for Dc"):
        payload = build_api_input(fields)

    assert payload["Ventilation"] == 3


def test_build_api_input_warns_for_unsupported_dd_subtype_but_keeps_4() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=[{"ventilatie_hoofdtype": "Dd", "ventilatie_subtype": "D.9"}],
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig="0",
        koeling_aanwezig="0",
    )

    with pytest.warns(UserWarning, match="not supported for Dd"):
        payload = build_api_input(fields)

    assert payload["Ventilation"] == 4


def test_build_api_input_raises_when_no_ventilation_systems() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=[],
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig="0",
        koeling_aanwezig="0",
    )

    with pytest.raises(ValueError, match="no ventilation systems"):
        build_api_input(fields)


def test_build_api_input_raises_when_ventilation_system_e() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=[{"ventilatie_hoofdtype": "E", "ventilatie_subtype": "E.1"}],
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig="0",
        koeling_aanwezig="0",
    )

    with pytest.raises(ValueError, match="system E not supported"):
        build_api_input(fields)


def test_build_api_input_maps_solar_panels_from_example() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig="0",
        koeling_aanwezig="0",
        zonne_energie_systemen=[
            {
                "oppervlakte": "20.00",
                "aantal_panelen": "10",
                "hellingshoek": "35",
                "orientatie": "ZW",
                "spv": "4350",
                "paneeltype": "Kwaliteitsverklaring",
                "pvt_systeem": "0",
                "bouwintegratietype": "MatigGeventileerd",
            },
            {
                "oppervlakte": "8.00",
                "aantal_panelen": "4",
                "hellingshoek": "15",
                "orientatie": "NO",
                "spv": "1720",
                "paneeltype": "Kwaliteitsverklaring",
                "pvt_systeem": "0",
                "bouwintegratietype": "SterkGeventileerd",
            },
        ],
    )

    payload = build_api_input(fields)
    panels = payload["SolarPanels"]

    assert isinstance(panels, list)
    assert len(panels) == 2
    assert panels[0] == {
        "PVTotalWattPeak": 4350.0,
        "PVArea": 20.0,
        "InstallationAngle": 35,
        "Orientation": 225,
        "FreeRoofArea": 0.0,
        "RoofType": 1,
    }
    assert panels[1] == {
        "PVTotalWattPeak": 1720.0,
        "PVArea": 8.0,
        "InstallationAngle": 15,
        "Orientation": 45,
        "FreeRoofArea": 0.0,
        "RoofType": 2,
    }


def test_build_api_input_skips_pvt_systems_from_solar_panels() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig="0",
        koeling_aanwezig="0",
        zonne_energie_systemen=[
            {
                "oppervlakte": "20.00",
                "hellingshoek": "35",
                "orientatie": "ZW",
                "spv": "4350",
                "paneeltype": "Kwaliteitsverklaring",
                "pvt_systeem": "1",
                "bouwintegratietype": "MatigGeventileerd",
            }
        ],
    )

    payload = build_api_input(fields)

    assert payload["SolarPanels"] == []


def test_build_api_input_uses_specific_wattpeak_when_spv_missing_or_zero() -> None:
    fields = RawMonitorbestandFields(
        gebruiksoppervlakte="50.0",
        construction_year="1974",
        building_category="12",
        dak_constructiedelen=ROOF_ITEMS_DEFAULT,
        rc_gevels="1.80",
        rc_vloeren="1.00",
        ventilatie_systemen=VENTILATIE_ITEMS_DEFAULT,
        raam_constructiedelen=RAAM_ITEMS_DEFAULT,
        opwekkertype_verwarming="HR107",
        opwekkertype_tapwater="CombiGKHRCW",
        douche_wtw_aanwezig="0",
        koeling_aanwezig="0",
        zonne_energie_systemen=[
            {
                "oppervlakte": "12.00",
                "hellingshoek": "30",
                "orientatie": "Z",
                "spv": "0",
                "paneeltype": "Monokristalijn",
                "pvt_systeem": "0",
                "bouwintegratietype": "Onbekend",
            }
        ],
    )

    payload = build_api_input(fields)
    panel = payload["SolarPanels"][0]

    assert "PVTotalWattPeak" not in panel
    assert panel["SpecificWattpeak"] == 175.0



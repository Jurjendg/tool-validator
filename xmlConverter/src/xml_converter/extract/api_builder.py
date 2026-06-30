import warnings

from xml_converter.extract.raw_fields import RawMonitorbestandFields


def _parse_living_area(fields: RawMonitorbestandFields) -> float:
    raw = fields.gebruiksoppervlakte
    if raw is None or raw.strip() == "":
        raise ValueError("LivingArea mapping failed: 'Gebruiksoppervlakte' is missing.")

    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(
            f"LivingArea mapping failed: invalid 'Gebruiksoppervlakte' value '{raw}'."
        ) from exc

    if value <= 0:
        raise ValueError(
            f"LivingArea mapping failed: 'Gebruiksoppervlakte' must be > 0, got {value}."
        )

    return value


def _map_construction_year_category(fields: RawMonitorbestandFields) -> int:
    raw = fields.construction_year
    if raw is None or raw.strip() == "":
        raise ValueError("ConstructionYearCategory mapping failed: 'ConstructionYear' is missing.")

    try:
        year = int(raw)
    except ValueError as exc:
        raise ValueError(
            f"ConstructionYearCategory mapping failed: invalid 'ConstructionYear' value '{raw}'."
        ) from exc

    if year <= 1924:
        return 1
    if year <= 1945:
        return 2
    if year <= 1964:
        return 3
    if year <= 1974:
        return 4
    if year <= 1991:
        return 5
    if year <= 2005:
        return 6
    if year <= 2014:
        return 7
    return 8


def _map_housing_type(fields: RawMonitorbestandFields) -> int:
    raw = fields.building_category
    if raw is None or raw.strip() == "":
        raise ValueError("HousingType mapping failed: 'BuildingCategory' is missing.")

    try:
        category = int(raw)
    except ValueError as exc:
        raise ValueError(f"HousingType mapping failed: invalid 'BuildingCategory' value '{raw}'.") from exc

    if category == 1:
        return 1
    if category == 12:
        return 2
    if category == 2:
        return 3
    if category == 3:
        return 4
    if category == 7:
        warnings.warn(
            (
                "HousingType mapping for apartment category (BuildingCategory=7) is not implemented; "
                "use apartment-specific API flow."
            ),
            UserWarning,
            stacklevel=2,
        )
        raise NotImplementedError(
            "HousingType mapping failed: apartment category (BuildingCategory=7) is not yet implemented."
        )

    raise ValueError(
        f"HousingType mapping failed: BuildingCategory '{category}' is not supported for this API."
    )


def _map_roof_type(fields: RawMonitorbestandFields) -> int:
    if not fields.dak_constructiedelen:
        warnings.warn(
            "RoofType mapping warning: no roof entries present; defaulting RoofType to 2.",
            UserWarning,
            stacklevel=2,
        )
        return 2

    horizontal_area = 0.0
    other_area = 0.0
    for item in fields.dak_constructiedelen:
        raw_area = item.get("oppervlakte")
        if raw_area is None or str(raw_area).strip() == "":
            continue

        try:
            area = float(raw_area)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"RoofType mapping failed: invalid roof oppervlakte value '{raw_area}'."
            ) from exc

        orientation = str(item.get("orientatie") or "").strip().lower()
        if orientation == "horizontaal":
            horizontal_area += area
        else:
            other_area += area

    total_area = horizontal_area + other_area
    if total_area <= 0:
        warnings.warn(
            "RoofType mapping warning: total roof area is 0; defaulting RoofType to 2.",
            UserWarning,
            stacklevel=2,
        )
        return 2

    ratio = horizontal_area / total_area
    if ratio > 0.75:
        return 2
    if ratio > 0.25:
        return 3
    return 1


def _map_wall_insulation(fields: RawMonitorbestandFields) -> int:
    raw = fields.rc_gevels
    if raw is None or raw.strip() == "":
        raise ValueError("WallInsulation mapping failed: 'RcGevels' is missing.")

    try:
        rc_gevels = float(raw)
    except ValueError as exc:
        raise ValueError(f"WallInsulation mapping failed: invalid 'RcGevels' value '{raw}'.") from exc

    if rc_gevels < 0.86:
        return 1
    if rc_gevels < 1.9:
        return 2
    if rc_gevels < 3.4:
        return 3
    return 4


def _map_floor_insulation(fields: RawMonitorbestandFields) -> int:
    raw = fields.rc_vloeren
    if raw is None or raw.strip() == "":
        raise ValueError("FloorInsulation mapping failed: 'RcVloeren' is missing.")

    try:
        rc_vloeren = float(raw)
    except ValueError as exc:
        raise ValueError(f"FloorInsulation mapping failed: invalid 'RcVloeren' value '{raw}'.") from exc

    if rc_vloeren < 0.74:
        return 1
    if rc_vloeren < 1.9:
        return 2
    if rc_vloeren < 3.25:
        return 3
    return 4


def _classify_roof_insulation(weighted_rc: float) -> int:
    if weighted_rc < 0.9:
        return 1
    if weighted_rc < 2.25:
        return 2
    if weighted_rc < 4.71:
        return 3
    return 4


def _map_roof_insulation(fields: RawMonitorbestandFields) -> tuple[int, int]:
    if not fields.dak_constructiedelen:
        raise ValueError(
            "Roof insulation mapping failed: no roof entries present in 'dak_constructiedelen'."
        )

    horiz_num = 0.0
    horiz_den = 0.0
    other_num = 0.0
    other_den = 0.0

    for item in fields.dak_constructiedelen:
        raw_area = item.get("oppervlakte")
        raw_rc = item.get("dicht_rc")

        if raw_area is None or str(raw_area).strip() == "":
            continue
        if raw_rc is None or str(raw_rc).strip() == "":
            continue

        try:
            area = float(raw_area)
            rc = float(raw_rc)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Roof insulation mapping failed: invalid roof values oppervlakte='{raw_area}', dicht_rc='{raw_rc}'."
            ) from exc

        if area <= 0:
            continue

        orientation = str(item.get("orientatie") or "").strip().lower()
        if orientation == "horizontaal":
            horiz_num += rc * area
            horiz_den += area
        else:
            other_num += rc * area
            other_den += area

    weighted_horiz = (horiz_num / horiz_den) if horiz_den > 0 else 0.0
    weighted_other = (other_num / other_den) if other_den > 0 else 0.0

    if weighted_horiz == 0.0 and weighted_other == 0.0:
        raise ValueError(
            "Roof insulation mapping failed: both weighted horizontal and sloped roof Rc values are 0."
        )

    if weighted_horiz == 0.0:
        weighted_horiz = weighted_other
    if weighted_other == 0.0:
        weighted_other = weighted_horiz

    return _classify_roof_insulation(weighted_other), _classify_roof_insulation(weighted_horiz)


def _normalize_glass_category(raw: str) -> str:
    value = raw.strip().lower().replace(" ", "")
    if value in {"enkel"}:
        return "enkel"
    if value in {"voorzetraam", "dubbel", "hr"}:
        return "joined_dubbel"
    if value in {"hr+", "hr++"}:
        return "joined_hr"
    if value in {"3-voudig", "3voudig", "drievoudig"}:
        return "3-voudig"
    raise ValueError(f"Glass mapping failed: unsupported raam_beglazing value '{raw}'.")


def _glass_category_to_api_value(category: str) -> int:
    mapping = {
        "enkel": 1,
        "joined_dubbel": 2,
        "joined_hr": 3,
        "3-voudig": 4,
    }
    return mapping[category]


def _map_glass_areas(fields: RawMonitorbestandFields, housing_type: int) -> tuple[int, int]:
    if not fields.raam_constructiedelen:
        raise ValueError("Glass mapping failed: no entries present in 'raam_constructiedelen'.")

    category_area: dict[str, float] = {}
    total_area = 0.0

    for item in fields.raam_constructiedelen:
        raw_area = item.get("oppervlakte")
        raw_beglazing = item.get("raam_beglazing")
        if raw_area is None or str(raw_area).strip() == "":
            continue
        if raw_beglazing is None or str(raw_beglazing).strip() == "":
            continue

        try:
            area = float(raw_area)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Glass mapping failed: invalid raam oppervlakte value '{raw_area}'."
            ) from exc

        if area <= 0:
            continue

        category = _normalize_glass_category(str(raw_beglazing))
        category_area[category] = category_area.get(category, 0.0) + area
        total_area += area

    if total_area <= 0 or not category_area:
        raise ValueError("Glass mapping failed: no valid raam oppervlakte data present.")

    sorted_categories = sorted(category_area.items(), key=lambda item: item[1], reverse=True)
    largest_category, largest_area = sorted_categories[0]
    largest_fraction = largest_area / total_area

    if len(sorted_categories) == 1:
        mapped = _glass_category_to_api_value(largest_category)
        return mapped, mapped

    second_category, second_area = sorted_categories[1]
    second_fraction = second_area / total_area

    if housing_type in {1, 2}:
        largest_min = 0.50
        second_min = 0.20
        dominant_largest = 0.80
    elif housing_type in {3, 4}:
        largest_min = 0.40
        second_min = 0.30
        dominant_largest = 0.75
    else:
        raise ValueError(f"Glass mapping failed: unsupported HousingType '{housing_type}'.")

    if largest_fraction <= largest_min:
        warnings.warn(
            (
                f"GlassBedroomArea mapping warning: largest glass category fraction "
                f"({largest_fraction:.3f}) is out of expected limits for HousingType={housing_type}."
            ),
            UserWarning,
            stacklevel=2,
        )

    bedroom_value = _glass_category_to_api_value(largest_category)

    if largest_fraction > dominant_largest:
        return bedroom_value, bedroom_value

    if second_fraction <= second_min:
        warnings.warn(
            (
                f"GlassLivingArea mapping warning: second largest glass category fraction "
                f"({second_fraction:.3f}) is out of expected limits for HousingType={housing_type}."
            ),
            UserWarning,
            stacklevel=2,
        )

    living_value = _glass_category_to_api_value(second_category)
    return bedroom_value, living_value


def _flag_to_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "ja", "yes"}


def _parse_float_or_none(value: object) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _normalize_value(value: str | None) -> str:
    return (value or "").strip()


def _collect_opwekker_types(fields: RawMonitorbestandFields) -> list[str]:
    result: list[str] = []
    for opwekker in fields.opwekkers:
        hoofdtype = opwekker.get("HoofdtypeVerwarmingstoestel")
        if isinstance(hoofdtype, str) and hoofdtype.strip():
            result.append(hoofdtype.strip())
    return result


def _collect_tapwater_toestellen(fields: RawMonitorbestandFields) -> list[str]:
    toestellen: list[str] = []
    for systeem in fields.tapwater_systemen:
        multi = systeem.get("toestellen")
        if isinstance(multi, list):
            toestellen.extend([str(t).strip() for t in multi if str(t).strip()])
            continue
        single = systeem.get("toestel")
        if isinstance(single, str) and single.strip():
            toestellen.append(single.strip())
    return toestellen


def _map_installation(fields: RawMonitorbestandFields) -> int:
    opwekkertype_verwarming = _normalize_value(fields.opwekkertype_verwarming)
    opwekkertype_tapwater = _normalize_value(fields.opwekkertype_tapwater)

    # Backward-compatible fallback for early tests where installation inputs were not specified.
    if not opwekkertype_verwarming and not opwekkertype_tapwater:
        warnings.warn(
            "Installation mapping warning: heating and hot water generator types missing; defaulting to 4.",
            UserWarning,
            stacklevel=2,
        )
        return 4

    external_heat_values = {"ExterneWarmte", "ExterneWarmtelevering"}
    is_external_heat = opwekkertype_verwarming in external_heat_values
    is_external_hotwater = opwekkertype_tapwater in external_heat_values

    if is_external_heat and is_external_hotwater:
        return 7
    if is_external_heat != is_external_hotwater:
        warnings.warn(
            (
                "Installation mapping warning: external heating is only supported when both heating and "
                f"hot water are ExterneWarmtelevering; got '{opwekkertype_verwarming}/{opwekkertype_tapwater}'."
            ),
            UserWarning,
            stacklevel=2,
        )
        raise ValueError(
            "Installation mapping failed: unsupported combination with ExterneWarmtelevering."
        )

    if fields.verwarming_collectief not in {None, "0", "false", "False"} or fields.tapwater_collectief not in {
        None,
        "0",
        "false",
        "False",
    }:
        warnings.warn(
            "Installation mapping warning: collective installation not supported; continuing with available data.",
            UserWarning,
            stacklevel=2,
        )

    opwekker_types = _collect_opwekker_types(fields)
    tapwater_toestellen = _collect_tapwater_toestellen(fields)

    if len(opwekker_types) > 1 and not _flag_to_bool(fields.hybride_warmtepomp_samenvatting):
        warnings.warn(
            (
                "Installation mapping warning: multiple heating generators are not supported; "
                f"additional generators ignored ({', '.join(opwekker_types)})."
            ),
            UserWarning,
            stacklevel=2,
        )

    if len(fields.tapwater_systemen) > 1 or len(tapwater_toestellen) > 1:
        warnings.warn(
            (
                "Installation mapping warning: multiple hot water generators are not supported; "
                f"additional generators ignored ({', '.join(tapwater_toestellen) if tapwater_toestellen else 'n/a'})."
            ),
            UserWarning,
            stacklevel=2,
        )

    combi_tapwater = {"Combitoestel", "CombiGK", "CombiGKCW", "CombiGKHRCW"}
    hr104_107 = {"HR104", "HR104Lucht", "HR107", "HR107Lucht"}
    conv_types = {"Conventioneel", "VR", "ConventioneelLucht", "VRLucht"}
    heat_pump_hybrid_tapwater = {"Combitoestel", "CombiGKHRCW", "HR107"}

    if len(opwekker_types) > 1 and _flag_to_bool(fields.hybride_warmtepomp_samenvatting):
        opwekker_set = set(opwekker_types)
        if (
            "ElektrischeWarmtepomp" in opwekker_set
            and len(opwekker_set.intersection(hr104_107)) > 0
            and opwekkertype_tapwater in combi_tapwater
        ):
            return 8

    zonneboiler_aanwezig = _flag_to_bool(fields.zonneboiler_aanwezig)
    if not zonneboiler_aanwezig:
        if opwekkertype_verwarming in {
            "LokaalGasMetAfvoer",
            "LokaalGasZonderAfvoer",
        } and opwekkertype_tapwater in {
            "Badgeiser",
            "Keukengeiser",
        }:
            return 1
        if opwekkertype_verwarming in conv_types and opwekkertype_tapwater in {"Badgeiser", "Keukengeiser"}:
            return 2
        if opwekkertype_verwarming in conv_types.union({"HR100", "HR100Lucht"}) and opwekkertype_tapwater in combi_tapwater:
            return 3
        if opwekkertype_verwarming in hr104_107 and opwekkertype_tapwater in combi_tapwater:
            return 4
        if opwekkertype_verwarming == "HR107" and opwekkertype_tapwater == "HR107":
            return 4
        if opwekkertype_verwarming == "ElektrischeWarmtepomp" and opwekkertype_tapwater in {
            "WarmtepompRetourlucht",
            "WarmtepompOverig",
        }:
            return 6
        if opwekkertype_verwarming == "ElektrischeWarmtepomp" and opwekkertype_tapwater in heat_pump_hybrid_tapwater:
            return 8
    else:
        if opwekkertype_verwarming in hr104_107 and opwekkertype_tapwater in combi_tapwater.union(
            {"ZonneboilerMetGeïntegreerdeGasgestookteNaverwarming"}
        ):
            return 5
        warnings.warn(
            (
                "Installation mapping warning: "
                f"'{opwekkertype_verwarming}/{opwekkertype_tapwater}' not supported with solar boiler."
            ),
            UserWarning,
            stacklevel=2,
        )

    raise ValueError(
        "Installation mapping failed: "
        f"'{opwekkertype_verwarming}/{opwekkertype_tapwater}' not possible."
    )


def _map_shower_heat_recovery(fields: RawMonitorbestandFields) -> int:
    raw = fields.douche_wtw_aanwezig
    if raw is None or raw.strip() == "":
        warnings.warn(
            "ShowerHeatRecovery mapping warning: missing 'DoucheWTWAanwezig'; defaulting to 1.",
            UserWarning,
            stacklevel=2,
        )
        return 1

    value = raw.strip().lower()
    if value in {"0", "false"}:
        return 1
    if value in {"1", "true"}:
        return 2

    raise ValueError(
        f"ShowerHeatRecovery mapping failed: invalid 'DoucheWTWAanwezig' value '{raw}'."
    )


def _map_cooling(fields: RawMonitorbestandFields) -> int:
    raw = fields.koeling_aanwezig
    if raw is None or raw.strip() == "":
        warnings.warn(
            "Cooling mapping warning: missing 'KoelingAanwezig'; defaulting to 1.",
            UserWarning,
            stacklevel=2,
        )
        return 1

    value = raw.strip().lower()
    if value in {"0", "false"}:
        return 1
    if value not in {"1", "true"}:
        raise ValueError(f"Cooling mapping failed: invalid 'KoelingAanwezig' value '{raw}'.")

    # koeling_aanwezig == 1
    if len(fields.koelsystemen) > 1:
        warnings.warn(
            f"Cooling mapping warning: multiple Koelsystemen found ({len(fields.koelsystemen)}).",
            UserWarning,
            stacklevel=2,
        )

    all_koudeopwekkers: list[dict[str, str | None]] = []
    for systeem in fields.koelsystemen:
        koudeopwekkers = systeem.get("koudeopwekkers")
        if isinstance(koudeopwekkers, list):
            all_koudeopwekkers.extend([k for k in koudeopwekkers if isinstance(k, dict)])

    if len(all_koudeopwekkers) > 1:
        warnings.warn(
            f"Cooling mapping warning: multiple Koudeopwekkers found ({len(all_koudeopwekkers)}).",
            UserWarning,
            stacklevel=2,
        )

    divergences: list[str] = []
    for idx, opwekker in enumerate(all_koudeopwekkers, start=1):
        type_koel = (opwekker.get("type_koelsysteem") or "").strip()
        energiedrager = (opwekker.get("energiedrager") or "").strip()
        if type_koel != "Compressie":
            divergences.append(f"Koudeopwekker[{idx}].TypeKoelsysteem={type_koel or '<missing>'}")
        if energiedrager != "elektriciteit":
            divergences.append(f"Koudeopwekker[{idx}].Energiedrager={energiedrager or '<missing>'}")

    for idx, systeem in enumerate(fields.koelsystemen, start=1):
        distributie_medium = (systeem.get("distributie_medium") or "").strip()
        if distributie_medium != "directe expansie in de ruimte":
            divergences.append(
                f"Koelsysteem[{idx}].DistributieMedium={distributie_medium or '<missing>'}"
            )

    if divergences:
        warnings.warn(
            "Cooling mapping warning: non-standard cooling configuration detected: "
            + "; ".join(divergences),
            UserWarning,
            stacklevel=2,
        )

    return 2


def _map_ventilation(fields: RawMonitorbestandFields) -> int:
    if not fields.ventilatie_systemen:
        raise ValueError("Ventilation mapping failed: no ventilation systems present.")

    first = fields.ventilatie_systemen[0]
    first_hoofdtype_raw = (first.get("ventilatie_hoofdtype") or "").strip()
    first_hoofdtype = first_hoofdtype_raw.lower()
    first_subtype = (first.get("ventilatie_subtype") or "").strip()

    if len(fields.ventilatie_systemen) > 1:
        differing: list[str] = []
        for extra in fields.ventilatie_systemen[1:]:
            extra_hoofdtype = (extra.get("ventilatie_hoofdtype") or "").strip()
            if extra_hoofdtype.lower() != first_hoofdtype:
                differing.append(extra_hoofdtype or "<missing>")
        if differing:
            warnings.warn(
                (
                    "Ventilation mapping warning: multiple ventilation systems not supported; "
                    f"ignoring additional hoofdtype(s): {', '.join(differing)}."
                ),
                UserWarning,
                stacklevel=2,
            )

    if first_hoofdtype == "e":
        raise ValueError("Ventilation mapping failed: ventilation system E not supported.")
    if first_hoofdtype == "a":
        return 1
    if first_hoofdtype == "c":
        return 2
    if first_hoofdtype == "dc":
        supported = {"D.2", "D.3", "D.5a", "D.5c"}
        if first_subtype not in supported:
            warnings.warn(
                f"Ventilation mapping warning: subtype '{first_subtype or '<missing>'}' not supported for Dc.",
                UserWarning,
                stacklevel=2,
            )
        return 3
    if first_hoofdtype == "dd":
        supported = {"D.5b"}
        if first_subtype not in supported:
            warnings.warn(
                f"Ventilation mapping warning: subtype '{first_subtype or '<missing>'}' not supported for Dd.",
                UserWarning,
                stacklevel=2,
            )
        return 4

    raise ValueError(
        f"Ventilation mapping failed: unsupported ventilation hoofdtype '{first_hoofdtype_raw or '<missing>'}'."
    )


def _map_solar_panels(fields: RawMonitorbestandFields) -> list[dict[str, object]]:
    orientation_map = {
        "N": 0,
        "NO": 45,
        "O": 90,
        "ZO": 135,
        "Z": 180,
        "ZW": 225,
        "W": 270,
        "NW": 315,
    }
    paneeltype_specific_wattpeak = {
        "Monokristalijn": 175.0,
        "Multikristalijn": 165.0,
        "AmorfEnkelvJunctie": 65.0,
        "AmorfMultiJunctie": 55.0,
        "KoperGallium": 105.0,
        "Cadmium": 95.0,
    }
    roof_type_1 = {"NietGeventileerd", "MatigGeventileerd", "Onbekend"}

    solar_panels: list[dict[str, object]] = []
    for idx, systeem in enumerate(fields.zonne_energie_systemen, start=1):
        pvt_raw = str(systeem.get("pvt_systeem") or "0").strip()
        if pvt_raw in {"1", "true", "True"}:
            continue
        if pvt_raw not in {"0", "false", "False"}:
            raise ValueError(
                f"SolarPanels mapping failed: invalid PVTsysteem value '{pvt_raw}' for item {idx}."
            )

        raw_area = str(systeem.get("oppervlakte") or "").strip()
        raw_angle = str(systeem.get("hellingshoek") or "").strip()
        orientation_raw = str(systeem.get("orientatie") or "").strip()
        raw_spv = str(systeem.get("spv") or "").strip()
        paneeltype = str(systeem.get("paneeltype") or "").strip()
        bouwintegratietype = str(systeem.get("bouwintegratietype") or "").strip()

        if not raw_area or not raw_angle or not orientation_raw:
            raise ValueError(
                f"SolarPanels mapping failed: missing required PV field(s) for item {idx}."
            )

        try:
            pv_area = float(raw_area)
            installation_angle = int(float(raw_angle))
        except ValueError as exc:
            raise ValueError(
                f"SolarPanels mapping failed: invalid numeric PV field(s) for item {idx}."
            ) from exc

        if orientation_raw not in orientation_map:
            raise ValueError(
                f"SolarPanels mapping failed: unsupported orientation '{orientation_raw}' for item {idx}."
            )

        roof_type = 1 if bouwintegratietype in roof_type_1 else 2
        panel: dict[str, object] = {
            "PVArea": pv_area,
            "InstallationAngle": installation_angle,
            "Orientation": orientation_map[orientation_raw],
            "FreeRoofArea": 0.0,
            "RoofType": roof_type,
        }

        spv_value: float | None = None
        if raw_spv:
            try:
                spv_value = float(raw_spv)
            except ValueError as exc:
                raise ValueError(
                    f"SolarPanels mapping failed: invalid Spv '{raw_spv}' for item {idx}."
                ) from exc

        if spv_value is not None and spv_value != 0:
            panel["PVTotalWattPeak"] = spv_value
        else:
            if paneeltype not in paneeltype_specific_wattpeak:
                raise ValueError(
                    f"SolarPanels mapping failed: unsupported Paneeltype '{paneeltype}' for item {idx} when Spv is 0/missing."
                )
            panel["SpecificWattpeak"] = paneeltype_specific_wattpeak[paneeltype]

        solar_panels.append(panel)

    return solar_panels


def _map_apartment_subtype(fields: RawMonitorbestandFields) -> int:
    raw = fields.building_category_supplement
    if raw is None or raw.strip() == "":
        raise ValueError("Subtype mapping failed: 'BuildingCategorySupplement' is missing.")

    mapping = {
        "3": 1,  # Hoek/vloer -> corner ground floor
        "6": 2,  # Tussen/vloer -> in between ground floor
        "2": 3,  # Hoek/midden -> corner mid floor
        "5": 4,  # Tussen/midden -> in between mid floor
        "1": 5,  # Hoek/dak -> corner top floor
        "4": 6,  # Tussen/dak -> in between top floor
        "7": 7,  # Tussen/dak/vloer -> entire top floor
    }
    value = raw.strip()
    if value not in mapping:
        raise ValueError(
            f"Subtype mapping failed: unsupported BuildingCategorySupplement '{raw}'."
        )
    return mapping[value]


def _map_apartment_number_of_stories(fields: RawMonitorbestandFields) -> int:
    types = {
        str(item.get("type") or "").strip()
        for item in fields.gebruiksfuncties
        if str(item.get("type") or "").strip()
    }
    if "WoongebouwMeerdereWoonlagen" in types:
        return 2
    if "WoongebouwEenWoonlaag" in types:
        return 1
    raise ValueError(
        "NumberOfStories mapping failed: no apartment Gebruiksfunctie type found."
    )


def _default_apartment_insulation(fields: RawMonitorbestandFields) -> int:
    construction_year_category = _map_construction_year_category(fields)
    if construction_year_category <= 4:
        return 1
    if construction_year_category <= 5:
        return 2
    if construction_year_category <= 6:
        return 3
    return 4


def _map_apartment_wall_insulation(fields: RawMonitorbestandFields) -> int:
    raw = fields.rc_gevels
    if raw is None or raw.strip() == "":
        default = _default_apartment_insulation(fields)
        warnings.warn(
            f"WallInsulation mapping warning: 'RcGevels' is missing; defaulting to level {default} for apartment input.",
            UserWarning,
            stacklevel=2,
        )
        return default
    return _map_wall_insulation(fields)


def _map_apartment_floor_insulation(fields: RawMonitorbestandFields) -> int:
    raw = fields.rc_vloeren
    if raw is None or raw.strip() == "":
        default = _default_apartment_insulation(fields)
        warnings.warn(
            f"FloorInsulation mapping warning: 'RcVloeren' is missing; defaulting to level {default} for apartment input.",
            UserWarning,
            stacklevel=2,
        )
        return default
    return _map_floor_insulation(fields)


def _orientation_degrees(raw: object) -> int | None:
    orientation_map = {
        "N": 0,
        "NO": 45,
        "O": 90,
        "ZO": 135,
        "Z": 180,
        "ZW": 225,
        "W": 270,
        "NW": 315,
    }
    value = str(raw or "").strip().upper()
    return orientation_map.get(value)


def _has_opposite_orientation_pair(orientations: list[str]) -> bool:
    degrees = [_orientation_degrees(value) for value in orientations]
    clean_degrees = [value for value in degrees if value is not None]
    for degree in clean_degrees:
        if (degree + 180) % 360 in clean_degrees:
            return True
    return False


def _map_apartment_back_facade(fields: RawMonitorbestandFields) -> int:
    area_by_orientation: dict[str, float] = {}
    for item in fields.constructiedelen:
        part_kind = str(item.get("part_kind") or "").strip().lower()
        vlaktype = str(item.get("vlaktype") or "").strip().lower()
        if part_kind not in {"dicht", "raam", "deur", "paneel"}:
            continue
        if part_kind == "dicht" and vlaktype != "gevel":
            continue

        slope = _parse_float_or_none(item.get("hellingshoek"))
        if slope is None or slope < 75 or slope > 105:
            continue

        orientation = str(item.get("orientatie") or "").strip().upper()
        if _orientation_degrees(orientation) is None:
            continue

        area = _parse_float_or_none(item.get("oppervlakte"))
        if area is None or area <= 0:
            continue

        area_by_orientation[orientation] = area_by_orientation.get(orientation, 0.0) + area

    if not area_by_orientation:
        warnings.warn(
            "BackFacade mapping warning: no vertical facade construction parts with orientation found; defaulting to 0.",
            UserWarning,
            stacklevel=2,
        )
        return 0

    largest_area = max(area_by_orientation.values())
    significant = [
        orientation
        for orientation, area in area_by_orientation.items()
        if area >= largest_area * 0.20
    ]
    significant.sort(key=lambda orientation: _orientation_degrees(orientation) or 0)
    has_opposite_pair = _has_opposite_orientation_pair(significant)

    supplement = (fields.building_category_supplement or "").strip()
    if supplement in {"4", "5", "6", "7"}:
        if len(significant) not in {1, 2}:
            warnings.warn(
                (
                    "BackFacade mapping warning: expected 1 or 2 significant facade orientations "
                    f"for tussen apartment supplement {supplement}, got {len(significant)} ({significant})."
                ),
                UserWarning,
                stacklevel=2,
            )
        if len(significant) >= 2 and not has_opposite_pair:
            warnings.warn(
                (
                    "BackFacade mapping warning: multiple significant facade orientations are not opposite "
                    f"for supplement {supplement}: {significant}."
                ),
                UserWarning,
                stacklevel=2,
            )
        return 1 if has_opposite_pair else 0

    if supplement in {"1", "2", "3", "8"}:
        if len(significant) not in {2, 3}:
            warnings.warn(
                (
                    "BackFacade mapping warning: expected 2 or 3 significant facade orientations "
                    f"for hoek apartment supplement {supplement}, got {len(significant)} ({significant})."
                ),
                UserWarning,
                stacklevel=2,
            )
        if len(significant) >= 3 and not has_opposite_pair:
            warnings.warn(
                (
                    "BackFacade mapping warning: significant facade orientations do not include an opposite pair "
                    f"for supplement {supplement}: {significant}."
                ),
                UserWarning,
                stacklevel=2,
            )
        return 1 if len(significant) >= 3 and has_opposite_pair else 0

    raise ValueError(
        f"BackFacade mapping failed: unsupported BuildingCategorySupplement '{supplement or '<missing>'}'."
    )


def _warn_if_apartment_roof_not_flat(fields: RawMonitorbestandFields) -> None:
    horizontal_area = 0.0
    total_area = 0.0
    for item in fields.dak_constructiedelen:
        area = _parse_float_or_none(item.get("oppervlakte"))
        if area is None or area <= 0:
            continue
        total_area += area
        if str(item.get("orientatie") or "").strip().lower() == "horizontaal":
            horizontal_area += area

    if total_area <= 0:
        warnings.warn(
            "Apartment roof mapping warning: no valid roof area found; assuming flat roof for apartment input.",
            UserWarning,
            stacklevel=2,
        )
        return

    ratio = horizontal_area / total_area
    if ratio <= 0.75:
        warnings.warn(
            (
                "Apartment roof mapping warning: horizontal roof area is not more than 75% "
                f"of total roof area ({ratio:.3f}); still assuming flat roof for apartment input."
            ),
            UserWarning,
            stacklevel=2,
        )


def _map_apartment_roof_insulation(fields: RawMonitorbestandFields) -> int:
    if fields.dak_constructiedelen:
        weighted_num = 0.0
        weighted_den = 0.0
        for item in fields.dak_constructiedelen:
            area = _parse_float_or_none(item.get("oppervlakte"))
            rc = _parse_float_or_none(item.get("dicht_rc"))
            if area is None or rc is None or area <= 0:
                continue
            weighted_num += area * rc
            weighted_den += area

        if weighted_den > 0:
            return _classify_roof_insulation(weighted_num / weighted_den)

        default = _default_apartment_insulation(fields)
        warnings.warn(
            f"RoofInsulation mapping warning: roof entries contain no valid Rc/area values; defaulting to level {default}.",
            UserWarning,
            stacklevel=2,
        )
        return default

    rc_daken = _parse_float_or_none(fields.rc_daken)
    if rc_daken is None:
        default = _default_apartment_insulation(fields)
        warnings.warn(
            f"RoofInsulation mapping warning: no roof entries present and 'RcDaken' is missing; defaulting to level {default}.",
            UserWarning,
            stacklevel=2,
        )
        return default

    warnings.warn(
        "RoofInsulation mapping warning: no roof entries present; using summary 'RcDaken'.",
        UserWarning,
        stacklevel=2,
    )
    return _classify_roof_insulation(rc_daken)


def _map_apartment_installation(fields: RawMonitorbestandFields) -> int:
    heating_collective = _flag_to_bool(fields.verwarming_collectief)
    tapwater_collective = _flag_to_bool(fields.tapwater_collectief)
    opwekkertype_verwarming = _normalize_value(fields.opwekkertype_verwarming)
    opwekkertype_tapwater = _normalize_value(fields.opwekkertype_tapwater)

    if heating_collective != tapwater_collective:
        raise ValueError(
            "Installation mapping failed: mixed collective/individual heating and hot water is unsupported."
        )

    if not heating_collective and not tapwater_collective:
        return _map_installation(fields)

    hr104_107 = {"HR104", "HR104Lucht", "HR107", "HR107Lucht"}
    combi_tapwater = {"Combitoestel", "CombiGK", "CombiGKCW", "CombiGKHRCW"}
    heat_pump_tapwater = {"WarmtepompRetourlucht", "WarmtepompOverig"}

    if opwekkertype_verwarming in hr104_107 and opwekkertype_tapwater in combi_tapwater:
        return 9
    if opwekkertype_verwarming == "ElektrischeWarmtepomp" and opwekkertype_tapwater in heat_pump_tapwater:
        return 10

    raise ValueError(
        "Installation mapping failed: "
        f"unsupported collective combination '{opwekkertype_verwarming}/{opwekkertype_tapwater}'."
    )


def _map_apartment_solar_panels(fields: RawMonitorbestandFields) -> list[dict[str, object]]:
    panels = _map_solar_panels(fields)
    for panel in panels:
        panel.pop("RoofType", None)
    return panels


def build_apartment_api_input(fields: RawMonitorbestandFields) -> dict[str, object]:
    if str(fields.building_category or "").strip() != "7":
        raise ValueError("Apartment API input mapping failed: BuildingCategory is not 7.")

    _warn_if_apartment_roof_not_flat(fields)
    installation = _map_apartment_installation(fields)

    return {
        "ConstructionYearCategory": _map_construction_year_category(fields),
        "SubType": _map_apartment_subtype(fields),
        "LivingArea": _parse_living_area(fields),
        "NumberOfStories": _map_apartment_number_of_stories(fields),
        "BackFacade": _map_apartment_back_facade(fields),
        "WallInsulation": _map_apartment_wall_insulation(fields),
        "FloorInsulation": _map_apartment_floor_insulation(fields),
        "RoofInsulation": _map_apartment_roof_insulation(fields),
        "GlassLivingArea": _map_glass_areas(fields, 3)[1],
        "Installation": installation,
        "ShowerHeatRecovery": _map_shower_heat_recovery(fields),
        "Cooling": _map_cooling(fields),
        "Ventilation": _map_ventilation(fields),
        "ElectricCooking": 2 if installation in {6, 7} else 1,
        "Residents": 3,
        "SolarPanels": _map_apartment_solar_panels(fields),
    }


def build_api_input(fields: RawMonitorbestandFields) -> dict[str, object]:
    # Field-by-field mapping.
    housing_type = _map_housing_type(fields)
    sloped_roof_insulation, flat_roof_insulation = _map_roof_insulation(fields)
    glass_bedroom_area, glass_living_area = _map_glass_areas(fields, housing_type)
    installation = _map_installation(fields)
    shower_heat_recovery = _map_shower_heat_recovery(fields)
    cooling = _map_cooling(fields)
    ventilation = _map_ventilation(fields)
    solar_panels = _map_solar_panels(fields)
    return {
        "ConstructionYearCategory": _map_construction_year_category(fields),
        "HousingType": housing_type,
        "LivingArea": _parse_living_area(fields),
        "RoofType": _map_roof_type(fields),
        "WallInsulation": _map_wall_insulation(fields),
        "FloorInsulation": _map_floor_insulation(fields),
        "SlopedRoofInsulation": sloped_roof_insulation,
        "FlatRoofInsulation": flat_roof_insulation,
        "GlassBedroomArea": glass_bedroom_area,
        "GlassLivingArea": glass_living_area,
        "Installation": installation,
        "ShowerHeatRecovery": shower_heat_recovery,
        "Cooling": cooling,
        "Ventilation": ventilation,
        "SolarPanels": solar_panels,
    }

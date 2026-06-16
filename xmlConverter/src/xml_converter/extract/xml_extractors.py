from typing import Any

from lxml import etree

from xml_converter.extract.raw_fields import RawMonitorbestandFields

_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_LOWER = "abcdefghijklmnopqrstuvwxyz"


def _ci_step(segment: str) -> str:
    return (
        f"*["  # nosec B608
        f"translate(local-name(), '{_UPPER}', '{_LOWER}')='{segment.lower()}'"
        f"]"
    )


def _path_expr(path: str) -> str:
    return "./" + "/".join(_ci_step(part) for part in path.split("/"))


def _text_at(root: etree._Element, path: str) -> str | None:
    nodes = root.xpath(_path_expr(path))
    if not nodes:
        return None
    text = (nodes[0].text or "").strip()
    return text or None


def _text_at_any(root: etree._Element, paths: list[str]) -> str | None:
    for path in paths:
        value = _text_at(root, path)
        if value is not None:
            return value
    return None


def _nodes_at(root: etree._Element, path: str) -> list[etree._Element]:
    nodes = root.xpath(_path_expr(path))
    return [node for node in nodes if isinstance(node, etree._Element)]


def _element_to_dict(node: etree._Element) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if node.attrib:
        result["_attributes"] = dict(node.attrib)

    child_elements = [child for child in node if isinstance(child.tag, str)]
    if not child_elements:
        text = (node.text or "").strip()
        if text:
            result["_text"] = text
        return result

    for child in child_elements:
        key = etree.QName(child).localname
        value: Any
        if any(isinstance(grandchild.tag, str) for grandchild in child):
            value = _element_to_dict(child)
        else:
            value = (child.text or "").strip() or None

        if key in result:
            if not isinstance(result[key], list):
                result[key] = [result[key]]
            result[key].append(value)
        else:
            result[key] = value
    return result


def _extract_tapwater_systemen(root: etree._Element) -> list[dict[str, Any]]:
    systems = _nodes_at(
        root,
        (
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/"
            "Tapwatersystemen/Tapwatersysteem"
        ),
    )
    output: list[dict[str, Any]] = []
    for item in systems:
        tapwater_toestellen = _nodes_at(item, "TapwaterOpwekking/Tapwatertoestel")
        toestellen: list[str] = []
        for toestel in tapwater_toestellen:
            toestel_naam = _text_at(toestel, "Toestel")
            if toestel_naam:
                toestellen.append(toestel_naam)

        output.append(
            {
                "collectief": _text_at(item, "Collectief"),
                "toestel": toestellen[0] if toestellen else None,
                "toestellen": toestellen,
                "energiedrager": _text_at(item, "TapwaterOpwekking/Tapwatertoestel/Energiedrager"),
                "douche_wtw_type": _text_at(item, "DoucheWTW/Type"),
            }
        )
    return output


def _extract_ventilatie_systemen(root: etree._Element) -> list[dict[str, Any]]:
    systemen = _nodes_at(
        root,
        (
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/"
            "Ventilatiesystemen/Ventilatiesysteem"
        ),
    )
    output: list[dict[str, Any]] = []
    for item in systemen:
        output.append(
            {
                "ventilatie_hoofdtype": _text_at(item, "VentilatieHoofdtype"),
                "ventilatie_subtype": _text_at(item, "VentilatieSubtype"),
                "wtw_aanwezig": _text_at(item, "WTWaanwezig"),
            }
        )
    return output


def _extract_zonne_energie_systemen(root: etree._Element) -> list[dict[str, Any]]:
    systemen = _nodes_at(
        root,
        (
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/"
            "ZonneEnergiesystemen/ZonneEnergiesysteem"
        ),
    )
    output: list[dict[str, Any]] = []
    for item in systemen:
        output.append(
            {
                "oppervlakte": _text_at(item, "Oppervlakte"),
                "aantal_panelen": _text_at(item, "AantalPanelen"),
                "hellingshoek": _text_at(item, "Hellingshoek"),
                "orientatie": _text_at(item, "Orientatie"),
                "spv": _text_at(item, "Spv"),
                "paneeltype": _text_at(item, "Paneeltype"),
                "bouwintegratietype": _text_at(item, "Bouwintegratietype"),
                "pvt_systeem": _text_at(item, "PVTsysteem"),
            }
        )
    return output


def _extract_koelsystemen(root: etree._Element) -> list[dict[str, Any]]:
    koelsystemen = _nodes_at(
        root,
        (
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/"
            "Koelsystemen/Koelsysteem"
        ),
    )

    output: list[dict[str, Any]] = []
    for systeem in koelsystemen:
        koudeopwekkers = _nodes_at(systeem, "Koudeopwekkers/Koudeopwekker")
        opwekkers_data: list[dict[str, str | None]] = []
        for opwekker in koudeopwekkers:
            opwekkers_data.append(
                {
                    "type_koelsysteem": _text_at_any(opwekker, ["TypeKoelsysteem", "TypeKoeltoestel"]),
                    "energiedrager": _text_at(opwekker, "Energiedrager"),
                }
            )

        output.append(
            {
                "koudeopwekkers": opwekkers_data,
                "distributie_medium": _text_at(
                    systeem, "Koudedistributie/Distributieleidingen/DistributieMedium"
                ),
            }
        )

    return output


def _extract_constructiedelen(
    root: etree._Element,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    constructiedelen = _nodes_at(
        root,
        (
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/"
            "Rekenzones/Rekenzone/Transmissie/Constructiedelen/Constructiedeel"
        ),
    )
    raam_items: list[dict[str, Any]] = []
    dak_items: list[dict[str, Any]] = []
    all_items: list[dict[str, Any]] = []

    for idx, item in enumerate(constructiedelen, start=1):
        raam_present = bool(_nodes_at(item, "Raam"))
        deur_present = bool(_nodes_at(item, "Deur"))
        paneel_present = bool(_nodes_at(item, "Paneel"))
        vlaktype = (_text_at(item, "Vlaktype") or "").lower()
        part = {
            "idx": idx,
            "id": item.get("id"),
            "vlaktype": vlaktype or None,
            "hellingshoek": _text_at(item, "Hellingshoek"),
            "orientatie": _text_at(item, "Orientatie"),
            "oppervlakte": _text_at(item, "Oppervlakte"),
            "dicht_rc": _text_at_any(item, ["Dicht/Rc", "Vloer/Rc"]),
            "raam_u": _text_at(item, "Raam/U"),
            "raam_g": _text_at(item, "Raam/g"),
            "raam_beglazing": _text_at(item, "Raam/Beglazing"),
            "deur_u": _text_at(item, "Deur/U"),
            "paneel_u": _text_at(item, "Paneel/U"),
            "part_kind": "dicht",
        }
        if raam_present:
            part["part_kind"] = "raam"
        elif deur_present:
            part["part_kind"] = "deur"
        elif paneel_present:
            part["part_kind"] = "paneel"
        all_items.append(part)

        if raam_present:
            raam_items.append(
                {
                    "oppervlakte": _text_at(item, "Oppervlakte"),
                    "raam_u": _text_at(item, "Raam/U"),
                    "raam_g": _text_at(item, "Raam/g"),
                    "raam_beglazing": _text_at(item, "Raam/Beglazing"),
                }
            )

        if vlaktype == "dak":
            dak_items.append(
                {
                    "hellingshoek": _text_at(item, "Hellingshoek"),
                    "orientatie": _text_at(item, "Orientatie"),
                    "oppervlakte": _text_at(item, "Oppervlakte"),
                    "dicht_rc": _text_at(item, "Dicht/Rc"),
                }
            )

    return all_items, raam_items, dak_items


def extract_required_fields(tree: etree._ElementTree) -> RawMonitorbestandFields:
    root = tree.getroot()

    opwekkers = _nodes_at(
        root,
        (
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/"
            "Verwarmingssystemen/Verwarmingssysteem/Opwekkers/Opwekker"
        ),
    )
    opwekkers_block = [_element_to_dict(node) for node in opwekkers]

    tapwater_systemen = _extract_tapwater_systemen(root)
    ventilatie_systemen = _extract_ventilatie_systemen(root)
    zonne_energie_systemen = _extract_zonne_energie_systemen(root)
    koelsystemen = _extract_koelsystemen(root)
    constructiedelen, raam_constructiedelen, dak_constructiedelen = _extract_constructiedelen(root)

    return RawMonitorbestandFields(
        epmeta_version=_text_at(root, "EPMeta/Version"),
        main_building_class=_text_at(root, "EPObject/MainBuilding/MainBuildingClass"),
        zipcode=_text_at(root, "EPObject/MainBuilding/ObjectLocation/TPGIdentification/ZipCode"),
        house_number=_text_at(root, "EPObject/MainBuilding/ObjectLocation/TPGIdentification/Number"),
        building_annotation=_text_at(
            root,
            "EPObject/MainBuilding/ObjectLocation/TPGIdentification/BuildingAnnotation",
        ),
        bag_residence_id=_text_at(root, "EPObject/MainBuilding/ObjectLocation/BAGIdentification/BAGResidenceId"),
        building_category=_text_at(root, "EPObject/MainBuilding/ObjectInformation/BuildingCategory"),
        building_category_supplement=_text_at(
            root,
            "EPObject/MainBuilding/ObjectInformation/BuildingCategorySupplement",
        ),
        construction_year=_text_at(root, "EPObject/MainBuilding/ObjectInformation/ConstructionYear"),
        gebruiksoppervlakte=_text_at(root, "EPSurvey/Summary/Gebruiksoppervlakte"),
        labelklasse=_text_at(root, "EPSurvey/Summary/Labelklasse"),
        indicator_primaire_fossiele_energie=_text_at(
            root,
            "EPSurvey/Summary/IndicatorPrimaireFossieleEnergie",
        ),
        eis_primaire_fossiele_energie=_text_at(root, "EPSurvey/Summary/EisPrimaireFossieleEnergie"),
        rc_gevels=_text_at(
            root,
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/Samenvatting/RcGevels",
        ),
        rc_vloeren=_text_at(
            root,
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/Samenvatting/RcVloeren",
        ),
        rc_daken=_text_at(
            root,
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/Samenvatting/RcDaken",
        ),
        u_ramen=_text_at(
            root,
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/Samenvatting/URamen",
        ),
        g_ramen=_text_at(
            root,
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/Samenvatting/GRamen",
        ),
        opwekkertype_verwarming=_text_at(
            root,
            (
                "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/"
                "Samenvatting/OpwekkertypeVerwarming"
            ),
        ),
        verwarming_collectief=_text_at(
            root,
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/Samenvatting/VerwarmingCollectief",
        ),
        opwekkertype_tapwater=_text_at(
            root,
            (
                "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/"
                "Samenvatting/OpwekkertypeTapwater"
            ),
        ),
        tapwater_collectief=_text_at(
            root,
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/Samenvatting/TapwaterCollectief",
        ),
        douche_wtw_aanwezig=_text_at(
            root,
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/Samenvatting/DoucheWTWAanwezig",
        ),
        koeling_aanwezig=_text_at(
            root,
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/Samenvatting/KoelingAanwezig",
        ),
        zonneboiler_aanwezig=_text_at(
            root,
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/Samenvatting/ZonneboilerAanwezig",
        ),
        hybride_warmtepomp_samenvatting=_text_at(
            root,
            "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/Samenvatting/HybrideWarmtepomp",
        ),
        type_verwarming=_text_at_any(
            root,
            [
                (
                    "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/"
                    "Verwarmingssystemen/Verwarmingssysteem/TypeVerwarming"
                ),
                (
                    "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/"
                    "Verwarmingssysteem/TypeVerwarming"
                ),
            ],
        ),
        hybride_warmtepomp_verwarmingssysteem=_text_at_any(
            root,
            [
                (
                    "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/"
                    "Verwarmingssystemen/Verwarmingssysteem/HybrideWarmtepomp"
                ),
                (
                    "EPSurvey/SurveySourceData/Energieprestatie/Gebouw/Invoer/"
                    "Verwarmingssysteem/HybrideWarmtepomp"
                ),
            ],
        ),
        opwekkers=opwekkers_block,
        tapwater_systemen=tapwater_systemen,
        ventilatie_systemen=ventilatie_systemen,
        zonne_energie_systemen=zonne_energie_systemen,
        koelsystemen=koelsystemen,
        constructiedelen=constructiedelen,
        raam_constructiedelen=raam_constructiedelen,
        dak_constructiedelen=dak_constructiedelen,
    )

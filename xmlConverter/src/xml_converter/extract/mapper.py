import lxml.etree as etree

from xml_converter.domain.models import BuildingRecord


def _first_text(tree: etree._ElementTree, xpath: str) -> str | None:
    result = tree.xpath(xpath)
    if not result:
        return None
    value = result[0]
    if isinstance(value, etree._Element):
        return value.text
    return str(value)


def map_monitorbestand(tree: etree._ElementTree) -> BuildingRecord:
    bag_id = _first_text(tree, "string(//BagId)") or ""
    label_class = _first_text(tree, "string(//LabelClass)") or None

    build_year_raw = _first_text(tree, "string(//BuildYear)")
    usable_area_raw = _first_text(tree, "string(//UsableArea)")

    build_year = int(build_year_raw) if build_year_raw else None
    usable_area = float(usable_area_raw) if usable_area_raw else None

    return BuildingRecord(
        bag_id=bag_id,
        label_class=label_class,
        build_year=build_year,
        usable_area_m2=usable_area,
    )

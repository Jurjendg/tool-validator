from xml_converter.domain.models import BuildingRecord
from xml_converter.extract.normalizer import normalize_record


def test_normalize_record_uppercases_label_and_trims_bag_id() -> None:
    record = BuildingRecord(
        bag_id="  0123456789 ",
        label_class=" a++ ",
        build_year=1999,
        usable_area_m2=120.5,
    )

    normalized = normalize_record(record)

    assert normalized.bag_id == "0123456789"
    assert normalized.label_class == "A++"

from xml_converter.domain.models import BuildingRecord
from xml_converter.validate.comparer import compare_prediction_to_xml


def test_compare_prediction_to_xml() -> None:
    record = BuildingRecord(
        bag_id="0123456789",
        label_class="A",
        build_year=2012,
        usable_area_m2=95.0,
    )

    result = compare_prediction_to_xml(record, prediction={"label_class": "A"})

    assert result["label_match"] is True

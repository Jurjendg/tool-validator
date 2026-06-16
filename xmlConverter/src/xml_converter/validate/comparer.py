from xml_converter.domain.models import BuildingRecord


def compare_prediction_to_xml(record: BuildingRecord, prediction: dict) -> dict[str, object]:
    predicted_label = prediction.get("label_class")

    return {
        "bag_id": record.bag_id,
        "xml_label_class": record.label_class,
        "predicted_label_class": predicted_label,
        "label_match": predicted_label == record.label_class,
    }

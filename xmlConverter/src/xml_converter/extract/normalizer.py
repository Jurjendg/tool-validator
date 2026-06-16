from xml_converter.domain.models import BuildingRecord


def normalize_record(record: BuildingRecord) -> BuildingRecord:
    label = record.label_class.upper().strip() if record.label_class else None
    bag_id = record.bag_id.strip()

    return BuildingRecord(
        bag_id=bag_id,
        label_class=label,
        build_year=record.build_year,
        usable_area_m2=record.usable_area_m2,
    )

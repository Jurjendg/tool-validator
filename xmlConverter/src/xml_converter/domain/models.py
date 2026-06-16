from dataclasses import asdict, dataclass


@dataclass(slots=True)
class BuildingRecord:
    bag_id: str
    label_class: str | None
    build_year: int | None
    usable_area_m2: float | None

    def to_dict(self) -> dict[str, str | int | float | None]:
        return asdict(self)

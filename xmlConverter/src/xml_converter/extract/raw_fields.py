from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class RawMonitorbestandFields:
    epmeta_version: str | None = None
    main_building_class: str | None = None
    zipcode: str | None = None
    house_number: str | None = None
    building_annotation: str | None = None
    bag_residence_id: str | None = None
    building_category: str | None = None
    building_category_supplement: str | None = None
    construction_year: str | None = None
    gebruiksoppervlakte: str | None = None
    labelklasse: str | None = None
    indicator_primaire_fossiele_energie: str | None = None
    eis_primaire_fossiele_energie: str | None = None
    rc_gevels: str | None = None
    rc_vloeren: str | None = None
    rc_daken: str | None = None
    u_ramen: str | None = None
    g_ramen: str | None = None
    opwekkertype_verwarming: str | None = None
    verwarming_collectief: str | None = None
    opwekkertype_tapwater: str | None = None
    tapwater_collectief: str | None = None
    douche_wtw_aanwezig: str | None = None
    koeling_aanwezig: str | None = None
    zonneboiler_aanwezig: str | None = None
    hybride_warmtepomp_samenvatting: str | None = None
    type_verwarming: str | None = None
    hybride_warmtepomp_verwarmingssysteem: str | None = None
    aantal_voorraadvaten: list[str] = field(default_factory=list)
    verwarmingssystemen: list[dict[str, Any]] = field(default_factory=list)
    opwekkers: list[dict[str, Any]] = field(default_factory=list)
    tapwater_systemen: list[dict[str, Any]] = field(default_factory=list)
    ventilatie_systemen: list[dict[str, Any]] = field(default_factory=list)
    zonne_energie_systemen: list[dict[str, Any]] = field(default_factory=list)
    koelsystemen: list[dict[str, Any]] = field(default_factory=list)
    gebruiksfuncties: list[dict[str, Any]] = field(default_factory=list)
    constructiedelen: list[dict[str, Any]] = field(default_factory=list)
    raam_constructiedelen: list[dict[str, Any]] = field(default_factory=list)
    dak_constructiedelen: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

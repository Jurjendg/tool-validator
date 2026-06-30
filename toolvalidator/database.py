from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _float(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _first_dict(value: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    for key in keys:
        candidate = value.get(key)
        if isinstance(candidate, dict):
            return candidate
    return {}


def _first_value(value: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        candidate = value.get(key)
        if candidate is not None:
            return candidate
    return None


@dataclass(slots=True)
class ValidatorDatabase:
    path: Path

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY,
                started_at TEXT NOT NULL,
                xml_dir TEXT NOT NULL,
                adviestool_base_url TEXT NOT NULL,
                building_kind TEXT NOT NULL DEFAULT 'house',
                toolvalidator_version TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS xml_files (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                path TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_hash TEXT,
                status TEXT NOT NULL,
                error_stage TEXT,
                error_message TEXT
            );

            CREATE TABLE IF NOT EXISTS xml_extracted (
                xml_file_id INTEGER PRIMARY KEY REFERENCES xml_files(id) ON DELETE CASCADE,
                epmeta_version TEXT,
                main_building_class TEXT,
                zipcode TEXT,
                house_number TEXT,
                building_annotation TEXT,
                bag_residence_id TEXT,
                building_category TEXT,
                building_category_supplement TEXT,
                construction_year INTEGER,
                gebruiksoppervlakte REAL,
                labelklasse TEXT,
                xml_beng2 REAL,
                eis_primaire_fossiele_energie REAL,
                rc_gevels REAL,
                rc_vloeren REAL,
                rc_daken REAL,
                u_ramen REAL,
                g_ramen REAL,
                opwekkertype_verwarming TEXT,
                opwekkertype_tapwater TEXT,
                verwarming_collectief TEXT,
                tapwater_collectief TEXT,
                zonneboiler_aanwezig TEXT,
                douche_wtw_aanwezig TEXT,
                koeling_aanwezig TEXT,
                hybride_warmtepomp_samenvatting TEXT,
                type_verwarming TEXT,
                hybride_warmtepomp_verwarmingssysteem TEXT,
                raw_fields_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS api_requests (
                xml_file_id INTEGER PRIMARY KEY REFERENCES xml_files(id) ON DELETE CASCADE,
                building_kind TEXT NOT NULL DEFAULT 'house',
                construction_year_category INTEGER,
                housing_type INTEGER,
                subtype INTEGER,
                living_area REAL,
                roof_type INTEGER,
                number_of_stories INTEGER,
                back_facade INTEGER,
                wall_insulation INTEGER,
                floor_insulation INTEGER,
                roof_insulation INTEGER,
                sloped_roof_insulation INTEGER,
                flat_roof_insulation INTEGER,
                glass_living_area INTEGER,
                glass_bedroom_area INTEGER,
                installation INTEGER,
                shower_heat_recovery INTEGER,
                cooling INTEGER,
                ventilation INTEGER,
                solar_panel_count INTEGER,
                solar_panel_area_total REAL,
                payload_json TEXT NOT NULL,
                mapping_warnings_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS api_responses (
                xml_file_id INTEGER PRIMARY KEY REFERENCES xml_files(id) ON DELETE CASCADE,
                http_status INTEGER,
                predicted_beng2 REAL,
                predicted_label TEXT,
                response_json TEXT,
                warnings_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS comparisons (
                xml_file_id INTEGER PRIMARY KEY REFERENCES xml_files(id) ON DELETE CASCADE,
                xml_beng2 REAL,
                predicted_beng2 REAL,
                beng2_delta REAL,
                abs_beng2_delta REAL,
                xml_label_derived TEXT,
                predicted_label_derived TEXT,
                label_match INTEGER,
                label_distance INTEGER
            );

            CREATE TABLE IF NOT EXISTS roof_parts (
                xml_file_id INTEGER NOT NULL REFERENCES xml_files(id) ON DELETE CASCADE,
                idx INTEGER NOT NULL,
                orientatie TEXT,
                hellingshoek TEXT,
                oppervlakte REAL,
                dicht_rc REAL,
                PRIMARY KEY (xml_file_id, idx)
            );

            CREATE TABLE IF NOT EXISTS window_parts (
                xml_file_id INTEGER NOT NULL REFERENCES xml_files(id) ON DELETE CASCADE,
                idx INTEGER NOT NULL,
                oppervlakte REAL,
                raam_u REAL,
                raam_g REAL,
                raam_beglazing TEXT,
                PRIMARY KEY (xml_file_id, idx)
            );

            CREATE TABLE IF NOT EXISTS ventilation_systems (
                xml_file_id INTEGER NOT NULL REFERENCES xml_files(id) ON DELETE CASCADE,
                idx INTEGER NOT NULL,
                ventilatie_hoofdtype TEXT,
                ventilatie_subtype TEXT,
                wtw_aanwezig TEXT,
                raw_json TEXT NOT NULL,
                PRIMARY KEY (xml_file_id, idx)
            );

            CREATE TABLE IF NOT EXISTS solar_systems (
                xml_file_id INTEGER NOT NULL REFERENCES xml_files(id) ON DELETE CASCADE,
                idx INTEGER NOT NULL,
                oppervlakte REAL,
                aantal_panelen TEXT,
                hellingshoek TEXT,
                orientatie TEXT,
                spv REAL,
                paneeltype TEXT,
                bouwintegratietype TEXT,
                pvt_systeem TEXT,
                raw_json TEXT NOT NULL,
                PRIMARY KEY (xml_file_id, idx)
            );

            CREATE TABLE IF NOT EXISTS heating_generators (
                xml_file_id INTEGER NOT NULL REFERENCES xml_files(id) ON DELETE CASCADE,
                idx INTEGER NOT NULL,
                hoofdtype_verwarmingstoestel TEXT,
                raw_json TEXT NOT NULL,
                PRIMARY KEY (xml_file_id, idx)
            );

            CREATE TABLE IF NOT EXISTS tapwater_systems (
                xml_file_id INTEGER NOT NULL REFERENCES xml_files(id) ON DELETE CASCADE,
                idx INTEGER NOT NULL,
                collectief TEXT,
                toestel TEXT,
                energiedrager TEXT,
                douche_wtw_type TEXT,
                raw_json TEXT NOT NULL,
                PRIMARY KEY (xml_file_id, idx)
            );

            CREATE TABLE IF NOT EXISTS cooling_systems (
                xml_file_id INTEGER NOT NULL REFERENCES xml_files(id) ON DELETE CASCADE,
                idx INTEGER NOT NULL,
                distributie_medium TEXT,
                raw_json TEXT NOT NULL,
                PRIMARY KEY (xml_file_id, idx)
            );

            CREATE TABLE IF NOT EXISTS construction_parts (
                xml_file_id INTEGER NOT NULL REFERENCES xml_files(id) ON DELETE CASCADE,
                idx INTEGER NOT NULL,
                source_id TEXT,
                vlaktype TEXT,
                part_kind TEXT,
                orientatie TEXT,
                hellingshoek TEXT,
                oppervlakte REAL,
                rc REAL,
                u_value REAL,
                g_value REAL,
                beglazing TEXT,
                raw_json TEXT NOT NULL,
                PRIMARY KEY (xml_file_id, idx)
            );

            CREATE TABLE IF NOT EXISTS construction_part_summary (
                xml_file_id INTEGER NOT NULL REFERENCES xml_files(id) ON DELETE CASCADE,
                part_group TEXT NOT NULL,
                part_count INTEGER NOT NULL,
                total_area REAL,
                weighted_average_rc REAL,
                weighted_average_u REAL,
                weighted_average_g REAL,
                weighted_average_slope_angle REAL,
                PRIMARY KEY (xml_file_id, part_group)
            );

            CREATE TABLE IF NOT EXISTS excluded_cases (
                run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                detail TEXT NOT NULL,
                count INTEGER NOT NULL,
                first_filename TEXT,
                last_filename TEXT,
                PRIMARY KEY (run_id, category, detail)
            );

            CREATE INDEX IF NOT EXISTS idx_xml_files_run_status ON xml_files(run_id, status);
            CREATE INDEX IF NOT EXISTS idx_comparisons_abs_delta ON comparisons(abs_beng2_delta);
            CREATE INDEX IF NOT EXISTS idx_xml_extracted_installation_summary
                ON xml_extracted(opwekkertype_verwarming, opwekkertype_tapwater);
            CREATE INDEX IF NOT EXISTS idx_api_requests_categories
                ON api_requests(construction_year_category, housing_type, roof_type, installation);
            """
        )
        self._migrate(conn)
        self._create_views(conn)
        conn.commit()

    def _migrate(self, conn: sqlite3.Connection) -> None:
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(xml_extracted)").fetchall()
        }
        migrations = {
            "epmeta_version": "ALTER TABLE xml_extracted ADD COLUMN epmeta_version TEXT",
            "main_building_class": "ALTER TABLE xml_extracted ADD COLUMN main_building_class TEXT",
            "bag_residence_id": "ALTER TABLE xml_extracted ADD COLUMN bag_residence_id TEXT",
            "building_category_supplement": (
                "ALTER TABLE xml_extracted ADD COLUMN building_category_supplement TEXT"
            ),
            "type_verwarming": "ALTER TABLE xml_extracted ADD COLUMN type_verwarming TEXT",
            "hybride_warmtepomp_verwarmingssysteem": (
                "ALTER TABLE xml_extracted ADD COLUMN hybride_warmtepomp_verwarmingssysteem TEXT"
            ),
        }
        for column, statement in migrations.items():
            if column not in columns:
                conn.execute(statement)

        run_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(runs)").fetchall()
        }
        if "building_kind" not in run_columns:
            conn.execute("ALTER TABLE runs ADD COLUMN building_kind TEXT NOT NULL DEFAULT 'house'")

        request_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(api_requests)").fetchall()
        }
        request_migrations = {
            "building_kind": "ALTER TABLE api_requests ADD COLUMN building_kind TEXT NOT NULL DEFAULT 'house'",
            "subtype": "ALTER TABLE api_requests ADD COLUMN subtype INTEGER",
            "number_of_stories": "ALTER TABLE api_requests ADD COLUMN number_of_stories INTEGER",
            "back_facade": "ALTER TABLE api_requests ADD COLUMN back_facade INTEGER",
            "roof_insulation": "ALTER TABLE api_requests ADD COLUMN roof_insulation INTEGER",
        }
        for column, statement in request_migrations.items():
            if column not in request_columns:
                conn.execute(statement)
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_api_requests_apartment
                ON api_requests(building_kind, subtype, number_of_stories, back_facade, installation)
            """
        )

        summary_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(construction_part_summary)").fetchall()
        }
        if (
            summary_columns
            and "weighted_average_slope_angle" not in summary_columns
        ):
            conn.execute(
                "ALTER TABLE construction_part_summary ADD COLUMN weighted_average_slope_angle REAL"
            )

    def _create_views(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            DROP VIEW IF EXISTS v_validation_results;
            CREATE VIEW v_validation_results AS
            SELECT
                xf.id AS xml_file_id,
                xf.run_id,
                r.building_kind,
                xf.filename,
                xf.path,
                xf.status,
                xf.error_stage,
                xf.error_message,
                xe.zipcode,
                xe.house_number,
                xe.building_annotation,
                xe.bag_residence_id,
                xe.main_building_class,
                xe.building_category,
                xe.building_category_supplement,
                xe.construction_year,
                xe.gebruiksoppervlakte,
                xe.labelklasse AS xml_labelklasse,
                xe.xml_beng2,
                ar.predicted_beng2,
                c.beng2_delta,
                c.abs_beng2_delta,
                c.xml_label_derived,
                c.predicted_label_derived,
                c.label_match,
                c.label_distance,
                xe.rc_gevels,
                xe.rc_vloeren,
                xe.rc_daken,
                xe.u_ramen,
                xe.g_ramen,
                req.construction_year_category,
                req.building_kind AS request_building_kind,
                req.housing_type,
                req.subtype,
                req.living_area,
                req.roof_type,
                req.number_of_stories,
                req.back_facade,
                req.wall_insulation,
                req.floor_insulation,
                req.roof_insulation,
                req.sloped_roof_insulation,
                req.flat_roof_insulation,
                req.glass_living_area,
                req.glass_bedroom_area,
                req.installation,
                req.shower_heat_recovery,
                req.cooling,
                req.ventilation,
                xe.opwekkertype_verwarming,
                xe.opwekkertype_tapwater,
                xe.verwarming_collectief,
                xe.tapwater_collectief,
                xe.zonneboiler_aanwezig,
                xe.douche_wtw_aanwezig,
                xe.koeling_aanwezig,
                xe.hybride_warmtepomp_samenvatting,
                xe.type_verwarming,
                xe.hybride_warmtepomp_verwarmingssysteem,
                req.solar_panel_count,
                req.solar_panel_area_total,
                COALESCE(rp.roof_part_count, 0) AS roof_part_count,
                COALESCE(rp.roof_area_total, 0) AS roof_area_total,
                COALESCE(wp.window_part_count, 0) AS window_part_count,
                COALESCE(wp.window_area_total, 0) AS window_area_total,
                COALESCE(vs.ventilation_system_count, 0) AS ventilation_system_count,
                COALESCE(ss.solar_system_count, 0) AS solar_system_count,
                COALESCE(hg.heating_generator_count, 0) AS heating_generator_count,
                COALESCE(ts.tapwater_system_count, 0) AS tapwater_system_count,
                COALESCE(cs.cooling_system_count, 0) AS cooling_system_count
                , COALESCE(cps_gevel.total_area, 0) AS gevel_area_total
                , cps_gevel.weighted_average_rc AS gevel_average_rc
                , COALESCE(cps_vloer.total_area, 0) AS vloer_area_total
                , cps_vloer.weighted_average_rc AS vloer_average_rc
                , COALESCE(cps_dak.total_area, 0) AS dak_area_total
                , cps_dak.weighted_average_rc AS dak_average_rc
                , COALESCE(cps_dak_plat.total_area, 0) AS dak_plat_area_total
                , cps_dak_plat.weighted_average_rc AS dak_plat_average_rc
                , COALESCE(cps_dak_hellend.total_area, 0) AS dak_hellend_area_total
                , cps_dak_hellend.weighted_average_rc AS dak_hellend_average_rc
                , cps_dak_hellend.weighted_average_slope_angle AS dak_hellend_average_slope_angle
                , COALESCE(cps_raam.total_area, 0) AS raam_area_total
                , cps_raam.weighted_average_u AS raam_average_u
                , cps_raam.weighted_average_g AS raam_average_g
                , COALESCE(cps_deur.total_area, 0) AS deur_area_total
                , cps_deur.weighted_average_u AS deur_average_u
                , COALESCE(cps_paneel.total_area, 0) AS paneel_area_total
                , cps_paneel.weighted_average_u AS paneel_average_u
            FROM xml_files xf
            LEFT JOIN runs r ON r.id = xf.run_id
            LEFT JOIN xml_extracted xe ON xe.xml_file_id = xf.id
            LEFT JOIN api_requests req ON req.xml_file_id = xf.id
            LEFT JOIN api_responses ar ON ar.xml_file_id = xf.id
            LEFT JOIN comparisons c ON c.xml_file_id = xf.id
            LEFT JOIN (
                SELECT xml_file_id, count(*) AS roof_part_count, sum(oppervlakte) AS roof_area_total
                FROM roof_parts
                GROUP BY xml_file_id
            ) rp ON rp.xml_file_id = xf.id
            LEFT JOIN (
                SELECT xml_file_id, count(*) AS window_part_count, sum(oppervlakte) AS window_area_total
                FROM window_parts
                GROUP BY xml_file_id
            ) wp ON wp.xml_file_id = xf.id
            LEFT JOIN (
                SELECT xml_file_id, count(*) AS ventilation_system_count
                FROM ventilation_systems
                GROUP BY xml_file_id
            ) vs ON vs.xml_file_id = xf.id
            LEFT JOIN (
                SELECT xml_file_id, count(*) AS solar_system_count
                FROM solar_systems
                GROUP BY xml_file_id
            ) ss ON ss.xml_file_id = xf.id
            LEFT JOIN (
                SELECT xml_file_id, count(*) AS heating_generator_count
                FROM heating_generators
                GROUP BY xml_file_id
            ) hg ON hg.xml_file_id = xf.id
            LEFT JOIN (
                SELECT xml_file_id, count(*) AS tapwater_system_count
                FROM tapwater_systems
                GROUP BY xml_file_id
            ) ts ON ts.xml_file_id = xf.id
            LEFT JOIN (
                SELECT xml_file_id, count(*) AS cooling_system_count
                FROM cooling_systems
                GROUP BY xml_file_id
            ) cs ON cs.xml_file_id = xf.id
            LEFT JOIN construction_part_summary cps_gevel
                ON cps_gevel.xml_file_id = xf.id AND cps_gevel.part_group = 'gevel'
            LEFT JOIN construction_part_summary cps_vloer
                ON cps_vloer.xml_file_id = xf.id AND cps_vloer.part_group = 'vloer'
            LEFT JOIN construction_part_summary cps_dak
                ON cps_dak.xml_file_id = xf.id AND cps_dak.part_group = 'dak'
            LEFT JOIN construction_part_summary cps_dak_plat
                ON cps_dak_plat.xml_file_id = xf.id AND cps_dak_plat.part_group = 'dak_plat'
            LEFT JOIN construction_part_summary cps_dak_hellend
                ON cps_dak_hellend.xml_file_id = xf.id AND cps_dak_hellend.part_group = 'dak_hellend'
            LEFT JOIN construction_part_summary cps_raam
                ON cps_raam.xml_file_id = xf.id AND cps_raam.part_group = 'raam'
            LEFT JOIN construction_part_summary cps_deur
                ON cps_deur.xml_file_id = xf.id AND cps_deur.part_group = 'deur'
            LEFT JOIN construction_part_summary cps_paneel
                ON cps_paneel.xml_file_id = xf.id AND cps_paneel.part_group = 'paneel';
            """
        )

    def create_run(
        self,
        conn: sqlite3.Connection,
        xml_dir: Path,
        adviestool_base_url: str,
        notes: str | None,
        building_kind: str = "house",
    ) -> int:
        cur = conn.execute(
            """
            INSERT INTO runs (started_at, xml_dir, adviestool_base_url, building_kind, toolvalidator_version, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                str(xml_dir),
                adviestool_base_url,
                building_kind,
                "0.1.0",
                notes,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)

    def insert_xml_file(
        self,
        conn: sqlite3.Connection,
        run_id: int,
        xml_path: Path,
        file_hash: str | None,
    ) -> int:
        cur = conn.execute(
            """
            INSERT INTO xml_files (run_id, path, filename, file_hash, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, str(xml_path), xml_path.name, file_hash, "started"),
        )
        return int(cur.lastrowid)

    def mark_status(
        self,
        conn: sqlite3.Connection,
        xml_file_id: int,
        status: str,
        error_stage: str | None = None,
        error_message: str | None = None,
    ) -> None:
        conn.execute(
            """
            UPDATE xml_files
            SET status = ?, error_stage = ?, error_message = ?
            WHERE id = ?
            """,
            (status, error_stage, error_message, xml_file_id),
        )

    def increment_excluded_case(
        self,
        conn: sqlite3.Connection,
        run_id: int,
        category: str,
        detail: str,
        filename: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO excluded_cases (run_id, category, detail, count, first_filename, last_filename)
            VALUES (?, ?, ?, 1, ?, ?)
            ON CONFLICT(run_id, category, detail) DO UPDATE SET
                count = count + 1,
                last_filename = excluded.last_filename
            """,
            (run_id, category, detail, filename, filename),
        )

    def insert_extracted(self, conn: sqlite3.Connection, xml_file_id: int, fields: Any) -> None:
        data = fields.to_dict()
        conn.execute(
            """
            INSERT INTO xml_extracted (
                xml_file_id, epmeta_version, main_building_class, zipcode, house_number,
                building_annotation, bag_residence_id, building_category,
                building_category_supplement, construction_year, gebruiksoppervlakte, labelklasse, xml_beng2,
                eis_primaire_fossiele_energie, rc_gevels, rc_vloeren, rc_daken, u_ramen,
                g_ramen, opwekkertype_verwarming, opwekkertype_tapwater, verwarming_collectief,
                tapwater_collectief, zonneboiler_aanwezig, douche_wtw_aanwezig,
                koeling_aanwezig, hybride_warmtepomp_samenvatting, type_verwarming,
                hybride_warmtepomp_verwarmingssysteem, raw_fields_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                xml_file_id,
                data.get("epmeta_version"),
                data.get("main_building_class"),
                data.get("zipcode"),
                data.get("house_number"),
                data.get("building_annotation"),
                data.get("bag_residence_id"),
                data.get("building_category"),
                data.get("building_category_supplement"),
                _int(data.get("construction_year")),
                _float(data.get("gebruiksoppervlakte")),
                data.get("labelklasse"),
                _float(data.get("indicator_primaire_fossiele_energie")),
                _float(data.get("eis_primaire_fossiele_energie")),
                _float(data.get("rc_gevels")),
                _float(data.get("rc_vloeren")),
                _float(data.get("rc_daken")),
                _float(data.get("u_ramen")),
                _float(data.get("g_ramen")),
                data.get("opwekkertype_verwarming"),
                data.get("opwekkertype_tapwater"),
                data.get("verwarming_collectief"),
                data.get("tapwater_collectief"),
                data.get("zonneboiler_aanwezig"),
                data.get("douche_wtw_aanwezig"),
                data.get("koeling_aanwezig"),
                data.get("hybride_warmtepomp_samenvatting"),
                data.get("type_verwarming"),
                data.get("hybride_warmtepomp_verwarmingssysteem"),
                _json(data),
            ),
        )
        self._insert_child_tables(conn, xml_file_id, data)

    def _insert_child_tables(
        self,
        conn: sqlite3.Connection,
        xml_file_id: int,
        data: dict[str, Any],
    ) -> None:
        for idx, item in enumerate(data.get("dak_constructiedelen") or [], start=1):
            conn.execute(
                """
                INSERT INTO roof_parts
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    xml_file_id,
                    idx,
                    item.get("orientatie"),
                    item.get("hellingshoek"),
                    _float(item.get("oppervlakte")),
                    _float(item.get("dicht_rc")),
                ),
            )

        for idx, item in enumerate(data.get("raam_constructiedelen") or [], start=1):
            conn.execute(
                """
                INSERT INTO window_parts
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    xml_file_id,
                    idx,
                    _float(item.get("oppervlakte")),
                    _float(item.get("raam_u")),
                    _float(item.get("raam_g")),
                    item.get("raam_beglazing"),
                ),
            )

        for idx, item in enumerate(data.get("ventilatie_systemen") or [], start=1):
            conn.execute(
                """
                INSERT INTO ventilation_systems
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    xml_file_id,
                    idx,
                    item.get("ventilatie_hoofdtype"),
                    item.get("ventilatie_subtype"),
                    item.get("wtw_aanwezig"),
                    _json(item),
                ),
            )

        for idx, item in enumerate(data.get("zonne_energie_systemen") or [], start=1):
            conn.execute(
                """
                INSERT INTO solar_systems
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    xml_file_id,
                    idx,
                    _float(item.get("oppervlakte")),
                    item.get("aantal_panelen"),
                    item.get("hellingshoek"),
                    item.get("orientatie"),
                    _float(item.get("spv")),
                    item.get("paneeltype"),
                    item.get("bouwintegratietype"),
                    item.get("pvt_systeem"),
                    _json(item),
                ),
            )

        for idx, item in enumerate(data.get("opwekkers") or [], start=1):
            conn.execute(
                """
                INSERT INTO heating_generators
                VALUES (?, ?, ?, ?)
                """,
                (
                    xml_file_id,
                    idx,
                    item.get("HoofdtypeVerwarmingstoestel"),
                    _json(item),
                ),
            )

        for idx, item in enumerate(data.get("tapwater_systemen") or [], start=1):
            conn.execute(
                """
                INSERT INTO tapwater_systems
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    xml_file_id,
                    idx,
                    item.get("collectief"),
                    item.get("toestel"),
                    item.get("energiedrager"),
                    item.get("douche_wtw_type"),
                    _json(item),
                ),
            )

        for idx, item in enumerate(data.get("koelsystemen") or [], start=1):
            conn.execute(
                """
                INSERT INTO cooling_systems
                VALUES (?, ?, ?, ?)
                """,
                (
                    xml_file_id,
                    idx,
                    item.get("distributie_medium"),
                    _json(item),
                ),
            )

        self._insert_construction_parts(conn, xml_file_id, data.get("constructiedelen") or [])

    def _insert_construction_parts(
        self,
        conn: sqlite3.Connection,
        xml_file_id: int,
        items: list[dict[str, Any]],
    ) -> None:
        groups: dict[str, dict[str, float]] = {}

        for idx, item in enumerate(items, start=1):
            part_kind = item.get("part_kind")
            vlaktype = item.get("vlaktype")
            part_group = part_kind if part_kind in {"raam", "deur", "paneel"} else vlaktype
            rc = _float(item.get("dicht_rc"))
            if part_kind == "raam":
                u_value = _float(item.get("raam_u"))
                g_value = _float(item.get("raam_g"))
            elif part_kind == "deur":
                u_value = _float(item.get("deur_u"))
                g_value = None
            elif part_kind == "paneel":
                u_value = _float(item.get("paneel_u"))
                g_value = None
            else:
                u_value = None
                g_value = None

            area = _float(item.get("oppervlakte"))
            conn.execute(
                """
                INSERT INTO construction_parts
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    xml_file_id,
                    idx,
                    item.get("id"),
                    vlaktype,
                    part_kind,
                    item.get("orientatie"),
                    item.get("hellingshoek"),
                    area,
                    rc,
                    u_value,
                    g_value,
                    item.get("raam_beglazing"),
                    _json(item),
                ),
            )

            slope_angle = _float(item.get("hellingshoek"))

            def add_to_group(group_name: str, include_slope: bool = False) -> None:
                group = groups.setdefault(
                    group_name,
                    {
                        "count": 0.0,
                        "area": 0.0,
                        "rc_num": 0.0,
                        "rc_den": 0.0,
                        "u_num": 0.0,
                        "u_den": 0.0,
                        "g_num": 0.0,
                        "g_den": 0.0,
                        "slope_num": 0.0,
                        "slope_den": 0.0,
                    },
                )
                group["count"] += 1
                if area is not None:
                    group["area"] += area
                    if rc is not None:
                        group["rc_num"] += area * rc
                        group["rc_den"] += area
                    if u_value is not None:
                        group["u_num"] += area * u_value
                        group["u_den"] += area
                    if g_value is not None:
                        group["g_num"] += area * g_value
                        group["g_den"] += area
                    if include_slope and slope_angle is not None:
                        group["slope_num"] += area * slope_angle
                        group["slope_den"] += area

            if part_group:
                add_to_group(str(part_group))
                if str(vlaktype) == "dak":
                    orientation = str(item.get("orientatie") or "").strip().lower()
                    if orientation == "horizontaal":
                        add_to_group("dak_plat")
                    else:
                        add_to_group("dak_hellend", include_slope=True)

        for part_group, group in groups.items():
            conn.execute(
                """
                INSERT INTO construction_part_summary
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    xml_file_id,
                    part_group,
                    int(group["count"]),
                    group["area"] or None,
                    group["rc_num"] / group["rc_den"] if group["rc_den"] else None,
                    group["u_num"] / group["u_den"] if group["u_den"] else None,
                    group["g_num"] / group["g_den"] if group["g_den"] else None,
                    group["slope_num"] / group["slope_den"] if group["slope_den"] else None,
                ),
            )

    def insert_request(
        self,
        conn: sqlite3.Connection,
        xml_file_id: int,
        payload: dict[str, Any],
        mapping_warnings: list[str],
    ) -> None:
        solar_panels = payload.get("SolarPanels") or []
        solar_area = sum(_float(panel.get("PVArea")) or 0.0 for panel in solar_panels)
        subtype = payload.get("SubType", payload.get("Subtype"))
        building_kind = "apartment" if subtype is not None else "house"
        conn.execute(
            """
            INSERT INTO api_requests (
                xml_file_id, building_kind, construction_year_category, housing_type,
                subtype, living_area, roof_type, number_of_stories, back_facade,
                wall_insulation, floor_insulation, roof_insulation,
                sloped_roof_insulation, flat_roof_insulation, glass_living_area,
                glass_bedroom_area, installation, shower_heat_recovery, cooling,
                ventilation, solar_panel_count, solar_panel_area_total, payload_json,
                mapping_warnings_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                xml_file_id,
                building_kind,
                payload.get("ConstructionYearCategory"),
                payload.get("HousingType"),
                subtype,
                payload.get("LivingArea"),
                payload.get("RoofType"),
                payload.get("NumberOfStories"),
                payload.get("BackFacade"),
                payload.get("WallInsulation"),
                payload.get("FloorInsulation"),
                payload.get("RoofInsulation"),
                payload.get("SlopedRoofInsulation"),
                payload.get("FlatRoofInsulation"),
                payload.get("GlassLivingArea"),
                payload.get("GlassBedroomArea"),
                payload.get("Installation"),
                payload.get("ShowerHeatRecovery"),
                payload.get("Cooling"),
                payload.get("Ventilation"),
                len(solar_panels),
                solar_area,
                _json(payload),
                _json(mapping_warnings),
            ),
        )

    def insert_response(
        self,
        conn: sqlite3.Connection,
        xml_file_id: int,
        http_status: int | None,
        response_json: dict[str, Any] | None,
    ) -> tuple[float | None, str | None]:
        response = response_json or {}
        current = _first_dict(
            response,
            (
                "Current_House",
                "CurrentHouse",
                "Current_Apartment",
                "CurrentApartment",
                "Current",
            ),
        )
        predicted_beng2 = _float(_first_value(current, ("BENG2", "beng2")))
        predicted_label = _first_value(
            current,
            ("Energy_label", "EnergyLabel", "energy_label", "label", "Label"),
        )
        warnings_json = _first_value(response, ("Warnings", "warnings")) or []
        conn.execute(
            """
            INSERT INTO api_responses
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                xml_file_id,
                http_status,
                predicted_beng2,
                predicted_label,
                _json(response_json) if response_json is not None else None,
                _json(warnings_json),
            ),
        )
        return predicted_beng2, predicted_label

    def insert_comparison(
        self,
        conn: sqlite3.Connection,
        xml_file_id: int,
        xml_beng2: float | None,
        predicted_beng2: float | None,
        xml_label: str | None,
        predicted_label: str | None,
        distance: int | None,
    ) -> None:
        delta = None
        abs_delta = None
        if xml_beng2 is not None and predicted_beng2 is not None:
            delta = predicted_beng2 - xml_beng2
            abs_delta = abs(delta)
        conn.execute(
            """
            INSERT INTO comparisons
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                xml_file_id,
                xml_beng2,
                predicted_beng2,
                delta,
                abs_delta,
                xml_label,
                predicted_label,
                int(xml_label == predicted_label) if xml_label is not None and predicted_label is not None else None,
                distance,
            ),
        )

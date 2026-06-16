import json
from pathlib import Path

import typer

from xml_converter.config import ExtractConfig
from xml_converter.extract.api_builder import build_api_input
from xml_converter.extract.export_raw_fields import export_raw_fields
from xml_converter.extract.export_prediction_input import export_prediction_input
from xml_converter.extract.mapper import map_monitorbestand
from xml_converter.extract.normalizer import normalize_record
from xml_converter.extract.xml_extractors import extract_required_fields
from xml_converter.io.xml_reader import parse_xml
from xml_converter.io.xsd_validator import validate_xml_against_xsd
from xml_converter.validate.batch_runner import run_batch_validation

app = typer.Typer(help="Monitorbestand XML extraction and validation")


@app.command("extract")
def extract_command(
    xml: Path = typer.Option(..., exists=True, file_okay=True, dir_okay=False),
    out: Path = typer.Option(..., file_okay=True, dir_okay=False),
    xsd: Path | None = typer.Option(None, exists=True, file_okay=True, dir_okay=False),
) -> None:
    config = ExtractConfig()

    if xsd is not None and config.validate_xsd:
        validate_xml_against_xsd(xml, xsd)

    tree = parse_xml(xml)
    record = normalize_record(map_monitorbestand(tree))
    export_prediction_input(record, out)

    typer.echo(f"Wrote prediction input to {out}")


@app.command("extract-raw")
def extract_raw_command(
    xml: Path = typer.Option(..., exists=True, file_okay=True, dir_okay=False),
    out: Path | None = typer.Option(None, file_okay=True, dir_okay=False),
    xsd: Path | None = typer.Option(None, exists=True, file_okay=True, dir_okay=False),
    debug_print: bool = typer.Option(False, "--debug-print", help="Print extracted fields to stdout"),
) -> None:
    config = ExtractConfig()

    if xsd is not None and config.validate_xsd:
        validate_xml_against_xsd(xml, xsd)

    tree = parse_xml(xml)
    fields = extract_required_fields(tree)
    if out is not None:
        export_raw_fields(fields, out)
        typer.echo(f"Wrote raw extracted fields to {out}")

    if debug_print:
        typer.echo(json.dumps(fields.to_dict(), indent=2, ensure_ascii=False))


@app.command("build-api-input")
def build_api_input_command(
    xml: Path = typer.Option(..., exists=True, file_okay=True, dir_okay=False),
    out: Path | None = typer.Option(None, file_okay=True, dir_okay=False),
    xsd: Path | None = typer.Option(None, exists=True, file_okay=True, dir_okay=False),
    debug_print: bool = typer.Option(False, "--debug-print", help="Print API input payload to stdout"),
) -> None:
    config = ExtractConfig()

    if xsd is not None and config.validate_xsd:
        validate_xml_against_xsd(xml, xsd)

    tree = parse_xml(xml)
    fields = extract_required_fields(tree)
    payload = build_api_input(fields)

    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        typer.echo(f"Wrote API input to {out}")

    if debug_print:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))


@app.command("validate")
def validate_command(
    xml_dir: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True),
    out: Path = typer.Option(..., file_okay=True, dir_okay=False),
    pattern: str = typer.Option("*.xml"),
) -> None:
    xml_paths = sorted(xml_dir.glob(pattern))
    run_batch_validation(xml_paths, out)
    typer.echo(f"Wrote validation report to {out}")


if __name__ == "__main__":
    app()

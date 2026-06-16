# xml-converter

Python tool for processing Dutch EP-Online monitorbestand XML files.

## Goals

1. Extract reusable input for an energy label prediction tool.
2. Validate API prediction results against values present in monitorbestand XML.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

Run extraction on a single XML:

```powershell
xml-converter extract --xml tests/fixtures/sample_monitorbestand.xml --out out/prediction_input.json
```

Run raw field extraction (stage 1):

```powershell
xml-converter extract-raw --xml "tests/fixtures/1216EZ-62-- (monitor)_anonymized.xml" --out out/raw_fields.json
```

Generate API input JSON (stage 2):

```powershell
xml-converter build-api-input --xml "tests/fixtures/1216EZ-62-- (monitor)_anonymized.xml" --out out/api_input.json
```

Print API input JSON to terminal:

```powershell
xml-converter build-api-input --xml "tests/fixtures/1216EZ-62-- (monitor)_anonymized.xml" --debug-print
```

Print and save at the same time:

```powershell
xml-converter build-api-input --xml "tests/fixtures/1216EZ-62-- (monitor)_anonymized.xml" --out out/api_input.json --debug-print
```

If `xml-converter` is not recognized, run via module:

```powershell
python -m xml_converter.cli build-api-input --xml "tests/fixtures/1216EZ-62-- (monitor)_anonymized.xml" --out out/api_input.json
```

Run validation in batch mode:

```powershell
xml-converter validate --xml-dir tests/fixtures --out out/validation_report.csv
```

Run tests:

```powershell
pytest
```

## Layout

- `src/xml_converter/extract`: reusable extraction pipeline.
- `src/xml_converter/validate`: internal validation pipeline.
- `tests/fixtures`: XML and XSD fixtures.

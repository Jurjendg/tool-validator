# xml-converter: API Input Generator (Current Scope)

This document covers the currently implemented workflow only:

1. Read a monitorbestand XML file
2. Extract/mapping to API input fields
3. Print and/or save API input JSON

It intentionally ignores validation and batch features.

## Prerequisites

- Python 3.12+
- Repository cloned locally

## Setup

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

### Linux/macOS (bash/zsh)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Generate API Input JSON

### Save JSON to file

Windows:

```powershell
xml-converter build-api-input --xml "tests/fixtures/1216EZ-62-- (monitor)_anonymized.xml" --out out/api_input.json
```

Linux/macOS:

```bash
xml-converter build-api-input --xml "tests/fixtures/1216EZ-62-- (monitor)_anonymized.xml" --out out/api_input.json
```

### Print JSON to terminal

Windows:

```powershell
xml-converter build-api-input --xml "tests/fixtures/1216EZ-62-- (monitor)_anonymized.xml" --debug-print
```

Linux/macOS:

```bash
xml-converter build-api-input --xml "tests/fixtures/1216EZ-62-- (monitor)_anonymized.xml" --debug-print
```

### Print and save

```powershell
xml-converter build-api-input --xml "tests/fixtures/1216EZ-62-- (monitor)_anonymized.xml" --out out/api_input.json --debug-print
```

## If `xml-converter` Is Not Found

Run via module (works on all platforms once venv is active):

```powershell
python -m xml_converter.cli build-api-input --xml "tests/fixtures/1216EZ-62-- (monitor)_anonymized.xml" --out out/api_input.json
```

## Output Behavior

- `--debug-print` only: prints JSON to terminal, does not save.
- `--out <path>` only: saves JSON file, does not print full JSON.
- both together: saves and prints.

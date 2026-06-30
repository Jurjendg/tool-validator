# Tool Validator

Validates monitor XML files against a locally running adviestool `/current` API.

The repository contains:

- `main.py`: simple local configuration entry point.
- `toolvalidator/`: validator runner, SQLite storage, API client, and label helpers.
- `xmlConverter/`: XML extraction and mapping code used to build adviestool input.

Raw XML files, SQLite outputs, and local legacy tools are intentionally ignored by Git.

## Usage

Start your production/local adviestool separately, then edit the variables in `main.py`:

```python
XML_DIR = Path("xml-files")
OUT_DB = Path("out/toolvalidator.sqlite")
ADVIESTOOL_BASE_URL = "http://localhost:5000"
BUILDING_KIND = "house"  # or "apartment"
LIMIT: int | None = None
```

Run:

```powershell
python main.py
```

Or use the module CLI:

```powershell
python -m toolvalidator --xml-dir xml-files --out-db out/toolvalidator.sqlite --base-url http://localhost:5000 --no-hash
```

For the apartment adviestool, start that local API and select the apartment builder:

```powershell
python -m toolvalidator --xml-dir xml-files --out-db out/apartments.sqlite --base-url http://localhost:5001 --building-kind apartment --no-hash
```

## Output

The validator writes SQLite tables for extracted XML data, generated `/current` requests, API responses, BENG2/label comparisons, construction-part summaries, and skipped/excluded case counts. Apartment runs store apartment request fields such as subtype, number of stories, back facade, and roof insulation in `api_requests`.

# toolvalidator

Batch-validates monitor XML files against a locally running adviestool `/current` endpoint.

The validator stores one SQLite database per run. It keeps full JSON for the raw XML extraction,
the generated `/current` request, and the adviestool response, plus query-friendly columns for
BENG2 comparison and common filters.

## Run With `main.py`

Edit the variables in the repository root [main.py](../main.py), then run:

```powershell
python main.py
```

The validator only connects to adviestool over HTTP, so adviestool does not need to live in this
repository. Start your production/local adviestool separately and set `ADVIESTOOL_BASE_URL`.

## Run With CLI

Start adviestool locally first, then from the repository root:

```powershell
python -m toolvalidator --xml-dir xml-files --out-db out/toolvalidator.sqlite --base-url http://localhost:5000
```

For the apartment adviestool, point `--base-url` at the locally running apartment API and use the apartment input builder:

```powershell
python -m toolvalidator --xml-dir xml-files --out-db out/apartments.sqlite --base-url http://localhost:5001 --building-kind apartment
```

For a small smoke run:

```powershell
python -m toolvalidator --xml-dir xml-files --out-db out/smoke.sqlite --limit 10
```

Use `--no-hash` to skip SHA-256 hashing on large runs.

## Main Tables

- `xml_files`: one row per XML file and processing status.
- `xml_extracted`: raw XML summary fields, including `xml_beng2`.
- `api_requests`: mapped adviestool `/current` inputs, including apartment fields such as subtype, number of stories, back facade, and roof insulation.
- `api_responses`: adviestool response, predicted BENG2, and warnings.
- `comparisons`: BENG2 deltas and derived-label comparison.
- `roof_parts`, `window_parts`, `ventilation_systems`, `solar_systems`,
  `heating_generators`, `tapwater_systems`, `cooling_systems`: detailed filter tables.

Example:

```sql
select e.opwekkertype_verwarming, r.installation, avg(c.abs_beng2_delta) as avg_abs_delta, count(*) as n
from comparisons c
join xml_extracted e on e.xml_file_id = c.xml_file_id
join api_requests r on r.xml_file_id = c.xml_file_id
group by e.opwekkertype_verwarming, r.installation
order by avg_abs_delta desc;
```

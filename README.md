# RD Territorial System

Sistema territorial y geoespacial reutilizable para la República Dominicana, diseñado para integrarse en proyectos que requieran jerarquía territorial, capas geoespaciales y resolución espacial de eventos.

## v2.0: datos reales

La v2.0 cambia el foco desde la madurez técnica del pipeline hacia la operación con fuentes reales.

### Objetivos de esta versión

- ingerir una fuente real de la ONE en CSV o XLSX;
- construir salidas geoespaciales a partir de la combinación ONE + GADM;
- registrar cobertura real y no-coincidencias;
- permitir reconciliación manual controlada;
- reinyectar esas reconciliaciones al pipeline;
- producir artefactos listos para iterar hasta cobertura nacional usable.

## Flujo recomendado

```bash
python scripts/fetch_gadm.py
python scripts/profile_one_source.py
python scripts/build_v2_0.py
```

Si aparecen no-coincidencias o matches débiles, completa:

```bash
data/reconciliation/municipality_overrides.csv
```

y vuelve a ejecutar:

```bash
python scripts/build_v2_0.py
```

## Salidas principales

- `data/processed/provinces.geojson`
- `data/processed/municipalities.geojson`
- `data/processed/territorial_master.csv`
- `data/processed/match_report.csv`
- `data/processed/coverage_report.csv`
- `data/processed/ingestion_report.json`
- `data/processed/unmatched_municipalities.csv`
- `data/processed/low_confidence_matches.csv`

## Autor

Edwin José Nolasco

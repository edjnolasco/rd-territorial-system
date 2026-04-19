# RD Territorial System

Sistema territorial y geoespacial reutilizable para la República Dominicana, concebido como una librería y paquete de datos que puede integrarse en cualquier proyecto que requiera normalización territorial, jerarquía administrativa, consulta de capas y resolución espacial de eventos.

## Enfoque de la v1.0

La v1.0 fortalece la ingestión operativa para fuentes de la ONE en Excel:

- soporte para **CSV y XLSX**;
- selección automática de hoja cuando el archivo Excel tiene múltiples sheets;
- selección explícita por nombre de hoja cuando se necesite;
- perfilado de columnas detectadas y usadas;
- reporte técnico del proceso de ingestión;
- continuidad del flujo ONE + GADM con cobertura y matching.

## Ejecución

```bash
python scripts/fetch_gadm.py
python scripts/build_v1_0.py
```

## Salidas

- `data/processed/provinces.geojson`
- `data/processed/municipalities.geojson`
- `data/processed/territorial_master.csv`
- `data/processed/match_report.csv`
- `data/processed/coverage_report.csv`
- `data/processed/ingestion_report.json`
- `data/processed/district_municipals.csv` (si existe la fuente)

## Autor

Edwin José Nolasco

# Excel multi-sheet support (v1.0)

La v1.0 agrega soporte real para archivos Excel con varias hojas.

## Comportamiento

- si el archivo fuente es CSV, se carga directamente;
- si es XLSX y no se especifica hoja, el sistema perfila todas las hojas;
- selecciona la hoja con mejor puntuación según:
  - presencia de columnas semánticas de provincia;
  - presencia de columnas semánticas de municipio;
  - volumen de filas.

## Selección explícita

También puedes forzar la hoja:

```bash
python scripts/build_v1_0.py --sheet-name "División Territorial"
```

## Reporte técnico

`ingestion_report.json` registra:
- archivo fuente usado;
- tipo de archivo;
- hoja seleccionada;
- perfiles por hoja;
- columnas originales;
- columnas mapeadas;
- filas de entrada;
- pares únicos usados;
- filas con match municipal.

# Municipality overrides

Cuando un municipio de la fuente ONE no haga match directo o difuso confiable con GADM, puedes declarar una reconciliación manual.

## Archivo

`data/reconciliation/municipality_overrides.csv`

## Columnas

- `province_name`
- `municipality_name`
- `gadm_municipality_name`

## Ejemplo

```csv
province_name,municipality_name,gadm_municipality_name
Distrito Nacional,Santo Domingo de Guzmán,Santo Domingo de Guzman
```

Estos overrides tienen prioridad sobre el matching automático.

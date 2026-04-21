# v2.0 real data workflow

## 1. Colocar fuente ONE real

Coloca en `data/raw/one/` un archivo `.csv` o `.xlsx` con columnas equivalentes a provincia y municipio.

## 2. Perfilar la fuente

```bash
python scripts/profile_one_source.py
```

## 3. Descargar GADM

```bash
python scripts/fetch_gadm.py
```

## 4. Construir salidas

```bash
python scripts/build_v2_0.py
```

## 5. Revisar problemas

- `data/processed/unmatched_municipalities.csv`
- `data/processed/low_confidence_matches.csv`

## 6. Aplicar overrides

Edita `data/reconciliation/municipality_overrides.csv` y vuelve a ejecutar el build.

## 7. Repetir hasta cobertura usable

La idea de v2.0 no es asumir cobertura perfecta de entrada, sino dejar una mecánica controlada para converger hacia cobertura nacional real.

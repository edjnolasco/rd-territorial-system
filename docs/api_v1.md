# RD Territorial System — API v1 OpenAPI-Ready Contract

## 1. Propósito

Esta especificación define el contrato formal de la API v1 del motor de resolución territorial de la República Dominicana.

La API se concibe como un servicio centralizado. Los SDKs de Python, JavaScript, C# u otros lenguajes deben consumir este contrato HTTP y no duplicar la lógica territorial.

---

## 2. Principios de resolución

- `name` funciona como búsqueda exploratoria.
- `name + level` puede devolver `ambiguous`.
- `name + level + parent_code` permite resolución contextual determinista.
- `composite_code` es la identidad absoluta.
- Los alias normalizan la entrada, pero no eliminan ambigüedad legítima.
- `ambiguous` no es un error en modo no estricto; es un resultado válido.

---

## 3. Estados oficiales

```text
matched
ambiguous
not_found
invalid_input
```

---

## 4. Niveles soportados

```text
province
municipality
district_municipal
section
barrio_paraje
sub_barrio
toponym
```

---

## 5. Endpoints v1

```text
GET  /api/v1/health
GET  /api/v1/catalog/stats
GET  /api/v1/entities/{composite_code}
GET  /api/v1/entities/{composite_code}/children
GET  /api/v1/provinces/{province_code}/entities
POST /api/v1/resolve
POST /api/v1/batch-resolve
POST /api/v1/search
POST /api/v1/explain
```

---

## 6. Modelos Pydantic recomendados

```python
from typing import Literal

from pydantic import BaseModel, Field


Level = Literal[
    "province",
    "municipality",
    "district_municipal",
    "section",
    "barrio_paraje",
    "sub_barrio",
    "toponym",
]

Status = Literal[
    "matched",
    "ambiguous",
    "not_found",
    "invalid_input",
]


class ResolveRequest(BaseModel):
    text: str = Field(..., min_length=1, examples=["Brisas del Norte"])
    level: Level | None = Field(default=None, examples=["sub_barrio"])
    parent_code: str | None = Field(
        default=None,
        examples=["10-01-01-01-01-001-00"],
    )
    strict: bool = Field(default=False)
    rules_version: str = Field(default="v1")


class BatchResolveRequest(BaseModel):
    items: list[str] = Field(..., min_length=1, max_length=100)
    level: Level | None = None
    parent_code: str | None = None
    strict: bool = False
    rules_version: str = "v1"


class SearchRequest(BaseModel):
    text: str = Field(..., min_length=1)
    level: Level | None = None
    parent_code: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class TerritorialEntityResponse(BaseModel):
    composite_code: str
    parent_composite_code: str | None = None
    name: str
    official_name: str | None = None
    normalized_name: str | None = None
    level: Level
    region_code: str
    province_code: str
    municipality_code: str
    district_municipal_code: str
    section_code: str
    barrio_paraje_code: str
    sub_barrio_code: str
    full_path: str
    parent_path: list[str] = []


class ResolveResponse(BaseModel):
    input: str
    normalized_text: str | None
    matched: bool
    status: Status
    confidence: float
    match_strategy: str
    canonical_name: str | None = None
    entity_id: str | None = None
    entity_type: Level | None = None
    entity: TerritorialEntityResponse | None = None
    candidates: list[TerritorialEntityResponse] = []
    trace: list[str] = []
    rules_version: str = "v1"


class SearchResponse(BaseModel):
    input: str
    normalized_text: str | None
    count: int
    items: list[TerritorialEntityResponse]


class HealthResponse(BaseModel):
    status: str
    service: str
    api_version: str
    catalog_format: str
    catalog_loaded: bool


class CatalogStatsResponse(BaseModel):
    catalog_version: str
    country: str
    province_count: int
    entity_count: int
    levels: dict[str, int]
    source_of_truth: str
```

---

## 7. GET /api/v1/health

### Objetivo

Verificar que la API está viva y que el catálogo cargó correctamente.

### Response 200

```json
{
  "status": "ok",
  "service": "rd-territorial-system",
  "api_version": "v1",
  "catalog_format": "csv",
  "catalog_loaded": true
}
```

---

## 8. GET /api/v1/catalog/stats

### Objetivo

Exponer métricas del catálogo cargado en memoria.

### Response 200

```json
{
  "catalog_version": "current",
  "country": "República Dominicana",
  "province_count": 32,
  "entity_count": 20773,
  "levels": {
    "province": 32,
    "municipality": 158,
    "district_municipal": 393,
    "section": 1599,
    "barrio_paraje": 12810,
    "sub_barrio": 5781
  },
  "source_of_truth": "csv"
}
```

---

## 9. GET /api/v1/entities/{composite_code}

### Objetivo

Resolver una entidad por identidad absoluta.

### Request

```text
GET /api/v1/entities/10-01-01-01-01-001-03
```

### Response 200

```json
{
  "matched": true,
  "status": "matched",
  "entity": {
    "composite_code": "10-01-01-01-01-001-03",
    "parent_composite_code": "10-01-01-01-01-001-00",
    "name": "Brisas del Norte",
    "official_name": "Brisas del Norte",
    "normalized_name": "brisas del norte",
    "level": "sub_barrio",
    "region_code": "10",
    "province_code": "01",
    "municipality_code": "01",
    "district_municipal_code": "01",
    "section_code": "01",
    "barrio_paraje_code": "001",
    "sub_barrio_code": "03",
    "full_path": "Distrito Nacional > Santo Domingo de Guzmán > Santo Domingo de Guzmán > Santo Domingo de Guzmán (Zona urbana) > Los Peralejos > Brisas del Norte",
    "parent_path": [
      "Distrito Nacional",
      "Santo Domingo de Guzmán",
      "Santo Domingo de Guzmán",
      "Santo Domingo de Guzmán (Zona urbana)",
      "Los Peralejos"
    ]
  }
}
```

### Response 404

```json
{
  "matched": false,
  "status": "not_found",
  "entity": null,
  "message": "No territorial entity found for composite_code."
}
```

---

## 10. GET /api/v1/entities/{composite_code}/children

### Objetivo

Obtener hijos directos de una entidad territorial.

### Query params

```text
level: optional
limit: optional, default 100, max 1000
```

### Request

```text
GET /api/v1/entities/10-01-01-01-01-001-00/children?level=sub_barrio
```

### Response 200

```json
{
  "parent_code": "10-01-01-01-01-001-00",
  "count": 1,
  "items": [
    {
      "composite_code": "10-01-01-01-01-001-03",
      "parent_composite_code": "10-01-01-01-01-001-00",
      "name": "Brisas del Norte",
      "level": "sub_barrio",
      "province_code": "01",
      "full_path": "Distrito Nacional > Santo Domingo de Guzmán > Santo Domingo de Guzmán > Santo Domingo de Guzmán (Zona urbana) > Los Peralejos > Brisas del Norte",
      "parent_path": [
        "Distrito Nacional",
        "Santo Domingo de Guzmán",
        "Santo Domingo de Guzmán",
        "Santo Domingo de Guzmán (Zona urbana)",
        "Los Peralejos"
      ]
    }
  ]
}
```

---

## 11. GET /api/v1/provinces/{province_code}/entities

### Objetivo

Obtener entidades por provincia, con filtro opcional por nivel.

### Query params

```text
level: optional
limit: optional, default 1000, max 5000
```

### Request

```text
GET /api/v1/provinces/01/entities?level=barrio_paraje
```

### Response 200

```json
{
  "province_code": "01",
  "count": 1,
  "items": [
    {
      "composite_code": "10-01-01-01-01-001-00",
      "name": "Los Peralejos",
      "level": "barrio_paraje",
      "province_code": "01",
      "full_path": "Distrito Nacional > Santo Domingo de Guzmán > Santo Domingo de Guzmán > Santo Domingo de Guzmán (Zona urbana) > Los Peralejos"
    }
  ]
}
```

---

## 12. POST /api/v1/resolve

### Objetivo

Resolver texto a una entidad territorial.

### Request

```json
{
  "text": "Brisas del Norte",
  "level": "sub_barrio",
  "parent_code": "10-01-01-01-01-001-00",
  "strict": false,
  "rules_version": "v1"
}
```

### Response 200 — matched

```json
{
  "input": "Brisas del Norte",
  "normalized_text": "brisas del norte",
  "matched": true,
  "status": "matched",
  "confidence": 1.0,
  "match_strategy": "exact_catalog",
  "canonical_name": "Brisas del Norte",
  "entity_id": "10-01-01-01-01-001-03",
  "entity_type": "sub_barrio",
  "entity": {
    "composite_code": "10-01-01-01-01-001-03",
    "parent_composite_code": "10-01-01-01-01-001-00",
    "name": "Brisas del Norte",
    "level": "sub_barrio",
    "province_code": "01",
    "full_path": "Distrito Nacional > Santo Domingo de Guzmán > Santo Domingo de Guzmán > Santo Domingo de Guzmán (Zona urbana) > Los Peralejos > Brisas del Norte"
  },
  "candidates": [],
  "trace": [
    "normalized input -> 'brisas del norte'",
    "matched sub_barrio by normalized_name"
  ],
  "rules_version": "v1"
}
```

### Response 200 — ambiguous

```json
{
  "input": "Los Peralejos",
  "normalized_text": "los peralejos",
  "matched": false,
  "status": "ambiguous",
  "confidence": 0.0,
  "match_strategy": "exact_catalog",
  "canonical_name": null,
  "entity_id": null,
  "entity_type": null,
  "entity": null,
  "candidates": [
    {
      "composite_code": "10-01-01-01-01-001-00",
      "parent_composite_code": "10-01-01-01-01-000-00",
      "name": "Los Peralejos",
      "level": "barrio_paraje",
      "province_code": "01",
      "full_path": "Distrito Nacional > Santo Domingo de Guzmán > Santo Domingo de Guzmán > Santo Domingo de Guzmán (Zona urbana) > Los Peralejos"
    }
  ],
  "trace": [
    "normalized input -> 'los peralejos'",
    "ambiguous match: multiple candidates"
  ],
  "rules_version": "v1"
}
```

### Response 200 — not_found

```json
{
  "input": "Sector Inventado",
  "normalized_text": "sector inventado",
  "matched": false,
  "status": "not_found",
  "confidence": 0.0,
  "match_strategy": "exact_catalog",
  "canonical_name": null,
  "entity_id": null,
  "entity_type": null,
  "entity": null,
  "candidates": [],
  "trace": [
    "normalized input -> 'sector inventado'",
    "no candidates found in catalog"
  ],
  "rules_version": "v1"
}
```

---

## 13. POST /api/v1/batch-resolve

### Objetivo

Resolver múltiples entradas con un mismo contexto opcional.

### Límite recomendado

```text
max_items = 100
```

### Request

```json
{
  "items": [
    "DN",
    "Brisas del Norte",
    "Villa María"
  ],
  "level": "sub_barrio",
  "parent_code": null,
  "strict": false,
  "rules_version": "v1"
}
```

### Response 200

```json
[
  {
    "input": "DN",
    "matched": false,
    "status": "not_found",
    "entity": null,
    "candidates": []
  },
  {
    "input": "Brisas del Norte",
    "matched": false,
    "status": "ambiguous",
    "entity": null,
    "candidates": []
  },
  {
    "input": "Villa María",
    "matched": false,
    "status": "ambiguous",
    "entity": null,
    "candidates": []
  }
]
```

---

## 14. POST /api/v1/search

### Objetivo

Buscar candidatos sin exigir resolución final. Útil para autocomplete y UI.

### Request

```json
{
  "text": "Los Peralejos",
  "level": "barrio_paraje",
  "parent_code": null,
  "limit": 20
}
```

### Response 200

```json
{
  "input": "Los Peralejos",
  "normalized_text": "los peralejos",
  "count": 3,
  "items": [
    {
      "composite_code": "10-01-01-01-01-001-00",
      "name": "Los Peralejos",
      "level": "barrio_paraje",
      "province_code": "01",
      "full_path": "Distrito Nacional > Santo Domingo de Guzmán > Santo Domingo de Guzmán > Santo Domingo de Guzmán (Zona urbana) > Los Peralejos"
    }
  ]
}
```

---

## 15. POST /api/v1/explain

### Objetivo

Resolver igual que `/resolve`, pero exponiendo trazabilidad ampliada.

### Request

```json
{
  "text": "DN",
  "level": "province",
  "parent_code": null,
  "rules_version": "v1"
}
```

### Response 200

```json
{
  "input": "DN",
  "normalized_text": "distrito nacional",
  "matched": true,
  "status": "matched",
  "match_strategy": "exact_catalog",
  "entity": {
    "name": "Distrito Nacional",
    "level": "province",
    "composite_code": "10-01-00-00-00-000-00"
  },
  "candidates": [],
  "trace": [
    "normalized input -> 'dn'",
    "applied alias -> 'distrito nacional'",
    "searched level -> province",
    "matched province by normalized_name"
  ],
  "rules_version": "v1"
}
```

---

## 16. Política HTTP

### Modo no estricto (`strict=false`)

```text
200 → matched
200 → ambiguous
200 → not_found
200 → invalid_input
```

### Modo estricto (`strict=true`)

```text
200 → matched
404 → not_found
409 → ambiguous
422 → invalid_input
```

### Error 409

```json
{
  "detail": {
    "status": "ambiguous",
    "message": "Multiple territorial entities match the input.",
    "candidate_count": 7
  }
}
```

---

## 17. Contrato de SDK

Todos los SDKs deben exponer:

```text
resolve()
batch_resolve()
search()
explain()
get_entity()
get_children()
get_by_province()
health()
stats()
```

### Python

```python
client.resolve(
    "Brisas del Norte",
    level="sub_barrio",
    parent_code="10-01-01-01-01-001-00",
)
```

### JavaScript

```javascript
client.resolve("Brisas del Norte", {
  level: "sub_barrio",
  parentCode: "10-01-01-01-01-001-00"
});
```

### C#

```csharp
await client.ResolveAsync(
    "Brisas del Norte",
    level: "sub_barrio",
    parentCode: "10-01-01-01-01-001-00"
);
```

---

## 18. Decisiones congeladas para v1

1. CSV es la fuente única del catálogo.
2. El catálogo se carga en memoria al iniciar.
3. `composite_code` es identidad absoluta.
4. `parent_code` es el mecanismo oficial de desambiguación.
5. Alias normaliza entrada, pero no resuelve ambigüedad.
6. `ambiguous` no es error en modo no estricto.
7. `full_path` debe estar presente en candidatos.
8. Batch resolve no debe ocultar ambigüedad.
9. Los SDKs no implementan lógica territorial; solo consumen API HTTP.

---

## 19. Orden recomendado de implementación

1. Crear schemas Pydantic v1.
2. Refactorizar `api/main.py` para usar schemas.
3. Garantizar OpenAPI limpio en `/docs`.
4. Añadir `GET /health`.
5. Añadir `GET /catalog/stats`.
6. Añadir `GET /entities/{composite_code}`.
7. Añadir `GET /entities/{composite_code}/children`.
8. Añadir `GET /provinces/{province_code}/entities`.
9. Añadir `POST /search`.
10. Actualizar tests API.
11. Congelar este documento como `docs/api_v1.md`.

---

## 20. Source of Truth

```text
data/catalog/current/rd_territorial_master.csv
```

El archivo CSV:

- se versiona por Git,
- no se modifica en runtime,
- se carga en memoria al iniciar el servicio,
- se indexa por estructuras internas del resolver.

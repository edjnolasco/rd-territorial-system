# 🇩🇴 rd-territorial-system

> Deterministic territorial resolution engine for the Dominican Republic  
> **Powered by Nancy**

Motor determinístico de resolución territorial para República Dominicana.

Permite transformar texto no estructurado en entidades territoriales normalizadas (provincias, municipios, distritos municipales, secciones, barrios y sub-barrios) con alta precisión y rendimiento en memoria.

---

## 🎯 ¿Qué es esto?

`rd-territorial-system` es:

> Una capa de infraestructura para normalizar ubicaciones territoriales en sistemas reales.

No es un script. No es un dataset.

Es un **motor reusable** diseñado para:

- Fintech (validación de direcciones)
- Logística (normalización de ubicaciones)
- DSS (riesgo, accidentes, crimen)
- BI / Analytics (limpieza de datos)

---

## 🚀 Uso como librería (RECOMENDADO)

Instalación:

```bash
pip install rd-territorial-system
```
---

Resolución simple
```bash
from rd_territorial_system import resolve

result = resolve("SDE")

print(result)
```
---

Ejemplo de salida:

```python
{
  "status": "matched",
  "canonical_name": "Santo Domingo Este",
  "entity_type": "district_municipal",
  "confidence": 0.852,
  "catalog_version": "v1.0.0"
}
```
---

Resolución en lote
```python
from rd_territorial_system import batch_resolve

results = batch_resolve(["SDN", "Villa Mella"])
```
---

🧠 Características del motor
Resolución determinística (no ML)
Índices en memoria
Matching jerárquico
Manejo de ambigüedad
Normalización robusta
Catálogo versionado (~20k entidades)

---

📦 Uso avanzado (motor)
```python
from rd_territorial_system import resolve_name

resolve_name("Azua", level="province")
```
---

🌐 Uso como API

Ejecutar local
```bash
uvicorn app.main:app --reload
```

Docs:

http://localhost:8000/docs

---

Ejemplo request
```bash
curl -X POST http://localhost:8000/api/v1/resolve \
  -H "Content-Type: application/json" \
  -d '{"text": "Azua", "level": "province"}'
```
---  

🔒 Seguridad
API Keys
Scopes por endpoint
Identificación de cliente
Rate limiting por cliente

---  

⚙️ Rate Limiting
Memory (dev)
Redis (producción)
HTTP 429 automático

--- 

📊 Observabilidad

Cada request incluye:

request_id
client_id
api_key_hash

--- 

📦 Catálogo
32 provincias
~20,000 entidades
jerarquía completa
versionado (catalog_version)

--- 

🧪 Testing

```bash
python -m pytest

```
---

🧱 Arquitectura

Cliente (DSS / App / API)
        │
        ▼
Core Library (resolve / batch_resolve)
        │
        ▼
FastAPI Layer (opcional)
        │
        ▼
Catálogo territorial (in-memory)

---

⚙️ Tecnología

Este sistema está construido sobre Nancy, un motor de resolución y procesamiento de datos diseñado para:

sistemas DSS
procesamiento geoespacial
pipelines determinísticos
motores de decisión

Nancy actúa como núcleo de ejecución para múltiples soluciones reutilizables.

---

📁 Estructura

src/rd_territorial_system/
  core/
  api/
  catalog.py
  rules/
  parsers/

data/
  catalog/
  processed/

data_pipeline/
  raw/

examples/

---

🔭 Casos de uso
Normalización de direcciones
Sistemas DSS territoriales
Limpieza de datos geográficos
Integración con APIs externas
Validación en formularios

---

📌 Diseño
Sin dependencias externas para resolver
Latencia mínima (in-memory)
Reproducible (determinístico)
Portable (pip install)

---

👤 Autor

Edwin José Nolasco
PhD (c) Artificial Intelligence & Machine Learning
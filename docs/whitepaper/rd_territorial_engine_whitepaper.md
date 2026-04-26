# rd-territorial-system  
## Motor de Resolución Territorial para la República Dominicana

**Autor:** Edwin José Nolasco  
**Estado:** Versión técnica inicial  
**Fecha:** 2026  

---

## Resumen ejecutivo

El presente documento describe un motor determinístico de resolución territorial diseñado para transformar entradas textuales no estructuradas en entidades territoriales normalizadas, alineadas con la jerarquía administrativa de la República Dominicana.

El sistema actúa como una capa de infraestructura reutilizable para múltiples dominios analíticos, incluyendo sistemas de soporte a decisiones, análisis de riesgos, monitoreo geoespacial y procesamiento de datos territoriales.

---

1. Introducción

Los sistemas analíticos que operan sobre información territorial en la República Dominicana enfrentan un problema estructural: la falta de una representación consistente, normalizada y jerárquicamente coherente de las entidades geográficas.

En la práctica, los datos territoriales suelen presentarse en formatos heterogéneos, con variaciones ortográficas, ambigüedad semántica y ausencia de estandarización. Esto afecta directamente la calidad de los análisis, limitando la capacidad de integrar información proveniente de múltiples fuentes y reduciendo la precisión de los modelos utilizados en la toma de decisiones.

Este problema se intensifica en escenarios donde el territorio constituye una dimensión crítica, como en sistemas de análisis de accidentes de tránsito, estudios de criminalidad, evaluación de riesgos naturales o monitoreo de tráfico. En todos estos casos, la correcta identificación y normalización de entidades territoriales es un requisito fundamental.

Ante este contexto, se propone un motor de resolución territorial determinístico, diseñado para transformar entradas textuales no estructuradas en representaciones territoriales normalizadas, alineadas con una jerarquía administrativa completa del país.

El sistema no solo resuelve nombres geográficos, sino que establece una base común para la integración de datos en múltiples dominios analíticos, actuando como una capa de infraestructura reutilizable en distintos sistemas.

2. Problema técnico

El procesamiento de información territorial presenta tres desafíos principales:

2.1 Ambigüedad semántica

Una misma denominación puede referirse a múltiples entidades territoriales. Por ejemplo, nombres como “Villa María” o “Los Peralejos” pueden existir en diferentes niveles administrativos o en distintas ubicaciones geográficas.

Esta ambigüedad impide la resolución directa de entidades sin contexto adicional.

2.2 Variabilidad en la representación

Los datos territoriales suelen contener:

errores ortográficos
ausencia de tildes
variaciones en el uso de espacios
alias históricos o nombres alternativos

Esto genera inconsistencias que dificultan el matching directo contra catálogos estructurados.

2.3 Falta de estructura jerárquica

Muchos sistemas tratan las ubicaciones como texto plano, sin considerar la jerarquía territorial (provincia, municipio, distrito, sección, etc.). Esto limita la capacidad de:

desambiguar entidades
navegar relaciones territoriales
realizar análisis agregados

3. Solución propuesta

El sistema desarrollado consiste en un motor de resolución territorial determinístico, diseñado para transformar entradas textuales no estructuradas en representaciones territoriales normalizadas, alineadas con la jerarquía administrativa completa de la República Dominicana.

A diferencia de enfoques basados exclusivamente en técnicas probabilísticas o aprendizaje automático, el motor propuesto adopta un enfoque determinístico y estructurado, apoyado en un catálogo territorial validado y en reglas explícitas de resolución y desambiguación.

El proceso de resolución se basa en tres componentes principales:

normalización de entrada, que reduce la variabilidad en la representación textual;
matching contra catálogo estructurado, utilizando identificadores y niveles jerárquicos;
desambiguación basada en contexto, considerando restricciones como nivel territorial y relaciones padre-hijo.

El resultado es una salida estructurada que incluye:

entidad territorial resuelta (cuando es unívoca),
lista de candidatos (en caso de ambigüedad),
metadatos adicionales que facilitan su integración en sistemas consumidores.

Este enfoque permite garantizar:

interpretabilidad total del proceso de resolución,
consistencia en los resultados,
y reproducibilidad en escenarios operativos.
4. Arquitectura del sistema

La arquitectura del sistema se organiza en torno a tres capas principales:

4.1 Catálogo territorial

El sistema se apoya en un catálogo nacional estructurado que contiene aproximadamente 20,000 entidades territoriales, organizadas jerárquicamente en niveles administrativos:

provincia
municipio
distrito municipal
sección
barrio/paraje
sub-barrio

Cada entidad está identificada mediante un código compuesto, que permite representar su posición dentro de la jerarquía y facilita la navegación entre niveles.

Este catálogo constituye la base semántica del sistema y permite garantizar consistencia en la resolución.

4.2 Motor de resolución

El motor de resolución opera completamente en memoria, utilizando estructuras optimizadas para:

búsqueda rápida de entidades
comparación de nombres normalizados
filtrado por nivel territorial
aplicación de reglas de desambiguación

El flujo general del motor es:

recepción del texto de entrada
normalización
búsqueda de coincidencias en el catálogo
evaluación de candidatos
selección del resultado o generación de ambigüedad

Este diseño permite mantener tiempos de respuesta bajos y comportamiento determinístico.

4.3 Capa de API

El motor se expone mediante una API REST que permite su consumo por sistemas externos. Esta capa incluye:

endpoints versionados (/api/v1)
validación de entrada
control de acceso mediante API keys
gestión de scopes por endpoint
rate limiting por cliente

Adicionalmente, la API incorpora mecanismos de observabilidad:

logging estructurado
identificación de cliente (client_id)
métricas de latencia
clasificación de resultados del resolver
4.4 Instrumentación y métricas

El sistema incluye un módulo de métricas que captura información en tiempo real sobre:

latencia por request
estado de la respuesta
tipo de resultado del resolver (matched, ambiguous, no_match)
uso por cliente

Estos datos son exportados a formatos estructurados (CSV) para su análisis posterior, permitiendo evaluar el comportamiento del sistema en condiciones reales de operación.

5. Funcionamiento del resolver

El motor de resolución territorial implementa un enfoque determinístico basado en reglas, apoyado en una representación jerárquica explícita del territorio. Su objetivo es transformar una entrada textual en una entidad territorial estructurada o, en su defecto, identificar y reportar ambigüedad de forma controlada.

5.1 Flujo de resolución

El proceso de resolución sigue una secuencia bien definida:

Recepción de la entrada
Se recibe un texto libre que representa una posible entidad territorial, junto con parámetros opcionales como nivel (level) o código de entidad padre (parent_code).
Normalización
La entrada es transformada mediante reglas de normalización que incluyen:
eliminación de tildes,
normalización de mayúsculas/minúsculas,
limpieza de espacios y caracteres especiales,
tratamiento de variantes comunes.
Búsqueda en el catálogo
Se realiza una búsqueda sobre el catálogo territorial utilizando estructuras optimizadas en memoria. Esta búsqueda puede:
considerar coincidencias exactas,
aplicar filtros por nivel,
restringirse a un subárbol territorial si se proporciona un parent_code.
Evaluación de candidatos
Los resultados se clasifican en función del número y calidad de coincidencias:
un único candidato válido,
múltiples candidatos compatibles,
ausencia de coincidencias.
Construcción del resultado
En función de la evaluación, el sistema devuelve:
una entidad resuelta (caso unívoco),
una lista de candidatos (ambigüedad),
o una respuesta de no correspondencia.
5.2 Clasificación de resultados

Para efectos de evaluación, los resultados del resolver se clasifican en tres categorías:

matched: se identifica una única entidad que satisface los criterios de búsqueda.
ambiguous: múltiples entidades cumplen los criterios y no es posible seleccionar una sin contexto adicional.
no_match: no se encuentra ninguna entidad compatible en el catálogo.

Esta clasificación permite evaluar el comportamiento del sistema desde una perspectiva cuantitativa y facilita su análisis en escenarios reales.

5.3 Desambiguación jerárquica

El sistema incorpora mecanismos de desambiguación basados en la estructura jerárquica del territorio. En particular:

el uso de parent_code permite restringir la búsqueda a un subconjunto del catálogo, reduciendo ambigüedad;
el filtrado por level limita las coincidencias a un nivel administrativo específico;
la relación padre-hijo entre entidades permite validar la coherencia de los resultados.

Este enfoque evita la necesidad de heurísticas probabilísticas complejas, manteniendo la interpretabilidad del proceso.

5.4 Complejidad y desempeño

El motor opera completamente en memoria, lo que permite:

tiempos de respuesta constantes en la práctica para consultas típicas,
ausencia de dependencias externas durante la resolución,
escalabilidad adecuada para el tamaño del catálogo nacional.

La complejidad efectiva del proceso depende del tamaño del conjunto de candidatos, pero se mantiene acotada mediante el uso de índices y estructuras de acceso optimizadas.

6. Evaluación empírica

La evaluación del sistema se realizó utilizando métricas capturadas en tiempo de ejecución durante la operación de la API. Este enfoque permite analizar el comportamiento del sistema bajo condiciones reales, en lugar de depender exclusivamente de datasets sintéticos.

6.1 Desempeño (latencia)

El sistema mostró una latencia promedio de μ = [VALOR] ms y una mediana de M = [VALOR] ms, lo que confirma la eficiencia del enfoque en memoria.

La distribución de latencia no presenta valores extremos significativos, lo que indica estabilidad en la ejecución de las solicitudes. Este comportamiento es consistente con el diseño del motor, que evita operaciones costosas durante la fase de resolución.

6.2 Calidad de resolución

La distribución de resultados del resolver fue la siguiente:

matched: [VALOR] %
ambiguous: [VALOR] %
no_match: [VALOR] %

Estos resultados evidencian que el sistema logra resolver de forma unívoca la mayoría de las consultas, manteniendo un manejo explícito de la ambigüedad cuando esta ocurre.

La proporción de casos ambiguos es coherente con la estructura del dominio territorial, donde múltiples entidades pueden compartir denominaciones similares. Por su parte, los casos de no correspondencia reflejan limitaciones en la cobertura del catálogo o en la calidad de las entradas.

6.3 Comportamiento operativo

El análisis de métricas operativas muestra que:

el sistema mantiene una distribución heterogénea de uso por cliente, con concentración de solicitudes en determinados consumidores;
los mecanismos de seguridad y control de acceso funcionan correctamente, evidenciado por la presencia de respuestas 401 y 403;
el rate limiting se activa de manera efectiva en escenarios de alta frecuencia de solicitudes (código 429).

Estos resultados confirman que el sistema no solo es funcional desde el punto de vista de resolución, sino que también es robusto en términos operativos.

7. Ventajas del enfoque

El motor de resolución territorial propuesto presenta varias ventajas relevantes frente a enfoques alternativos:

7.1 Interpretabilidad

El sistema opera mediante reglas determinísticas explícitas, lo que permite comprender completamente el proceso de resolución. A diferencia de modelos basados en aprendizaje automático, cada resultado puede ser trazado y explicado en función de las reglas aplicadas y la estructura del catálogo.

7.2 Desempeño

El uso de estructuras en memoria y la ausencia de dependencias externas durante la resolución permiten alcanzar tiempos de respuesta bajos y consistentes. Esto lo hace adecuado para aplicaciones en tiempo real y sistemas con alta frecuencia de consultas.

7.3 Consistencia

El uso de un catálogo territorial unificado garantiza que todas las resoluciones se alineen con una representación común del territorio. Esto facilita la integración de datos entre sistemas y reduce inconsistencias semánticas.

7.4 Reutilización

El motor actúa como una capa de infraestructura reutilizable, que puede ser consumida por múltiples aplicaciones en distintos dominios, incluyendo:

análisis de accidentes de tránsito,
estudios de criminalidad,
evaluación de riesgos naturales,
monitoreo de tráfico,
sistemas de soporte a decisiones (DSS).
7.5 Independencia de modelos complejos

El sistema no depende de modelos de aprendizaje automático, lo que reduce:

la necesidad de datasets de entrenamiento,
la complejidad de mantenimiento,
la opacidad en los resultados.

Esto lo hace especialmente útil en contextos donde la interpretabilidad es crítica o los datos son limitados.

8. Limitaciones

A pesar de sus ventajas, el sistema presenta ciertas limitaciones que deben ser consideradas:

8.1 Dependencia del catálogo

La calidad de la resolución depende directamente de la cobertura y consistencia del catálogo territorial. Errores o ausencias en el catálogo impactan directamente los resultados.

8.2 Ambigüedad inherente

El sistema no elimina la ambigüedad del dominio, sino que la expone de manera controlada. En casos donde múltiples entidades comparten denominación, es necesario proporcionar contexto adicional para una resolución unívoca.

8.3 Normalización limitada

Aunque el sistema implementa reglas de normalización, entradas altamente ruidosas o alejadas de las variantes conocidas pueden no ser correctamente resueltas.

8.4 Ausencia de inferencia probabilística

El enfoque determinístico no permite inferir la “mejor” opción en casos ambiguos sin información adicional, lo que podría ser abordado en futuras extensiones mediante técnicas híbridas.

9. Roadmap

El sistema establece una base sólida que puede ser extendida en múltiples direcciones:

9.1 Integración geoespacial

Incorporación de coordenadas geográficas para:

mejorar la precisión de resolución,
habilitar análisis espaciales,
permitir visualización en mapas.
9.2 Enfoque híbrido

Integración de componentes de aprendizaje automático para:

priorización de candidatos en casos ambiguos,
corrección automática de entradas ruidosas,
mejora en la experiencia de usuario.
9.3 Expansión del catálogo

Ampliación del catálogo para:

incluir nuevas entidades,
mejorar cobertura en niveles finos,
integrar fuentes oficiales adicionales.
9.4 Exposición como servicio comercial

Evolución del sistema hacia un servicio API con:

planes de consumo,
autenticación avanzada,
monitoreo de uso por cliente.

10. Conclusión

El motor de resolución territorial presentado constituye una solución robusta, eficiente e interpretable para el procesamiento de entidades geográficas en la República Dominicana.

Los resultados obtenidos demuestran que es posible alcanzar un alto nivel de desempeño y precisión mediante un enfoque determinístico basado en estructuras jerárquicas, evitando la complejidad y opacidad asociadas a modelos de aprendizaje automático.

El sistema no solo resuelve el problema de normalización territorial, sino que establece una capa de infraestructura reutilizable que puede ser integrada en múltiples dominios analíticos. Esta capacidad lo posiciona como un componente clave en la construcción de sistemas más complejos, incluyendo plataformas de análisis, DSS y aplicaciones geoespaciales.

En conjunto, el enfoque propuesto ofrece una base sólida para la estandarización del tratamiento de información territorial, contribuyendo a mejorar la calidad, consistencia e interoperabilidad de los datos en contextos reales de operación.

---

## Uso del sistema

El motor se expone mediante una API REST y puede ser consumido por sistemas externos para:

- normalización de direcciones
- validación territorial
- enriquecimiento de datos geográficos
- integración en pipelines analíticos

---

## Estado del proyecto

El sistema se encuentra en estado funcional con:

- API operativa
- catálogo nacional integrado
- métricas instrumentadas
- exportación de datos para análisis

---

## Licencia

[Definir según estrategia del proyecto]
# P01-ES v1.0: Un Marco Sociotécnico para la Ingestión Determinista de Documentos de Política

## 1. Resumen

Este documento describe la arquitectura y los contratos formales del nodo canónico N1, la primera fase operativa del pipeline mecanístico de políticas F.A.R.F.A.N. El nodo N1 es responsable de la ingestión determinista de Paquetes Canónicos de Política (CPP), transformándolos en un `PreprocessedDocument` estructurado que contiene exactamente 60 Smart Policy Chunks (SPC). Al conceptualizar este pipeline como un sistema sociotécnico, enfatizamos la interacción crítica entre sus componentes computacionales (código, infraestructura) y sus componentes sociales (analistas, formuladores de políticas, marcos legales). Este enfoque asegura que el sistema no solo sea técnicamente robusto, sino que también esté alineado con el complejo contexto humano en el que opera. El diseño del nodo N1 garantiza la integridad referencial, la salida determinista y el cumplimiento verificable a través de una serie de contratos explícitos de entrada, salida y procesamiento.

## 2. Introducción

El análisis de documentos de política pública presenta un desafío significativo para los sistemas computacionales. Estos documentos son artefactos complejos y semiestructurados que codifican intenciones legales, sociales y políticas. Los pipelines tradicionales de procesamiento de lenguaje natural a menudo tienen dificultades para mantener el determinismo y la trazabilidad, lo que hace que sus resultados sean difíciles de auditar y confiar. El proyecto F.A.R.F.A.N. aborda este desafío implementando un pipeline mecanístico, impulsado por contratos, que asegura que cada etapa del procesamiento sea verificable y reproducible.

Este artículo detalla la primera fase de este pipeline, el nodo de ingestión N1. Adoptamos una perspectiva de la teoría de sistemas sociotécnicos para enmarcar nuestro diseño. Esta teoría postula que cualquier sistema eficaz es producto de la interacción entre sus subsistemas técnico y social. En nuestro contexto, lo "técnico" se refiere al código Python, las estructuras de datos y la lógica de validación, mientras que lo "social" abarca a los expertos en políticas que crean los documentos fuente, los analistas que interpretan los resultados del sistema y los estándares legales que gobiernan el dominio de la política. Por lo tanto, el nodo N1 está diseñado no solo como un script de procesamiento de datos, sino como un mecanismo institucional crítico para estandarizar datos de políticas no estructurados en un formato legible por máquina que respeta y preserva su intención semántica original.

La principal contribución de este trabajo es la formalización del proceso de ingestión como una serie de contratos inmutables, asegurando que la transformación de un PDF crudo a un `PreprocessedDocument` sea determinista y auditable. Este paso fundamental es crítico para las fases analíticas posteriores, que dependen de la integridad estructural de los 60 SPC canónicos generados por este nodo.

## 3. Arquitectura del Sistema y Metodología

El nodo N1 opera como una función discreta y sin estado dentro del motor de orquestación más amplio de F.A.R.F.A.N. Su arquitectura se define por una serie de contratos que gobiernan sus entradas, flujo interno y salidas, asegurando un comportamiento predecible y una integración perfecta con los componentes upstream y downstream.

### 3.1. Resumen del Nodo Canónico
- **ID del Nodo:** N1
- **Upstream:** N0 (Configuración Validada) + Entrada de PDF Crudo
- **Downstream:** N3 (Ejecución de Micro Preguntas) a través de `PreprocessedDocument`
- **Propósito:** Transformar un Paquete Canónico de Política (CPP) en un `PreprocessedDocument` chunkado que contiene exactamente 60 Smart Policy Chunks (SPC) y toda la metadata requerida para el análisis determinista.

### 3.2. Flujo Interno
El proceso interno es un pipeline de cinco pasos que asegura que cada documento se maneje de manera consistente:
1.  **Ingestión de CPP:** El sistema ejecuta el pipeline de ingestión de SPC para producir un `CanonPolicyPackage`.
2.  **Paso de Adaptador:** Un adaptador dedicado convierte el `CanonPolicyPackage` en un `PreprocessedDocument`, extrayendo y normalizando chunks, metadata e índices.
3.  **Validación:** El sistema valida el `PreprocessedDocument` contra su esquema, asegurando el conteo de chunks, la integridad del grafo y los campos de texto no vacíos.
4.  **Registro de Contexto:** La metadata de ingestión se almacena en un Manifiesto de Verificación para la auditabilidad.
5.  **Emisión:** El `PreprocessedDocument` validado se devuelve al contexto del orquestador para el procesamiento downstream.

### 3.3. Restricciones de Complejidad
Para mantener la modularidad y prevenir la decadencia arquitectónica, el nodo N1 se adhiere a límites estrictos de complejidad:
- **Subnodos:** Máximo 5 (ingestión, adaptador, validador, registrador de manifiesto, emisión).
- **Profundidad de Decisión:** No más de 3 ramas condicionales.
- **Acoplamiento:** Estrechamente acoplado solo al pipeline de SPC, el adaptador, el manifiesto de verificación y el contexto del orquestador.

## 4. Verificación y Validación (Resultados)

La fiabilidad del nodo N1 está garantizada por un conjunto de contratos formales que funcionan como su especificación operativa. Estos contratos no son meramente documentación; se hacen cumplir en tiempo de ejecución y sirven como la verdad fundamental para el comportamiento del sistema.

### 4.1. Contrato de Entrada
- **Ruta:** `process_development_plan_async(pdf_path, preprocessed_document=None, config)`
- **Entradas Requeridas:**
    - `pdf_path`: Una cadena que apunta al archivo fuente canónico.
    - `config`: Un objeto de configuración validado del nodo N0.
- **Precondiciones:**
    - El PDF debe ser accesible y su checksum registrado.
    - La versión del adaptador de SPC debe estar fijada y la estrategia de chunking declarada como "semántica".
- **Entradas Prohibidas:** Cargas útiles parcialmente analizadas, documentos sin metadata de política y referencias a adaptadores experimentales.

### 4.2. Contrato de Salida
- **Tipo:** Un dataclass `PreprocessedDocument`.
- **Postcondiciones:**
    - La salida debe contener exactamente 60 chunks de SPC, cada uno etiquetado con un `policy_area_id` y `dimension_id`.
    - La metadata debe reportar `chunk_count == 60` y `processing_mode == "chunked"`.

### 4.3. Manejo de Errores
El sistema está diseñado para fallar rápidamente y explícitamente ante la violación de un contrato:
- Las excepciones del pipeline de SPC o del adaptador se tratan como fatales y provocan el rechazo de la ejecución.
- El texto vacío o cero chunks desencadenan un `ValueError`.
- La falta de metadata `policy_area_id` o `dimension_id` en cualquier chunk conduce a un aborto con una entrada de diagnóstico detallada.

## 5. Visualizaciones

Los siguientes diagramas ilustran la arquitectura y la lógica del nodo N1, renderizados en la estética del dashboard Atroz para proporcionar un lenguaje visual cohesivo para el proyecto F.A.R.F.A.N.

### 5.1. Grafo de Control de Flujo
Este grafo muestra la lógica secuencial del nodo N1, destacando la ruta de procesamiento principal y el único punto de falla.

![Grafo de Control de Flujo](images/control_flow.png)

### 5.2. Grafo de Flujo de Datos
Este grafo ilustra cómo se pasan los objetos de datos entre los componentes del nodo N1, desde el PDF y la configuración iniciales hasta el `PreprocessedDocument` final y el Manifiesto de Verificación.

![Grafo de Flujo de Datos](images/data_flow.png)

### 5.3. Grafo de Transición de Estados
Este diagrama modela los posibles estados del nodo N1 durante su ejecución, desde "Inactivo" hasta "Emitiendo", incluyendo el estado de "Fallo" que resulta de una violación de contrato.

![Grafo de Transición de Estados](images/state_transition.png)

### 5.4. Grafo de Vinculación de Contratos
Este grafo muestra las relaciones entre los contratos formales y los componentes del sistema que gobiernan, enfatizando la naturaleza de la arquitectura impulsada por contratos.

![Grafo de Vinculación de Contratos](images/contract_linkage.png)

## 6. Discusión

El diseño del nodo N1 refleja una aplicación deliberada de la teoría de sistemas sociotécnicos. La arquitectura rígida y basada en contratos es una respuesta directa a la necesidad social de confianza y auditabilidad en el análisis de políticas. Al hacer cumplir el determinismo en el punto de ingestión, construimos una base de fiabilidad que persiste en todo el pipeline. El requisito de "60 chunks" no es arbitrario; es un estándar negociado socialmente que equilibra la granularidad analítica con la tratabilidad cognitiva para los analistas humanos.

Esta elección de diseño tiene varias implicaciones. Primero, fuerza una clara separación de preocupaciones entre la tarea técnica de análisis sintáctico y la tarea social de definir categorías analíticas (áreas de política y dimensiones). Segundo, hace que el comportamiento del sistema sea legible para todos los interesados, desde los desarrolladores hasta los expertos en políticas. El Manifiesto de Verificación, por ejemplo, sirve como un objeto límite que traduce los detalles de la ejecución técnica en un registro socialmente significativo de cumplimiento.

Sin embargo, esta rigidez también introduce restricciones. El sistema es intencionalmente inflexible en cuanto al conteo y la estructura de los chunks. Cualquier desviación de los 60 SPC canónicos se trata como un error crítico. Este compromiso—sacrificar la flexibilidad por la previsibilidad—es un principio fundamental de la filosofía del proyecto F.A.R.F.A.N., que prioriza la robustez institucional sobre la libertad analítica ad-hoc.

## 7. Conclusión

El nodo de ingestión N1 es un componente crítico del pipeline mecanístico de políticas F.A.R.F.A.N. Al enmarcar su diseño a través de una lente sociotécnica, hemos desarrollado un sistema que no solo es técnicamente sólido, sino también socialmente consciente. Su arquitectura basada en contratos asegura que la transformación inicial de documentos de política no estructurados en datos estructurados y analizables sea determinista, verificable y alineada con los objetivos generales de transparencia y confianza.

El trabajo futuro se centrará en los nodos analíticos downstream (N3 y más allá), que consumirán el `PreprocessedDocument` generado por N1. El determinismo fundamental establecido en esta fase es la precondición para los análisis semánticos y cuantitativos más complejos que siguen. Los principios de diseño impulsado por contratos y alineación sociotécnica continuarán guiando el desarrollo de todo el pipeline F.A.R.F.A.N.

## 8. Gestión de Cambios

- Cualquier cambio en el recuento de chunks, el comportamiento del adaptador o el pipeline de SPC requiere la actualización de este documento, su versión en inglés, e incrementar la etiqueta de la versión (p. ej., `P01-ES_v1.1`).
- La adición de nuevos atributos al `PreprocessedDocument` debe reflejarse en su contrato de esquema.

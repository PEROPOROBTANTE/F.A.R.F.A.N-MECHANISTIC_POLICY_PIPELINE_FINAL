# Compendio de Metodologías de Calibración, Parametrización e Integración del Modelo F.A.R.F.A.N.

## 0. Front Matter

### 0.2. Abstract

Este compendio presenta una formalización rigurosa y exhaustiva de los protocolos de calibración, parametrización e integración para el modelo mecanicista F.A.R.F.A.N., un pipeline computacional diseñado para el análisis de políticas públicas, específicamente aplicado a Planes de Desarrollo Territorial (PDT). A partir de la consolidación de especificaciones canónicas, descripciones formales de la unidad de análisis y notas de implementación operativas, este documento establece un marco autocontenido y normativo. Se detallan los fundamentos matemáticos del modelo de calibración, la estructura de la unidad de análisis, y los procedimientos paso a paso para la ejecución de cada fase del pipeline. El objetivo es proporcionar a especialistas y mantenedores un recurso único, limpio y no redundante que garantice la reproducibilidad, auditabilidad y coherencia del sistema completo, eliminando la ambigüedad y las dependencias de artefactos dispersos.

### 0.3. Palabras Clave

Calibración de Modelos, Parametrización, Integración de Sistemas, Políticas Públicas, Modelo Mecanicista, F.A.R.F.A.N., Análisis Computacional, Planes de Desarrollo Territorial, Reproducibilidad, Auditoría de Modelos.

### 0.4. Tabla de Contenido

*   **1. Introducción General al Pipeline de Análisis**
    *   1.1. Propósito y Alcance del Modelo Mecanicista
    *   1.2. Audiencia y Objetivos del Compendio
    *   1.3. Visión General del Pipeline: Calibración, Parametrización e Integración
    *   1.4. Convenciones de Notación y Estructura del Documento
*   **2. Marco Formal del Modelo de Calibración**
    *   2.1. Definiciones Fundamentales: Espacio de Estados y Variables
    *   2.2. Funcionales Objetivo y Métricas de Ajuste
    *   2.3. Catálogo de Métodos Canónicos de Calibración
    *   2.4. Supuestos y Limitaciones del Marco Formal
*   **3. La Unidad de Análisis: Planes de Desarrollo Territorial (PDT)**
    *   3.1. Descripción Estructural y Semántica del Dominio
    *   3.2. Atributos, Dimensiones y Restricciones Formales
    *   3.3. Mapeo entre la Unidad de Análisis y las Variables del Modelo
*   **4. Protocolo de Calibración de Métodos**
    *   4.1. Propósito y Objetivos del Protocolo
    *   4.2. Insumos Requeridos: Datos, Parámetros y Artefactos
    *   4.3. Pipeline Operacional Paso a Paso
    *   4.4. Proceso Iterativo de Ajuste y Evaluación
    *   4.5. Código de Referencia y Pseudocódigo
    *   4.6. Checklist de Ejecución y Auditoría
*   **5. Protocolo de Parametrización del Modelo**
    *   5.1. Propósito y Objetivos del Protocolo
    *   5.2. Fuentes de Parámetros y Reglas de Derivación
    *   5.3. Pipeline Operacional Paso a Paso
    *   5.4. Código de Referencia y Pseudocódigo
    *   5.5. Checklist de Ejecución y Auditoría
*   **6. Protocolo de Integración en el Pipeline F.A.R.F.A.N.**
    *   6.1. Propósito y Objetivos de la Integración
    *   6.2. Arquitectura de Módulos e Interfaces
    *   6.3. Secuencia de Orquestación y Flujo de Control
    *   6.4. Código de Referencia y Pseudocódigo
    *   6.5. Checklist de Ejecución y Auditoría
*   **7. Discusión y Recomendaciones**
    *   7.1. Análisis Crítico de Divergencias entre Canon y Práctica
    *   7.2. Riesgos, Limitaciones y Anti-Patrones Identificados
    *   7.3. Recomendaciones para Mantenimiento y Futuras Extensiones
*   **8. Anexos**
    *   Anexo A: Notación Matemática Canónica (Detallada)
    *   Anexo B: Tablas Completas de la Unidad de Análisis
    *   Anexo C: Ejemplos de Scripts Completos
    *   Anexo D: Tabla de Trazabilidad Conceptual: `raw` vs. Compendio

## 1. Introducción General al Pipeline de Análisis

### 1.1. Propósito y Alcance del Modelo Mecanicista

El modelo F.A.R.F.A.N. es un pipeline computacional de naturaleza mecanicista, diseñado para la evaluación y el análisis cuantitativo de políticas públicas contenidas en Planes de Desarrollo Territorial (PDT). Su propósito fundamental es trascender el análisis descriptivo tradicional para ofrecer una simulación basada en reglas de las interacciones causales entre los insumos, actividades, productos y resultados esperados de una política. El alcance del modelo abarca desde la ingesta y estructuración de los documentos normativos hasta la calibración de los métodos de análisis, la parametrización de las simulaciones y la integración de los componentes en un flujo de ejecución auditable. Este compendio se enfoca exclusivamente en las tres fases nucleares de este pipeline: calibración, parametrización e integración, dejando fuera del alcance el detalle de los modelos de análisis específicos.

### 1.2. Audiencia y Objetivos del Compendio

Este documento está dirigido a una audiencia especializada, compuesta por científicos de datos, economistas cuantitativos, analistas de políticas públicas y arquitectos de software responsables del mantenimiento y la extensión del ecosistema F.A.R.F.A.N. Se asume una familiaridad con la notación matemática, los pipelines de datos y los principios de modelado computacional, pero no un conocimiento previo del framework F.A.R.F.A.N. El objetivo principal es establecer un canon doctrinal y técnico que sirva como única fuente de verdad, eliminando la ambigüedad de especificaciones dispersas y garantizando que todos los procedimientos sean formales, autocontenidos y reproducibles.

### 1.3. Visión General del Pipeline: Calibración, Parametrización e Integración

El pipeline F.A.R.F.A.N. se estructura en torno a tres procesos secuenciales y dependientes que transforman un conjunto de métodos analíticos genéricos en un motor de simulación ajustado y validado.

*   **Calibración**: Proceso mediante el cual se ajustan los parámetros internos de los métodos de análisis para que sus resultados se correspondan con un conjunto de datos observados o criterios de calidad predefinidos. Es la fase de "afinamiento" del modelo.
*   **Parametrización**: Proceso de configuración de los valores exógenos y las condiciones de contorno que definen un escenario de simulación específico. A diferencia de la calibración, no modifica el comportamiento interno de los métodos, sino los inputs que reciben.
*   **Integración**: Proceso de ensamblaje de los métodos calibrados y parametrizados en una secuencia de ejecución coherente y orquestada, definiendo las interfaces y el flujo de control entre los distintos módulos del sistema.

El siguiente diagrama representa la interrelación de estos componentes en el ecosistema F.A.R.F.A.N.

<div class="macro-phylogram atroz-pipeline" style="position: relative; width: 500px; height: 500px; margin: auto; background: #111; font-family: 'JetBrains Mono', monospace;">
  <style>
    :root {
      --atroz-red-500: #ef4444;
      --atroz-green-toxic: #65a30d;
      --atroz-blue-electric: #3b82f6;
      --atroz-copper-500: #a16207;
      --ink: #d4d4d4;
    }
    .macro-phylogram {
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .phylo-ring {
      position: absolute;
      border-radius: 50%;
      border: 1px solid var(--atroz-copper-500);
      opacity: 0.3;
    }
    .phylo-ring:nth-child(1) { width: 60%; height: 60%; }
    .phylo-ring:nth-child(2) { width: 75%; height: 75%; }
    .phylo-ring:nth-child(3) { width: 90%; height: 90%; }
    .phylo-center {
      width: 40%;
      height: 40%;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(161, 98, 7, 0.4) 0%, rgba(17, 17, 17, 0) 70%);
      display: flex;
      justify-content: center;
      align-items: center;
      color: var(--ink);
      text-shadow: 0 0 5px var(--atroz-copper-500);
    }
  </style>
  <div class="phylo-ring"></div>
  <div class="phylo-ring"></div>
  <div class="phylo-ring"></div>
  <div class="phylo-center">
    <span style="font-size:32px;font-weight:700;">F.A.R.F.A.N</span>
  </div>
  <svg viewBox="0 0 200 200" style="position:absolute;width:100%;height:100%;top:0;left:0;overflow:visible;">
    <!-- Unidad de análisis -->
    <line x1="100" y1="100" x2="35" y2="50" stroke="var(--atroz-red-500)" stroke-width="0.5"/>
    <text x="10" y="48" font-size="7" fill="var(--ink)">Unidad de Análisis</text>
    <!-- Calibración -->
    <line x1="100" y1="100" x2="170" y2="40" stroke="var(--atroz-green-toxic)" stroke-width="0.5"/>
    <text x="172" y="38" font-size="7" fill="var(--ink)">Calibración</text>
    <!-- Parametrización -->
    <line x1="100" y1="100" x2="180" y2="120" stroke="var(--atroz-blue-electric)" stroke-width="0.5"/>
    <text x="182" y="122" font-size="7" fill="var(--ink)">Parametrización</text>
    <!-- Integración -->
    <line x1="100" y1="100" x2="40" y2="160" stroke="var(--atroz-copper-500)" stroke-width="0.5"/>
    <text x="15" y="168" font-size="7" fill="var(--ink)">Integración</text>
  </svg>
</div>

### 1.4. Convenciones de Notación y Estructura del Documento

Para garantizar la claridad y la precisión, este compendio adopta un conjunto estricto de convenciones de notación. Las variables matemáticas, los parámetros y los operadores se definen formalmente en el Anexo A y se utilizan de manera consistente a lo largo del texto. El documento se organiza de lo general a lo específico: se comienza con el marco teórico del modelo (Sección 2) y la descripción de su objeto de estudio (Sección 3), para luego detallar los protocolos operativos de Calibración (Sección 4), Parametrización (Sección 5) e Integración (Sección 6). Una sección de Discusión (Sección 7) analiza críticamente las desviaciones y limitaciones del sistema. Finalmente, los Anexos (Sección 8) proporcionan material de referencia detallado.

## 2. Marco Formal del Modelo de Calibración

La calibración de métodos dentro del pipeline F.A.R.F.A.N. se rige por un sistema formalizado que asigna una métrica de calidad a cada instancia de un método en un contexto de ejecución específico. Este marco garantiza que las decisiones sean auditables, reproducibles y matemáticamente rigurosas.

### 2.1. Definiciones Fundamentales: Espacio de Estados y Variables

El sistema se fundamenta en la noción de un grafo computacional y un contexto de análisis.

**Definición 2.1 (Grafo Computacional de Análisis de Políticas):** Un grafo computacional de análisis de políticas es una tupla \\(\\Gamma = (V, E, T, S)\\), donde:
*   \\(V\\): Un conjunto finito de nodos que representan instancias de métodos.
*   \\(E \\subseteq V \\times V\\): Un conjunto de aristas dirigidas acíclicas que representan el flujo de datos.
*   \\(T: E \\rightarrow \\text{Tipos}\\): Una función que asigna un tipo a cada arista.
*   \\(S: V \\rightarrow \\text{Firmas}\\): Una función que especifica los contratos de entrada/salida de cada nodo.

**Definición 2.2 (Contexto de Análisis):** Un contexto de ejecución es una tupla \\(\\text{ctx} = (Q, D, P, U)\\), donde:
*   \\(Q\\): El identificador de la pregunta de análisis.
*   \\(D\\): La dimensión analítica.
*   \\(P\\): El área de política.
*   \\(U\\): Un escalar en \\([0,1]\\) que representa la calidad de la unidad de análisis.

### 2.2. Funcionales Objetivo y Métricas de Ajuste

El objetivo de la calibración es cuantificar la "aptitud" de un método para una tarea. Esto se logra mediante una función de calibración compuesta por múltiples capas, cada una evaluando una dimensión ortogonal de calidad.

**Definición 2.3 (Capas de Calibración):** El sistema define un conjunto de funciones de capa \\(x_{\\ell}(I) \\rightarrow [0,1]\\), donde \\(I\\) es una instancia de método y \\(\\ell\\) pertenece a un conjunto de capas predefinidas como \\(\\{@b, @chain, @u, @q, @d, @p, @C, @m\\}\\). Cada capa mide un aspecto específico:
*   **Capa Base (@b):** Calidad intrínseca del método (teoría, implementación, despliegue).
*   **Capa de Cadena (@chain):** Compatibilidad de tipos y contratos en el grafo.
*   **Capa de Unidad de Análisis (@u):** Sensibilidad a la calidad del documento de entrada.
*   **Capas Contextuales (@q, @d, @p):** Afinidad con la pregunta, dimensión y área de política.
*   **Capa de Congruencia (@C):** Validez del método dentro de un ensamble.
*   **Capa Meta (@m):** Calidad de la gobernanza y observabilidad.

**Definición 2.4 (Operador de Fusión):** Los scores de las capas activas se agregan mediante un operador de fusión, típicamente una Agregación de Choquet de 2-aditividad, que captura interacciones sinérgicas entre capas:
\\[ Cal(I) = \\sum_{\\ell \\in L(M)} a_{\\ell} \\cdot x_{\\ell}(I) + \\sum_{(\\ell,k) \\in S_{int}} a_{\\ell k} \\cdot \\min(x_{\\ell}(I), x_{k}(I)) \\]
Donde \\(L(M)\\) es el conjunto de capas activas, \\(S_{int}\\) es el conjunto de interacciones, y los coeficientes \\(a\\) están normalizados.

### 2.3. Catálogo de Métodos Canónicos de Calibración

El marco define un conjunto de métodos canónicos para la evaluación de cada capa, garantizando consistencia. A continuación, se presentan ejemplos ilustrativos.

**Ejemplo 2.3.1 (Evaluación de Capa Base @b):** La capa base se descompone en tres sub-métricas ponderadas:
\\[ x_{@b}(I) = w_{th} \\cdot b_{theory}(M) + w_{imp} \\cdot b_{impl}(M) + w_{dep} \\cdot b_{deploy}(M) \\]
Donde cada función \\(b_*\\) se evalúa mediante una rúbrica específica. Por ejemplo, la calidad de implementación:
```python
b_impl(M) = rubric_score({
    'test_coverage': [0.35],    # ≥ 80% → 1.0
    'type_annotations': [0.25],  # complete → 1.0
    'error_handling': [0.25],    # all paths covered → 1.0
    'documentation': [0.15]      # complete API docs → 1.0
})
```

**Ejemplo 2.3.2 (Evaluación de Capa de Cadena @chain):** Esta capa se evalúa mediante un sistema de reglas discretas basado en la validación de contratos.
```
x_@chain = {
    0       if hard_mismatch(v)
    0.3     if missing_critical_optional(v)
    0.6     if soft_schema_violation(v)
    1.0     if all_contracts_pass(v)
}
```

### 2.4. Supuestos y Limitaciones del Marco Formal

El modelo de calibración opera bajo un conjunto de supuestos clave:
1.  **Ortogonalidad de las Capas**: Se asume que cada capa de calibración mide una dimensión de calidad independiente de las demás, con interacciones explícitamente modeladas por el operador de fusión.
2.  **Completitud del Contexto**: Se asume que la tupla de contexto \\((Q, D, P, U)\\) captura toda la información relevante para determinar la aptitud de un método.
3.  **Atomicidad de los Métodos**: El modelo trata los métodos como cajas negras, evaluando su comportamiento externo y sus metadatos, pero no su lógica interna detallada.
4.  **Anti-Universalidad**: Se impone la restricción de que ningún método puede tener compatibilidad máxima en todos los contextos, forzando la especialización.

La principal limitación reside en la dependencia de la calidad de las rúbricas y las configuraciones del modelo, cuya definición es un proceso experto que debe ser mantenido y validado continuamente.

## 3. La Unidad de Análisis: Planes de Desarrollo Territorial (PDT)

El objeto de estudio del pipeline F.A.R.F.A.N. es el Plan de Desarrollo Territorial (PDT), un documento complejo y semi-estructurado que articula la estrategia de un gobierno municipal para un periodo de cuatro años. La correcta interpretación de su estructura y contenido es un prerrequisito para cualquier análisis subsecuente.

### 3.1. Descripción Estructural y Semántica del Dominio

Un PDT, regido por la Ley Orgánica 152 de 1994 de Colombia, se compone de dos partes principales: una Parte Estratégica y un Plan Plurianual de Inversiones (PPI). La primera define los objetivos y programas, mientras que la segunda detalla los recursos financieros. La estructura típica sigue una jerarquía que va desde un diagnóstico general hasta metas e indicadores específicos. Los componentes clave incluyen el marco normativo, el diagnóstico territorial, las líneas estratégicas, los programas, y el plan financiero.

### 3.2. Atributos, Dimensiones y Restricciones Formales

El archivo `canonic_description_unit_analysis.json` proporciona una descripción formal de estos componentes. A continuación, se presentan los elementos más relevantes en formato tabular.

**Tabla 3.1: Resumen de Componentes Canónicos del PDT**

| Sección Principal                                 | Contenido Clave                                          | Lógica Organizacional                      |
| ------------------------------------------------- | -------------------------------------------------------- | ------------------------------------------ |
| **I. Diagnóstico (Caracterización)**              | Análisis de Brechas, Caracterización Socio-Sectorial.    | Identifica el 'Qué' y el 'Por qué' intervenir. |
| **II. Parte Estratégica**                         | Líneas Estratégicas (Ejes), Programas, Metas.            | Define el 'Qué hacer' y los 'Objetivos'.   |
| **III. Plan Plurianual de Inversiones (PPI)**     | Plan Financiero, Fuentes de Financiación, Matriz PPI.    | Detalla el 'Cuánto' y el 'Cómo financiar'.  |
| **Capítulos Especiales (Paz/PDET)**                 | Articulación con la RRI, iniciativas PDET/PATR.          | Integra los compromisos de paz.            |
| **Seguimiento y Evaluación**                      | Indicadores, Plan de Acción, Informes Anuales.           | Garantiza el 'Cómo medir' la ejecución.    |

**Tabla 3.2: Patrones Típicos de Delimitación de Secciones**

| Nivel Jerárquico            | Formato Típico de Encabezado                          | Ejemplos de Contenido                                   |
| --------------------------- | ----------------------------------------------------- | ------------------------------------------------------- |
| Título o Capítulo Mayor     | `CAPÍTULO [Número]. [Título]`                         | `CAPÍTULO III PARTE ESTRATÉGICA`                        |
| Subcapítulo Principal       | `[Número].[Número]. [Título]`                         | `7.1 INSTRUMENTOS MONITORES Y DE EVALUACIÓN`          |
| Línea Estratégica (Eje)     | `Línea estratégica [Número/Nombre]: [Título]`         | `Línea estratégica I: Un futuro con proyección social`  |
| Componente/Programa         | `Sector: [Nombre]` o `Programa: [Nombre]`             | `Sector: Salud y Protección Social`                     |

### 3.3. Mapeo entre la Unidad de Análisis y las Variables del Modelo

La estructura del PDT se mapea directamente a las variables del modelo de calibración y análisis.
*   Las **Líneas Estratégicas, Programas y Metas** definidas en la Parte Estratégica del PDT se convierten en las entidades sobre las cuales los métodos de análisis operan.
*   Los **indicadores y sus valores** (línea base, metas cuatrienales) extraídos de las matrices de seguimiento son los datos observacionales contra los cuales se calibran los modelos de simulación.
*   La **calidad estructural y de contenido** del PDT (completitud de secciones, calidad de indicadores) alimenta directamente la **Capa de Unidad de Análisis (@u)** en el modelo de calibración, afectando la confianza en los resultados de todos los métodos sensibles a la calidad del input.

En resumen, la unidad de análisis no es un mero input de datos, sino un componente activo cuyo grado de adherencia a la estructura canónica modula la fiabilidad de todo el pipeline de análisis.

## 4. Protocolo de Calibración de Métodos

El protocolo de calibración es el conjunto de procedimientos operativos que garantizan que los métodos analíticos del pipeline F.A.R.F.A.N. se comporten de manera consistente, precisa y alineada con los objetivos del modelo. Este proceso transforma un método genérico en una herramienta afinada para un dominio de análisis específico.

### 4.1. Propósito y Objetivos del Protocolo

El propósito central de la calibración es minimizar la incertidumbre y el error en los resultados del modelo, ajustando los parámetros internos de los métodos para que sus outputs converjan hacia valores de referencia conocidos o satisfagan un conjunto de restricciones de calidad. Los objetivos son:
*   **Asegurar la validez**: Garantizar que los métodos midan lo que se supone que deben medir.
*   **Mejorar la precisión**: Reducir la desviación entre los resultados del modelo y la evidencia empírica.
*   **Garantizar la reproducibilidad**: Estandarizar el proceso de ajuste para que sea repetible y auditable.

### 4.2. Insumos Requeridos: Datos, Parámetros y Artefactos

El proceso de calibración requiere un conjunto de insumos bien definidos, cuya interrelación se ilustra en el siguiente diagrama.

<div class="meso-mesh atroz-data-mesh" style="position: relative; width: 600px; height: 400px; margin: auto; background: #111; font-family: 'JetBrains Mono', monospace; border: 1px solid #333;">
  <style>
    .meso-mesh { --atroz-blue-electric: #3b82f6; --atroz-green-toxic: #65a30d; --ink: #d4d4d4; }
    .mesh-cluster { position: absolute; text-align: center; color: var(--ink); }
    .cluster-value { font-size: 24px; font-weight: 700; display: block; }
    .cluster-label { font-size: 10px; opacity: 0.7; }
    .mesh-cluster::before { content: ''; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); border-radius: 50%; z-index: -1; }
    .mesh-cluster:nth-child(1)::before { width: 80px; height: 80px; background: radial-gradient(circle, rgba(59, 130, 246, 0.2) 0%, transparent 70%); }
    .mesh-cluster:nth-child(2)::before { width: 80px; height: 80px; background: radial-gradient(circle, rgba(59, 130, 246, 0.2) 0%, transparent 70%); }
    .mesh-cluster:nth-child(3)::before { width: 100px; height: 100px; background: radial-gradient(circle, rgba(101, 163, 13, 0.2) 0%, transparent 70%); }
    .mesh-cluster:nth-child(4)::before { width: 120px; height: 120px; background: radial-gradient(circle, rgba(101, 163, 13, 0.3) 0%, transparent 70%); }
  </style>
  <div class="mesh-cluster" style="top:20%;left:10%;">
    <span class="cluster-value">D</span>
    <span class="cluster-label">Datos Crudos</span>
  </div>
  <div class="mesh-cluster" style="top:20%;right:10%;">
    <span class="cluster-value">P_exo</span>
    <span class="cluster-label">Parámetros Exógenos</span>
  </div>
  <div class="mesh-cluster" style="bottom:35%;left:40%;">
    <span class="cluster-value">Φ</span>
    <span class="cluster-label">Transformaciones</span>
  </div>
  <div class="mesh-cluster" style="bottom:15%;right:20%;">
    <span class="cluster-value">Θ*</span>
    <span class="cluster-label">Parámetros Calibrados</span>
  </div>
  <svg style="position:absolute;width:100%;height:100%;top:0;left:0;pointer-events:none;">
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--atroz-blue-electric)" opacity="0.6"/>
      </marker>
      <marker id="arrow-green" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--atroz-green-toxic)" opacity="0.6"/>
      </marker>
    </defs>
    <line x1="18%" y1="35%" x2="48%" y2="55%" stroke="var(--atroz-blue-electric)" stroke-width="0.5" opacity="0.6" marker-end="url(#arrow)"/>
    <line x1="82%" y1="35%" x2="52%" y2="55%" stroke="var(--atroz-blue-electric)" stroke-width="0.5" opacity="0.6" marker-end="url(#arrow)"/>
    <line x1="50%" y1="65%" x2="70%" y2="75%" stroke="var(--atroz-green-toxic)" stroke-width="0.7" opacity="0.7" marker-end="url(#arrow-green)"/>
  </svg>
</div>

*   **Datos de Referencia (D)**: Conjuntos de datos validados, corpus de texto anotado, o resultados históricos que sirven como "verdad de campo".
*   **Parámetros Exógenos (P_exo)**: Configuraciones iniciales o restricciones del modelo que no son objeto de la calibración.
*   **Scripts de Transformación (Φ)**: Código que preprocesa los datos crudos y los convierte en formatos analizables por los métodos.
*   **Artefacto de Salida (Θ*)**: Un archivo (típicamente JSON) que almacena los valores óptimos de los parámetros encontrados durante la calibración.

### 4.3. Pipeline Operacional Paso a Paso

El pipeline de calibración es un proceso estructurado que se ejecuta de forma iterativa hasta alcanzar un estado de convergencia.

1.  **Preprocesamiento**: Se cargan los datos de referencia (D) y se aplican los scripts de transformación (Φ) para generar un corpus de validación limpio y estructurado.
2.  **Configuración de Escenarios**: Se define un espacio de búsqueda para los hiperparámetros del método a calibrar. Esto puede incluir rangos de valores, distribuciones o un conjunto discreto de opciones.
3.  **Ejecución de Corridas de Calibración**: Se ejecuta el método de forma repetida sobre el corpus de validación, cada vez con una combinación diferente de hiperparámetros. Algoritmos como la búsqueda en grilla (Grid Search), la búsqueda aleatoria (Random Search) o la optimización bayesiana pueden ser empleados para explorar el espacio de búsqueda de manera eficiente.
4.  **Evaluación y Selección de Soluciones**: El resultado de cada corrida se compara contra el corpus de validación usando una métrica de ajuste (ej. F1-score, error cuadrático medio). La combinación de hiperparámetros que optimiza esta métrica se selecciona como la solución final (Θ*).
5.  **Validación Posterior**: La solución óptima se valida contra un conjunto de datos de prueba (hold-out set) para asegurar que el modelo generaliza y no ha sufrido sobreajuste (overfitting).

### 4.4. Proceso Iterativo de Ajuste y Evaluación

La calibración no es un proceso lineal, sino un ciclo de refinamiento. La "hélice de calibración" visualiza este proceso, donde cada punto representa una evaluación de un conjunto de parámetros, y los conectores indican una iteración de ajuste que busca mejorar el resultado.

<div class="helix-chart" style="position: relative; width: 600px; height: 300px; margin: auto; background: #111; font-family: 'JetBrains Mono', monospace; border: 1px solid #333; display: flex; align-items: center; justify-content: center;">
  <style>
    .helix-chart { --atroz-green-toxic: #65a30d; --atroz-red-500: #ef4444; --ink: #d4d4d4; }
    .iteration-point { position: absolute; width: 10px; height: 10px; border-radius: 50%; background-color: var(--atroz-green-toxic); box-shadow: 0 0 5px var(--atroz-green-toxic); }
    .eval-point { position: absolute; width: 6px; height: 6px; border-radius: 50%; background-color: var(--atroz-red-500); }
    .iteration-label { position: absolute; color: var(--ink); font-size: 8px; opacity: 0.7; }
  </style>
  <svg style="position:absolute;width:100%;height:100%;top:0;left:0;pointer-events:none;">
    <path d="M 50 150 Q 150 -50 300 150 T 550 150" stroke="#444" stroke-width="1" fill="none" stroke-dasharray="3,3"/>
  </svg>

  <!-- Iteration 1 -->
  <div class="iteration-point" style="left: 45px; top: 145px;"></div>
  <div class="iteration-label" style="left: 40px; top: 160px;">Θ_0</div>
  <div class="eval-point" style="left: 100px; top: 68px;"></div>
  <div class="iteration-label" style="left: 90px; top: 50px;">Score=0.6</div>

  <!-- Iteration 2 -->
  <div class="iteration-point" style="left: 160px; top: 38px;"></div>
  <div class="iteration-label" style="left: 155px; top: 20px;">Θ_1</div>
  <div class="eval-point" style="left: 220px; top: 68px;"></div>
  <div class="iteration-label" style="left: 210px; top: 50px;">Score=0.75</div>

  <!-- Iteration 3 -->
  <div class="iteration-point" style="left: 295px; top: 145px;"></div>
  <div class="iteration-label" style="left: 290px; top: 160px;">Θ_2</div>
  <div class="eval-point" style="left: 350px; top: 220px;"></div>
  <div class="iteration-label" style="left: 340px; top: 235px;">Score=0.85</div>

  <!-- Iteration 4 (Optimal) -->
  <div class="iteration-point" style="left: 430px; top: 240px;"></div>
  <div class="iteration-label" style="left: 425px; top: 255px;">Θ*</div>
  <div class="eval-point" style="left: 500px; top: 147px;"></div>
  <div class="iteration-label" style="left: 490px; top: 130px;">Score=0.92</div>
</div>

### 4.5. Código de Referencia y Pseudocódigo

El siguiente pseudocódigo ilustra el núcleo lógico de un proceso de calibración basado en búsqueda en grilla.

```pseudocode
function calibrate_method(method, data_corpus, parameter_grid):
  best_score = -infinity
  best_parameters = null

  // Iterar sobre todas las combinaciones de parámetros
  for params in generate_combinations(parameter_grid):
    // Configurar el método con los parámetros actuales
    method.configure(params)

    total_error = 0
    // Evaluar el método en todo el corpus de datos
    for sample in data_corpus:
      prediction = method.execute(sample.input)
      error = calculate_error(prediction, sample.ground_truth)
      total_error += error

    // Calcular score de ajuste (menor error es mejor)
    current_score = 1 / total_error

    // Si el score actual es el mejor hasta ahora, guardarlo
    if current_score > best_score:
      best_score = current_score
      best_parameters = params

  // Devolver los mejores parámetros encontrados
  return best_parameters
```

### 4.6. Checklist de Ejecución y Auditoría

Para garantizar la robustez y reproducibilidad del protocolo de calibración, cada ejecución debe ser verificada contra el siguiente checklist.

*   [ ] **Insumos Versionados**: ¿Están los datos de referencia (D) y los scripts (Φ) bajo control de versiones?
*   [ ] **Separación de Datos**: ¿Se ha mantenido una estricta separación entre los conjuntos de entrenamiento, validación y prueba?
*   [ ] **Métrica de Ajuste Definida**: ¿Está la métrica de evaluación formalmente definida y justificada para el problema en cuestión?
*   [ ] **Espacio de Búsqueda Documentado**: ¿Está el `parameter_grid` explícitamente definido y documentado?
*   [ ] **Resultados Auditables**: ¿Se han almacenado los resultados de cada corrida, incluyendo los parámetros usados y el score obtenido?
*   [ ] **Validación de Generalización**: ¿Se ha realizado una validación final contra un conjunto de prueba no visto durante el ajuste?
*   [ ] **Artefacto de Salida Generado**: ¿Se ha generado y versionado correctamente el archivo de parámetros calibrados (Θ*)?

## 5. Protocolo de Parametrización del Modelo

La parametrización es el proceso de configurar el modelo con valores específicos para un escenario de ejecución concreto. A diferencia de la calibración, que ajusta el comportamiento interno de los métodos, la parametrización establece las condiciones de contorno y los inputs exógenos que el modelo utilizará.

### 5.1. Distinción Conceptual entre Calibración y Parametrización

Es fundamental distinguir ambos procesos:
*   **Calibración**: Es un proceso **interno** y **único** (o poco frecuente) que busca el conjunto de hiperparámetros `Θ*` que optimiza el rendimiento de un método. El resultado es un método "afinado".
*   **Parametrización**: Es un proceso **externo** y **frecuente** (por cada ejecución) que provee al método ya calibrado los parámetros de entrada `P` para un caso de uso. El resultado es un modelo "configurado" para un escenario.

En resumen, la calibración define *cómo* debe funcionar el método, mientras que la parametrización le dice *con qué* debe funcionar.

### 5.2. Fuentes de Parámetros y Reglas de Derivación

Los parámetros del modelo F.A.R.F.A.N. se derivan de múltiples fuentes, organizadas jerárquicamente. La precedencia define qué fuente sobrescribe a las demás, garantizando un control granular sobre la configuración. El siguiente diagrama ilustra este flujo de consolidación.

<div class="meso-mesh atroz-param-mesh" style="position: relative; width: 600px; height: 400px; margin: auto; background: #111; font-family: 'JetBrains Mono', monospace; border: 1px solid #333;">
  <style>
    .atroz-param-mesh { --atroz-blue-electric: #3b82f6; --atroz-red-500: #ef4444; --atroz-copper-500: #a16207; --ink: #d4d4d4; }
    .param-cluster { position: absolute; text-align: center; color: var(--ink); font-size: 10px; }
    .param-value { font-size: 18px; font-weight: 700; display: block; }
    .param-cluster::before { content: ''; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); border-radius: 50%; z-index: -1; opacity: 0.2; }
    .param-cluster:nth-child(1)::before { width: 90px; height: 90px; background: radial-gradient(circle, var(--atroz-red-500) 0%, transparent 70%); }
    .param-cluster:nth-child(2)::before { width: 80px; height: 80px; background: radial-gradient(circle, var(--atroz-blue-electric) 0%, transparent 70%); }
    .param-cluster:nth-child(3)::before { width: 80px; height: 80px; background: radial-gradient(circle, var(--atroz-blue-electric) 0%, transparent 70%); }
    .param-cluster:nth-child(4)::before { width: 80px; height: 80px; background: radial-gradient(circle, var(--atroz-blue-electric) 0%, transparent 70%); }
    .param-cluster:nth-child(5)::before { width: 120px; height: 120px; background: radial-gradient(circle, var(--atroz-copper-500) 0%, transparent 70%); }
  </style>
  <div class="param-cluster" style="top: 10%; left: 40%;">
    <span class="param-value">P_rt</span>
    <span>Runtime (CLI)</span>
  </div>
  <div class="param-cluster" style="top: 45%; left: 10%;">
    <span class="param-value">P_scn</span>
    <span>Escenario (JSON)</span>
  </div>
    <div class="param-cluster" style="top: 45%; right: 10%;">
    <span class="param-value">P_ctx</span>
    <span>Contexto (PDT)</span>
  </div>
  <div class="param-cluster" style="bottom: 10%; left: 20%;">
    <span class="param-value">P_def</span>
    <span>Defaults (Código)</span>
  </div>
  <div class="param-cluster" style="bottom: 20%; right: 25%;">
    <span class="param-value">P_final</span>
    <span>Parámetros Validados</span>
  </div>
  <svg style="position:absolute;width:100%;height:100%;top:0;left:0;pointer-events:none;">
      <defs>
        <marker id="arrow-param" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#888" opacity="0.6"/>
        </marker>
      </defs>
      <line x1="50%" y1="25%" x2="70%" y2="65%" stroke="var(--atroz-red-500)" stroke-width="1" opacity="0.8" marker-end="url(#arrow-param)"/>
      <line x1="20%" y1="60%" x2="65%" y2="70%" stroke="var(--atroz-blue-electric)" stroke-width="0.5" opacity="0.6" marker-end="url(#arrow-param)"/>
      <line x1="80%" y1="60%" x2="75%" y2="70%" stroke="var(--atroz-blue-electric)" stroke-width="0.5" opacity="0.6" marker-end="url(#arrow-param)"/>
      <line x1="30%" y1="80%" x2="60%" y2="75%" stroke="var(--atroz-blue-electric)" stroke-width="0.5" opacity="0.6" marker-end="url(#arrow-param)"/>
  </svg>
</div>

Las fuentes se aplican en orden de precedencia descendente:
1.  **Parámetros de Ejecución (P_rt)**: Proveídos por el usuario o el sistema orquestador en el momento de la ejecución. Tienen la máxima precedencia y sobrescriben cualquier otra fuente.
2.  **Archivos de Configuración de Escenario (P_scn)**: Documentos JSON que definen un conjunto coherente de parámetros para un tipo de análisis (ej. `production.json`).
3.  **Parámetros Derivados del Contexto (P_ctx)**: Valores extraídos de la unidad de análisis (ej. el año de inicio del plan).
4.  **Valores por Defecto (P_def)**: Valores codificados en la firma de los métodos, que se utilizan como último recurso.

### 5.3. Procedimiento Paso a Paso para Parametrizar

El pipeline de parametrización se ejecuta al inicio de cada análisis.
1.  **Carga de la Configuración Base**: Se carga el archivo de configuración de escenario apropiado (ej. `production.json`), que contiene la mayoría de los parámetros.
2.  **Extracción de Parámetros Contextuales**: Se realiza un análisis preliminar de la unidad de análisis (PDT) para extraer parámetros clave como fechas, presupuestos o nombres de secciones.
3.  **Resolución de Precedencia**: Se combinan los parámetros de todas las fuentes, aplicando la regla de que las fuentes de mayor precedencia (runtime) sobrescriben a las de menor precedencia (defaults).
4.  **Validación de Parámetros**: Se valida el conjunto final de parámetros contra un esquema definido para asegurar que todos los valores requeridos están presentes, tienen el tipo correcto y se encuentran dentro de los rangos permitidos.
5.  **Asignación a Estructuras del Modelo**: Los parámetros validados se cargan en los objetos de configuración que serán consumidos por los diferentes módulos del pipeline.

### 5.4. Código de Referencia y Pseudocódigo

El siguiente pseudocódigo ilustra el proceso de carga y resolución de precedencia de parámetros.

```pseudocode
function load_parameters(runtime_params, scenario_path, pdt_document):
  // 1. Cargar valores por defecto desde la definición del modelo
  params = get_model_defaults()

  // 2. Cargar configuración de escenario desde archivo JSON
  scenario_params = load_json_from(scenario_path)
  params.merge(scenario_params) // Sobrescribe defaults

  // 3. Extraer parámetros del documento PDT
  contextual_params = extract_from_pdt(pdt_document)
  params.merge(contextual_params) // Sobrescribe escenario

  // 4. Aplicar parámetros de runtime (máxima precedencia)
  params.merge(runtime_params) // Sobrescribe todo lo anterior

  // 5. Validar el conjunto final de parámetros
  validate_parameters(params)

  return params
```

### 5.5. Checklist de Ejecución y Auditoría

Cada proceso de parametrización debe ser verificable.
*   [ ] **Fuente de Verdad Única**: ¿Se ha cargado un solo archivo de configuración de escenario para la ejecución?
*   [ ] **Trazabilidad de Parámetros**: ¿Es posible trazar el origen de cada parámetro final (runtime, escenario, contexto o default)?
*   [ ] **Validación Completa**: ¿Se ha ejecutado el proceso de validación sobre el conjunto final de parámetros?
*   [ ] **Manejo de Secretos**: ¿Se han manejado los parámetros sensibles (ej. API keys) de forma segura, sin exponerlos en logs o archivos de artefactos?
*   [ ] **Consistencia de Tipos**: ¿Coinciden los tipos de datos de los parámetros cargados con los tipos esperados por los métodos?
*   [ ] **Inmutabilidad**: Una vez cargados y validados, ¿permanecen los parámetros inmutables durante toda la ejecución del pipeline?

## 6. Protocolo de Integración en el Pipeline F.A.R.F.A.N.

El protocolo de integración define cómo los componentes individuales del modelo, ya calibrados y parametrizados, se ensamblan en un sistema cohesivo y ejecutable. Esta fase es crítica para asegurar que el comportamiento del conjunto sea consistente con el de sus partes.

### 6.1. Propósito y Objetivos de la Integración

El propósito de la integración es materializar el pipeline teórico en una secuencia de operaciones computacionales concretas. Sus objetivos son:
*   **Orquestación**: Definir el flujo de control y la secuencia de ejecución de los distintos módulos.
*   **Interoperabilidad**: Asegurar que los outputs de un módulo sean compatibles con los inputs del siguiente.
*   **Verificación End-to-End**: Validar el comportamiento del pipeline completo, desde la ingesta de datos hasta la generación de resultados finales.

### 6.2. Arquitectura de Módulos e Interfaces

El pipeline F.A.R.F.A.N. se compone de un conjunto de módulos especializados que interactúan a través de interfaces bien definidas. El siguiente diagrama ilustra la arquitectura de componentes.

<div class="constellation-map" style="position: relative; width: 600px; height: 450px; margin: auto; background: #0a0a0a; font-family: 'JetBrains Mono', monospace; border: 1px solid #222;">
  <style>
    .constellation-map { --atroz-red-500: #ef4444; --atroz-green-toxic: #65a30d; --atroz-blue-electric: #3b82f6; --atroz-copper-500: #a16207; --ink: #d4d4d4; }
    .node { position: absolute; width: 100px; height: 115.47px; background-color: var(--atroz-blue-electric); clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%); display: flex; justify-content: center; align-items: center; text-align: center; font-size: 10px; color: var(--ink); box-shadow: 0 0 10px rgba(59, 130, 246, 0.5); }
    .node-label { padding: 5px; }
  </style>
  <div class="node" style="top: 20px; left: 250px; background-color: var(--atroz-red-500);"><div class="node-label">Ingestor de Datos</div></div>
  <div class="node" style="top: 150px; left: 100px; background-color: var(--atroz-green-toxic);"><div class="node-label">Módulo de Calibración</div></div>
  <div class="node" style="top: 150px; left: 400px; background-color: var(--atroz-blue-electric);"><div class="node-label">Motor de Simulación</div></div>
  <div class="node" style="top: 300px; left: 250px; background-color: var(--atroz-copper-500);"><div class="node-label">Exporter de Resultados</div></div>
  <svg style="position:absolute;width:100%;height:100%;top:0;left:0;pointer-events:none;">
      <defs>
        <marker id="arrow-int" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#888" opacity="0.6"/>
        </marker>
      </defs>
      <line x1="300px" y1="80px" x2="160px" y2="190px" stroke="#888" stroke-width="0.5" marker-end="url(#arrow-int)"/>
      <line x1="300px" y1="80px" x2="440px" y2="190px" stroke="#888" stroke-width="0.5" marker-end="url(#arrow-int)"/>
      <line x1="160px" y1="210px" x2="440px" y2="210px" stroke="#888" stroke-width="0.5" marker-end="url(#arrow-int)"/>
      <line x1="450px" y1="230px" x2="310px" y2="340px" stroke="#888" stroke-width="0.5" marker-end="url(#arrow-int)"/>
  </svg>
</div>

*   **Ingestor de Datos**: Responsable de leer, parsear y preprocesar los PDT. Su output es una representación estructurada del documento.
*   **Módulo de Calibración**: Contiene la lógica para ejecutar el protocolo de calibración. Su output es el artefacto de parámetros calibrados (Θ*).
*   **Motor de Simulación**: Es el núcleo del pipeline. Recibe los datos estructurados, los parámetros de escenario y los parámetros calibrados para ejecutar los métodos de análisis.
*   **Exporter de Resultados**: Recopila los outputs del motor de simulación y los formatea en reportes, visualizaciones o archivos de datos para consumo externo.

### 6.3. Secuencia de Orquestación y Flujo de Control

La integración se materializa en un script orquestador (`master_orchestrator.py`) que define la secuencia de ejecución.
1.  **Fase de Inicialización**: Se cargan las configuraciones, se inicializan los loggers y se valida el entorno de ejecución.
2.  **Fase de Ingesta**: Se invoca al Ingestor de Datos para procesar el PDT de entrada. Se genera la representación estructurada.
3.  **Fase de Parametrización**: Se ejecuta el protocolo de parametrización para cargar y validar los parámetros del escenario.
4.  **Fase de Ejecución**: Se invoca al Motor de Simulación, pasándole la representación del PDT y los parámetros. El motor ejecuta la secuencia de métodos analíticos.
5.  **Fase de Reporte**: Se invoca al Exporter de Resultados para generar los artefactos de salida.
6.  **Fase de Finalización (Teardown)**: Se cierran los recursos y se asegura que todos los procesos han terminado limpiamente.

### 6.4. Código de Referencia y Pseudocódigo

El siguiente pseudocódigo ilustra la lógica principal del script orquestador.

```pseudocode
function main(pdt_path, scenario_config_path):
  // 1. Inicialización
  setup_environment()

  // 2. Ingesta
  structured_pdt = Ingestor.run(pdt_path)

  // 3. Parametrización
  runtime_parameters = load_parameters(scenario_config_path, structured_pdt)

  // 4. Ejecución del motor
  // Se asume que los parámetros de calibración (Θ*) ya están disponibles para el motor
  simulation_results = SimulationEngine.run(structured_pdt, runtime_parameters)

  // 5. Reporte
  Exporter.generate_reports(simulation_results)

  // 6. Finalización
  teardown_environment()
```

### 6.5. Checklist de Ejecución y Auditoría

La validación de la integración se realiza mediante un checklist que asegura el correcto funcionamiento del pipeline completo.
*   [ ] **Punto de Entrada Único**: ¿Se invoca todo el pipeline a través de un único punto de entrada (el script orquestador)?
*   [ ] **Contratos de Interfaz**: ¿Se validan los datos que se pasan entre los módulos principales (Ingestor → Motor → Exporter)?
*   [ ] **Manejo de Errores**: ¿El orquestador tiene un mecanismo para capturar y registrar errores fatales en cualquiera de las fases?
*   [ ] **Trazabilidad de la Ejecución**: ¿Se genera un log de ejecución que permita reconstruir la secuencia de llamadas y los parámetros utilizados?
*   [ ] **Verificación de Artefactos**: ¿Se comprueba la existencia y validez de los artefactos de salida (reportes, logs, datos)?
*   [ ] **Estado Idempotente**: ¿La ejecución del pipeline sobre los mismos inputs produce consistentemente los mismos outputs?

## 7. Discusión y Recomendaciones

El análisis comparativo de las fuentes canónicas (`canonic_calibration_methods.md`, `canonic_description_unit_analysis.json`) y las notas de implementación operativas (`raw`) revela varias divergencias y anti-patrones que deben ser gestionados para garantizar la robustez del pipeline F.A.R.F.A.N.

### 7.1. Análisis Crítico de Divergencias entre Canon y Práctica

La principal divergencia observada es la tendencia en la práctica, documentada en `raw`, a utilizar atajos y valores hardcoded que violan los principios del marco formal.
*   **Calibración Hardcoded vs. Dinámica**: Mientras el canon exige una calibración multi-capa dinámica, las notas de `raw` evidencian el uso de scores base fijos (ej. `base_score = 0.9`) como una solución temporal que, si no se gestiona, se convierte en deuda técnica permanente.
*   **Confusión Conceptual**: El archivo `raw` muestra una persistente confusión entre los conceptos de calibración (ajuste de la calidad intrínseca) y parametrización (configuración de escenario), lo que puede llevar a errores de implementación donde los parámetros de un escenario se codifican erróneamente como parte del comportamiento de un método.

### 7.2. Riesgos, Limitaciones y Anti-Patrones Identificados

Estos anti-patrones introducen riesgos significativos para el sistema.
*   **Riesgo de Opacidad**: El uso de valores mágicos o hardcoded hace que el comportamiento del modelo sea opaco y no auditable. Es imposible trazar por qué un método recibió un score determinado si dicho score está quemado en el código en lugar de ser el resultado de un proceso de evaluación explícito.
*   **Riesgo de Fragilidad**: La falta de una centralización estricta de la configuración (parámetros y calibraciones) conduce a un sistema frágil. Un cambio en un parámetro requiere una búsqueda manual en todo el código base, con un alto riesgo de introducir inconsistencias.
*   **Limitación por Entropía Documental**: El uso de un archivo de notas no estructurado como `raw` para guiar la implementación es insostenible. La información es redundante, a menudo contradictoria y carece de un control de versiones semántico, lo que lo convierte en una fuente de errores.

### 7.3. Recomendaciones para Mantenimiento y Futuras Extensiones

Para mitigar estos riesgos y asegurar la escalabilidad del sistema, se emiten las siguientes recomendaciones de carácter obligatorio.
1.  **Centralización Absoluta de la Configuración**: Se debe prohibir terminantemente la existencia de cualquier valor de calibración o parametrización dentro del código fuente. Todos los scores de calibración intrínseca deben residir en `intrinsic_calibration.json`, y todos los parámetros de escenario en archivos de configuración dedicados (ej. `production.json`).
2.  **Implementación de un Validador de Anclaje**: Se debe desarrollar un script de validación, para ser ejecutado en el pipeline de CI/CD, que escanee el código base en busca de valores hardcoded y falle el build si se detecta alguna violación. Todos los métodos deben "anclarse" al sistema central de configuración y calibración.
3.  **Deprecación de Fuentes No Canónicas**: El archivo `raw` debe ser considerado obsoleto y archivado. Cualquier información de valor que contenga debe ser migrada a este compendio o a la documentación oficial. No debe ser utilizado como referencia para futuras implementaciones.
4.  **Adopción de un Flujo Basado en Contratos**: Las futuras extensiones del sistema deben seguir un flujo de desarrollo basado en contratos, donde la especificación formal (como este compendio) precede a la implementación, y la implementación es continuamente validada contra dicha especificación.

## 8. Anexos

### Anexo A: Notación Matemática Canónica (Detallada)

Este anexo detalla la notación formal utilizada en el marco de calibración, extraída de `canonic_calibration_methods.md`.

*   **Grafo Computacional (\\(\\Gamma\\))**: \\(\\Gamma = (V, E, T, S)\\)
    *   \\(V\\): Conjunto de nodos (instancias de métodos).
    *   \\(E\\): Conjunto de aristas dirigidas acíclicas (flujo de datos).
    *   \\(T\\): Función de tipado de aristas.
    *   \\(S\\): Función de signatura de nodos.
*   **Contexto de Análisis (\\(\\text{ctx}\\))**: \\(\\text{ctx} = (Q, D, P, U)\\)
    *   \\(Q\\): Identificador de la pregunta.
    *   \\(D\\): Dimensión analítica.
    *   \\(P\\): Área de política.
    *   \\(U\\): Calidad de la unidad de análisis \\(\\in [0,1]\\).
*   **Instancia de Calibración (\\(I\\))**: \\(I = (M, v, \\Gamma, G, \\text{ctx})\\)
    *   \\(M\\): Artefacto de código del método.
    *   \\(v\\): Nodo específico en el grafo.
    *   \\(\\Gamma\\): Grafo contenedor.
    *   \\(G\\): Subgrafo de interacciones.
    *   \\(\\text{ctx}\\): Contexto de ejecución.
*   **Función de Calibración (\\(Cal(I)\\))**:
    \\[ Cal(I) = \\sum_{\\ell \\in L(M)} a_{\\ell} \\cdot x_{\\ell}(I) + \\sum_{(\\ell,k) \\in S_{int}} a_{\\ell k} \\cdot \\min(x_{\\ell}(I), x_{k}(I)) \\]
    *   \\(x_{\\ell}(I)\\): Score de la capa \\(\\ell\\).
    *   \\(a_{\\ell}, a_{\\ell k}\\): Coeficientes de ponderación normalizados.

### Anexo B: Tablas Completas de la Unidad de Análisis

Este anexo proporciona tablas detalladas derivadas de `canonic_description_unit_analysis.json`.

*(Esta sección puede ser expandida con todas las tablas del JSON. Por brevedad, se omite la repetición completa).*

### Anexo C: Ejemplos de Scripts Completos

*(Esta sección está reservada para incluir ejemplos completos de scripts de orquestación, calibración y parametrización, que sirvan como referencia para los mantenedores del sistema).*

### Anexo D: Tabla de Trazabilidad Conceptual: `raw` vs. Compendio

| Sección del Compendio                                      | Bloque(s) de `raw` de Origen (Conceptual)                                                                     | Nota Editorial                                                                                                       |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **4. Protocolo de Calibración**                            | Discusiones sobre `execute_with_optimization`, `method skipping`, `_calibration` field, y `FILLING_THE_GAPS`. | Se ha sintetizado el flujo de trabajo implícito, eliminando la metaconversación y formalizando los pasos.       |
| **5. Protocolo de Parametrización**                        | Discusiones sobre `ExecutorConfig`, `CONSERVATIVE_CONFIG`, y la carga de parámetros desde el entorno o JSON.     | Se ha extraído la jerarquía de fuentes de configuración y se ha formalizado el pipeline de carga y validación. |
| **6. Protocolo de Integración**                            | Menciones a `FrontierExecutorOrchestrator`, `factory.py`, y la inyección de `MethodExecutor`.                   | Se ha reconstruido la arquitectura de componentes y el flujo de orquestación a partir de fragmentos dispersos.     |
| **7.1. Divergencias Canon vs. Práctica**                    | Múltiples referencias al uso de stubs (ej. `returns 1.0`), scores hardcoded y la necesidad de "rellenar gaps". | Se ha utilizado esta evidencia para formular el análisis crítico sobre la deuda técnica y los anti-patrones.   |

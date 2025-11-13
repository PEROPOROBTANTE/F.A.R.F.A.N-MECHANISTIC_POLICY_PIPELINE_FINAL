# 📊 TAXONOMÍA MESO - Policy Subsystem Clusters

## Canonical MESO-Level Structure for PDM Analysis

**Version:** 2.0.0  
**Status:** Immutable Taxonomy  
**Last Updated:** 2025-10-22

---

## 🎯 PURPOSE

The MESO level exists to model **policy subsystems** that connect multiple policy areas without dissolving into macro-level abstraction or fragmenting into micro-level questions. This requires an **explicit intermediate layer** with:

- Entities with canonical IDs
- Immutable composition rules  
- Computable aggregation logic
- Imbalance detection mechanisms

---

## 🔒 IMMUTABLE CLUSTER TAXONOMY

The system defines **exactly 4 clusters** with fixed composition. This closed taxonomy is defined in `questionnaire.json` metadata and **must not** be modified ad hoc in code modules.

### **CL01: Seguridad y Paz** (Security and Peace)

**Rationale:** Seguridad humana, protección de la vida y paz territorial  
**Policy Areas:**
- **PA01:** Prevención violencia y protección ante conflicto/GDO
- **PA02:** Derechos de víctimas y construcción de paz
- **PA03:** Líderes y defensores de DD. HH.

### **CL02: Grupos Poblacionales** (Population Groups)

**Rationale:** Enfoque diferencial y derechos de grupos específicos  
**Policy Areas:**
- **PA04:** Mujeres e igualdad de género
- **PA05:** Niñez-juventud-familia
- **PA06:** Personas privadas de la libertad

### **CL03: Territorio-Ambiente** (Territory-Environment)

**Rationale:** Sostenibilidad territorial y gestión ambiental  
**Policy Areas:**
- **PA07:** Ambiente-clima-desastres
- **PA08:** Tierras y territorios

### **CL04: Derechos Sociales & Crisis** (Social Rights & Crisis)

**Rationale:** Derechos económicos, sociales y culturales + gestión de crisis  
**Policy Areas:**
- **PA09:** DESC (Derechos Económicos, Sociales y Culturales)
- **PA10:** Migración transfronteriza

---

## 🏗️ CANONICAL ID NOTATION

To avoid ambiguity, the system enforces strict ID notation across all files:

| Entity | Pattern | Example | Range |
|--------|---------|---------|-------|
| **Cluster** | `CLxx` | `CL01` | CL01-CL04 |
| **Policy Area** | `PAxx` | `PA05` | PA01-PA10 |
| **Dimension** | `DIMxx` | `DIM03` | DIM01-DIM06 |
| **Question** | `Qxxx` | `Q042` | Q001-Q300 |

**Important:** Legacy notation (P1-P10, D1-D6) is being migrated to canonical notation.

---

## 📐 AGGREGATION HIERARCHY

The system implements a three-level aggregation:

```
Question (Qxxx) 
    ↓ [weighted by dimension]
Policy Area (PAxx)
    ↓ [weighted by policy area]
Cluster (CLxx)
    ↓ [weighted by cluster]
Macro (Overall Score)
```

### **Q → PA Aggregation**

Each question score is aggregated to its parent policy area using dimension-specific weights defined in `rubric_scoring.json`:

```json
"question_to_policy_area": {
  "PA01": {
    "method": "weighted_average",
    "weights": {
      "DIM01": 0.20,  // Diagnóstico
      "DIM02": 0.20,  // Estrategia
      "DIM03": 0.15,  // Programación
      "DIM04": 0.15,  // Resultados
      "DIM05": 0.15,  // Impactos
      "DIM06": 0.15   // Causalidad
    }
  }
}
```

### **PA → CL Aggregation**

Policy area scores are aggregated to clusters using policy area weights:

```json
"policy_area_to_cluster": {
  "CL01": {
    "method": "weighted_average",
    "weights": {
      "PA01": 0.40,  // Higher weight for violence prevention
      "PA02": 0.35,  // Peace construction
      "PA03": 0.25   // Human rights defenders
    },
    "imbalance_threshold": 30.0  // τ = 30 points
  }
}
```

### **CL → Macro Aggregation**

Cluster scores aggregate to overall plan score:

```json
"cluster_to_macro": {
  "method": "weighted_average",
  "weights": {
    "CL01": 0.30,  // Security and peace (highest priority)
    "CL02": 0.25,  // Population groups
    "CL03": 0.25,  // Territory-environment
    "CL04": 0.20   // Social rights & crisis
  }
}
```

---

## 📊 IMBALANCE DETECTION

The choreographer **must** calculate intra-cluster dispersion metrics for each cluster:

### **Metrics Required**

1. **Range:** `max(PA_scores) - min(PA_scores)`
2. **Standard Deviation (σ):** Dispersion of PA scores
3. **Gini Coefficient:** Inequality measure (0-1)

### **Flagging Conditions**

A cluster is flagged as **"HIGH IMBALANCE"** if:

```
range >= imbalance_threshold (τ)
```

Where `τ` is defined per cluster in `rubric_scoring.json` (typically 25-35 points).

### **Example:**

```python
CL01_scores = {
  "PA01": 75.0,  # Violence prevention
  "PA02": 45.0,  # Peace (WEAK!)
  "PA03": 70.0   # Human rights defenders
}

range = 75.0 - 45.0 = 30.0
threshold = 30.0

# Result: HIGH IMBALANCE flagged
# Weak area: PA02 (Peace construction)
```

---

## 🎯 RECOMMENDATION GRAMMAR

Recommendations must follow a **computable template**, not rhetorical text:

### **Template Structure**

```
IF (score_CLxx < UMBRAL) OR (desbalance_CLxx = Alto)
THEN Recomendar[Acción específica] := 
    (Problema concreto vinculado a PAxx débil) → 
    (Intervención factible intersectorial) → 
    (Indicador/Meta verificable) → 
    (Responsable & Horizonte) → 
    (Fuentes de verificación)
```

### **Example Implementation**

For `CL01` with high imbalance (weak PA02):

```json
{
  "condition": {
    "type": "high_imbalance",
    "threshold": 30.0,
    "weak_policy_area": "PA02"
  },
  "action_template": {
    "problem": "Debilidad crítica en construcción de paz (PA02: 45/100)",
    "intervention": "Fortalecer estrategias de reconciliación y justicia transicional con enfoque territorial",
    "indicator": "% de víctimas con acceso a mecanismos de reparación",
    "responsible": "Secretaría de Paz / Consejería Presidencial",
    "timeframe": "12 meses",
    "verification_sources": [
      "Registro Único de Víctimas (RUV)",
      "Informes de implementación PAR",
      "Encuestas de percepción ciudadana"
    ]
  }
}
```

---

## 🔄 DATA FLOW

### **Configuration Files**

1. **`questionnaire.json`** (Canonical Truth)
   - Defines 4 clusters with rationale
   - Lists 10 policy areas with names
   - Defines 6 dimensions
   - Contains 300 questions with PA/DIM mappings

2. **`rubric_scoring.json`** (Scoring Logic)
   - Aggregation methods (Q→PA→CL→Macro)
   - Weights for each level
   - Imbalance thresholds per cluster
   - Recommendation rule templates

3. **`responsibility_map.json`** (Provenance)
   - Maps each Qxxx to responsible modules
   - Inherits PAxx and CLxx from questionnaire

### **Choreographer Role**

The choreographer is the **procedural assembler**:

1. **Ingest** modular evidence from 9 producers
2. **Align** evidence to Qxxx questions
3. **Aggregate** Q→PA using dimension weights
4. **Aggregate** PA→CL using policy area weights
5. **Calculate** dispersion metrics (range, σ, Gini)
6. **Flag** high imbalance conditions
7. **Select** recommendation rules from rubric
8. **Emit** scored response with complete traceability

**No heuristics hidden in code** - all weights come from metadata or rubric.

---

## 🧪 VALIDATION RULES

Schema validation enforces:

✅ **Referential Integrity**
- All PAxx referenced by CLxx must exist in policy_areas
- Every Qxxx must map to exactly one PAxx and one DIMxx

✅ **Coverage Completeness**
- All 10 policy areas (PA01-PA10) must have ≥1 question
- No orphaned policy areas

✅ **Taxonomy Immutability**
- Exactly 4 clusters (CL01-CL04)
- Exactly 10 policy areas (PA01-PA10)  
- Exactly 6 dimensions (DIM01-DIM06)

✅ **Version Compatibility**
- `rubric_scoring.json` declares compatible questionnaire version
- Versions must match for execution

---

## 📝 USAGE IN CODE

### **Loading Clusters**

```python
from metadata_loader import MetadataLoader

loader = MetadataLoader("questionnaire.json")
clusters = loader.get_clusters()

for cluster in clusters:
    cluster_id = cluster["cluster_id"]  # CL01
    name = cluster["name"]  # Seguridad y Paz
    rationale = cluster["rationale"]
    policy_areas = cluster["policy_area_ids"]  # [PA01, PA02, PA03]
```

### **Aggregating Scores**

```python
from choreographer import ExecutionChoreographer

# Q→PA aggregation
pa_scores = choreographer.aggregate_questions_to_policy_area(
    question_results,
    policy_area_id="PA01",
    weights=rubric["aggregation_rules"]["question_to_policy_area"]["PA01"]["weights"]
)

# PA→CL aggregation with imbalance detection
cl_result = choreographer.aggregate_policy_areas_to_cluster(
    policy_area_scores,
    cluster_id="CL01",
    weights=rubric["aggregation_rules"]["policy_area_to_cluster"]["CL01"]["weights"],
    imbalance_threshold=rubric["aggregation_rules"]["policy_area_to_cluster"]["CL01"]["imbalance_threshold"]
)

# Check imbalance
if cl_result["is_high_imbalance"]:
    weak_pa = cl_result["weakest_policy_area"]
    # Trigger recommendation rules
```

### **Generating Recommendations**

```python
# Select recommendation rule
cluster_id = "CL01"
weak_pa = "PA02"  # Peace construction

rules = rubric["recommendation_rules"][cluster_id]
matching_rule = [r for r in rules if r["condition"]["weak_policy_area"] == weak_pa][0]

# Instantiate template with plan data
recommendation = {
    "problem": matching_rule["action_template"]["problem"],
    "intervention": matching_rule["action_template"]["intervention"],
    "indicator": matching_rule["action_template"]["indicator"],
    "responsible": matching_rule["action_template"]["responsible"],
    "timeframe": matching_rule["action_template"]["timeframe"],
    "verification_sources": matching_rule["action_template"]["verification_sources"]
}
```

---

## 🔍 VERIFICATION

Every execution must generate a `trace.json` containing:

```json
{
  "metadata": {
    "questionnaire_checksum": "sha256:...",
    "rubric_checksum": "sha256:...",
    "schema_versions": {
      "questionnaire": "2.0.0",
      "rubric": "2.0.0"
    }
  },
  "mapping": {
    "Q001": {"policy_area": "PA01", "cluster": "CL01", "dimension": "DIM01"},
    "Q002": {"policy_area": "PA01", "cluster": "CL01", "dimension": "DIM02"}
  },
  "aggregation": {
    "weights_applied": {
      "Q_to_PA": {...},
      "PA_to_CL": {...},
      "CL_to_Macro": {...}
    },
    "imbalance_metrics": {
      "CL01": {"range": 30.0, "std_dev": 12.5, "gini": 0.18},
      "CL02": {"range": 15.0, "std_dev": 6.2, "gini": 0.09}
    }
  },
  "recommendations": {
    "triggered_rules": [
      {"cluster": "CL01", "rule_id": "high_imbalance_PA02", "action": {...}}
    ]
  }
}
```

---

## 📚 REFERENCES

- `schemas/questionnaire.schema.json` - Schema definition
- `schemas/rubric_scoring.schema.json` - Rubric schema
- `questionnaire.json` - Canonical truth model
- `rubric_scoring.json` - Scoring configuration
- `schema_validator.py` - Validation engine
- `orchestrator.py` - MESO orchestration
- `choreographer.py` - Procedural assembly
- `report_assembly.py` - MESO rendering

---

**Document Version:** 2.0.0  
**Author:** Integration Team  
**Status:** Normative - All implementations must comply

#!/usr/bin/env python3
"""Migrate legacy policy analysis configuration to atomic ID v2 format.

This script converts the historical questionnaire.json and rubric_scoring.json
files that used P#/D#/Q# identifiers into the new canonical data contracts that
use PAxx/DIMxx/Qxxx identifiers. It also normalises structure, injects i18n
metadata, and computes deterministic content hashes for reproducible builds.

Usage
-----
python tools/migrations/migrate_ids_v1_to_v2.py \
    --questionnaire questionnaire.json \
    --rubric rubric_scoring.json \
    --execution-mapping execution_mapping.yaml \
    --write  # Persist changes (omit for dry-run)
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import sys
from collections import Counter, defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

ROOT = Path(__file__).resolve().parents[2]

LEGACY_POLICY_AREAS = [f"P{i}" for i in range(1, 11)]
LEGACY_DIMENSIONS = [f"D{i}" for i in range(1, 7)]

POLICY_AREA_IDS = [f"PA{i:02d}" for i in range(1, 11)]
DIMENSION_IDS = [f"DIM{i:02d}" for i in range(1, 7)]

SOURCES_CATALOG = [
    {
        "key": "official_stats",
        "type": "primary",
        "format": "stat",
        "auth_level": "official",
        "description": "Series estadísticas oficiales desagregadas por sexo, edad y territorio.",
    },
    {
        "key": "official_documents",
        "type": "primary",
        "format": "narrative",
        "auth_level": "official",
        "description": "Actos administrativos, planes sectoriales y acuerdos municipales vigentes.",
    },
    {
        "key": "monitoring_tables",
        "type": "primary",
        "format": "table",
        "auth_level": "official",
        "description": "Tableros de seguimiento con metas, responsables y ejecución presupuestal.",
    },
    {
        "key": "third_party_research",
        "type": "secondary",
        "format": "narrative",
        "auth_level": "third_party",
        "description": "Investigaciones académicas y evaluaciones externas con evidencia empírica.",
    },
    {
        "key": "geo_maps",
        "type": "secondary",
        "format": "map",
        "auth_level": "official",
        "description": "Capas geoespaciales oficiales (IGAC, IDEAM, UNGRD) con proyección EPSG:3116.",
    },
]

POLICY_AREA_EVIDENCE_KEYS = {
    "PA01": ["official_stats", "official_documents", "third_party_research"],
    "PA02": ["official_stats", "monitoring_tables", "official_documents"],
    "PA03": ["official_stats", "official_documents", "geo_maps"],
    "PA04": ["official_stats", "geo_maps", "official_documents"],
    "PA05": ["official_stats", "monitoring_tables", "third_party_research"],
    "PA06": ["official_documents", "third_party_research", "monitoring_tables"],
    "PA07": ["official_stats", "official_documents", "monitoring_tables"],
    "PA08": ["geo_maps", "official_documents", "official_stats"],
    "PA09": ["official_stats", "official_documents", "monitoring_tables"],
    "PA10": ["official_stats", "third_party_research", "official_documents"],
}

ALL_EVIDENCE_KEYS = sorted({key for keys in POLICY_AREA_EVIDENCE_KEYS.values() for key in keys})

DEFAULT_MODALITY_NA_RULES = {
    "TYPE_A": {"imputation": "mean", "scope": "dimension", "exclude_from_global": False},
    "TYPE_B": {"imputation": "mean", "scope": "dimension", "exclude_from_global": False},
    "TYPE_C": {"imputation": "median", "scope": "dimension", "exclude_from_global": False},
    "TYPE_D": {"imputation": "zero", "scope": "dimension", "exclude_from_global": False},
    "TYPE_E": {"imputation": "none", "scope": "policy_area", "exclude_from_global": False},
    "TYPE_F": {"imputation": "none", "scope": "policy_area", "exclude_from_global": True},
}

ROUNDING_RULES = {
    "question": {"mode": "half_up", "precision": 2},
    "dimension": {"mode": "half_up", "precision": 2},
    "policy_area": {"mode": "half_up", "precision": 1},
    "cluster": {"mode": "half_up", "precision": 1},
    "macro": {"mode": "half_up", "precision": 1},
}

UNCERTAINTY_POLICY = {
    "method": "bootstrap",
    "alpha": 0.05,
    "propagation": "weighted",
    "iterations": 2000,
}

PENALTY_RULES = {
    "contradictory_info": {"weight": 0.06},
    "missing_indicator": {"weight": 0.04},
    "OOD_flag": {"weight": 0.05},
}

IMBALANCE_POLICY = {
    "method": "gini",
    "gini_formula": "2*sum(i*xi)/(n*sum(xi)) - (n+1)/n",
    "std_dev_formula": "sqrt(sum((xi - mean)^2)/n)",
    "range_formula": "max(xi) - min(xi)",
    "thresholds": {
        "CL01": {"gini": 0.3, "std_dev": 12.0, "range": 35.0, "action": "penalize"},
        "CL02": {"gini": 0.28, "std_dev": 10.0, "range": 32.0, "action": "penalize"},
        "CL03": {"gini": 0.27, "std_dev": 9.0, "range": 28.0, "action": "flag"},
        "CL04": {"gini": 0.29, "std_dev": 11.0, "range": 30.0, "action": "penalize"},
    },
}

RECOMMENDATION_RULES = [
    {
        "cluster_id": "CL01",
        "condition": {"type": "low_score", "threshold": 60},
        "action": {
            "problem": "Déficit crítico en capacidades de seguridad y justicia local.",
            "intervention": "Implementar comités interinstitucionales con trazabilidad presupuestal.",
            "indicator": "Porcentaje de denuncias judicializadas con atención integral.",
            "owner": "Secretaría de Seguridad",
            "timeframe": "2025-Q2",
        },
    },
    {
        "cluster_id": "CL02",
        "condition": {"type": "high_imbalance", "threshold": 0.3},
        "action": {
            "problem": "Desbalance en enfoque diferencial y coberturas para población vulnerable.",
            "intervention": "Reasignar recursos a programas de inclusión con metas específicas.",
            "indicator": "Número de hogares con atención integral en rutas diferenciales.",
            "owner": "Secretaría de Desarrollo Social",
            "timeframe": "2025-Q3",
        },
    },
    {
        "cluster_id": "CL03",
        "condition": {"type": "combined", "threshold": 65},
        "action": {
            "problem": "Resultados ambientales inconsistentes con metas de mitigación.",
            "intervention": "Activar mesa técnica intersectorial para control de deforestación.",
            "indicator": "Hectáreas restauradas con monitoreo IDEAM.",
            "owner": "Secretaría de Ambiente",
            "timeframe": "2025-Q4",
        },
    },
    {
        "cluster_id": "CL04",
        "condition": {"type": "low_score", "threshold": 55},
        "action": {
            "problem": "Protección social insuficiente ante choques migratorios y sanitarios.",
            "intervention": "Implementar plan de contingencia con red hospitalaria y ayudas humanitarias.",
            "indicator": "Tiempo promedio de respuesta ante emergencias sociales.",
            "owner": "Secretaría de Salud",
            "timeframe": "2025-Q1",
        },
    },
]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questionnaire", type=Path, default=ROOT / "questionnaire.json")
    parser.add_argument("--rubric", type=Path, default=ROOT / "rubric_scoring.json")
    parser.add_argument(
        "--execution-mapping",
        type=Path,
        default=ROOT / "execution_mapping.yaml",
        dest="execution_mapping",
    )
    parser.add_argument("--write", action="store_true", help="Persist migrated artifacts")
    parser.add_argument("--output-dir", type=Path, default=None, help="Optional output directory")
    return parser.parse_args()

def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)

def canonical_hash(payload: Mapping[str, Any]) -> str:
    serialisable = json.loads(json.dumps(payload, ensure_ascii=False))
    serialisable = dict(serialisable)
    serialisable.pop("content_hash", None)
    canonical = json.dumps(serialisable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def dump_json(path: Path, payload: Mapping[str, Any]) -> None:
    payload = copy.deepcopy(payload)
    payload["content_hash"] = canonical_hash(payload)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")

def map_policy_area(legacy_id: str) -> str:
    index = LEGACY_POLICY_AREAS.index(legacy_id)
    return POLICY_AREA_IDS[index]

def map_dimension(legacy_id: str) -> str:
    index = LEGACY_DIMENSIONS.index(legacy_id)
    return DIMENSION_IDS[index]

def decimal_normalised(value: float, digits: int = 6) -> float:
    quant = Decimal(value).quantize(Decimal(10) ** -digits, rounding=ROUND_HALF_UP)
    return float(quant)

def build_i18n(label_es: str, label_en: str | None = None) -> dict[str, Any]:
    if label_en is None:
        label_en = label_es
    return {
        "default": "es",
        "keys": {
            "label_es": label_es,
            "label_en": label_en,
        },
    }

def migrate_questionnaire(
    questionnaire: dict[str, Any],
    legacy_modalities: Mapping[str, str] | None = None,
    legacy_policy_area_labels: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, str], dict[str, str], dict[str, list[str]]]:
    metadata = questionnaire.get("metadata", {})
    legacy_clusters = metadata.get("clusters", [])
    legacy_dimensions = questionnaire.get("dimensiones", {})
    questions = questionnaire.get("preguntas_base", [])

    pa_mapping = {legacy: map_policy_area(legacy) for legacy in LEGACY_POLICY_AREAS}
    dim_mapping = {legacy: map_dimension(legacy) for legacy in LEGACY_DIMENSIONS}

    cluster_by_pa: dict[str, str] = {}
    clusters: list[dict[str, Any]] = []
    for cluster in legacy_clusters:
        cluster_id = cluster["cluster_id"]
        pa_ids = []
        for raw in cluster.get("policy_area_ids", []):
            if raw in pa_mapping:
                pa_ids.append(pa_mapping[raw])
            elif raw in POLICY_AREA_IDS:
                pa_ids.append(raw)
        if not pa_ids and cluster.get("legacy_point_ids"):
            for raw in cluster.get("legacy_point_ids", []):
                if raw in pa_mapping:
                    pa_ids.append(pa_mapping[raw])
        for pa_id in pa_ids:
            cluster_by_pa[pa_id] = cluster_id
        legacy_ids = [raw for raw in cluster.get("legacy_point_ids", []) if raw in pa_mapping]
        if not legacy_ids:
            legacy_ids = [raw for raw in cluster.get("policy_area_ids", []) if raw in LEGACY_POLICY_AREAS]

        clusters.append(
            {
                "cluster_id": cluster_id,
                "i18n": build_i18n(cluster["name"], cluster["name"]),
                "rationale": cluster.get("rationale", ""),
                "policy_area_ids": pa_ids,
                "legacy_policy_area_ids": legacy_ids,
            }
        )

    policy_area_names: dict[str, str] = dict(legacy_policy_area_labels or {})
    for question in questions:
        pa_name = question.get("policy_area_name")
        legacy_pa = question.get("id", "").split("-")[0]
        if legacy_pa and pa_name and legacy_pa not in policy_area_names:
            policy_area_names[legacy_pa] = pa_name

    policy_area_entries: list[dict[str, Any]] = []
    for legacy_id in LEGACY_POLICY_AREAS:
        policy_area_id = pa_mapping[legacy_id]
        policy_area_entries.append(
            {
                "policy_area_id": policy_area_id,
                "legacy_ids": [legacy_id],
                "i18n": build_i18n(policy_area_names.get(legacy_id, legacy_id)),
                "cluster_id": cluster_by_pa.get(policy_area_id, ""),
                "dimension_ids": DIMENSION_IDS,
                "required_evidence_keys": POLICY_AREA_EVIDENCE_KEYS[policy_area_id],
            }
        )

    dimension_entries: list[dict[str, Any]] = []
    for legacy_dim, dim_payload in legacy_dimensions.items():
        dim_id = dim_mapping[legacy_dim]
        dimension_entries.append(
            {
                "dimension_id": dim_id,
                "legacy_id": legacy_dim,
                "i18n": build_i18n(dim_payload.get("nombre", legacy_dim)),
                "description": dim_payload.get("descripcion", ""),
            }
        )

    question_entries: list[dict[str, Any]] = []
    legacy_to_new_qid: dict[str, str] = {}
    policy_area_sequence: dict[str, int] = defaultdict(int)
    combination_sequence: dict[tuple[str, str], int] = defaultdict(int)

    questions_sorted = sorted(questions, key=lambda q: q.get("id", ""))
    for index, question in enumerate(questions_sorted, start=1):
        legacy_id = question.get("id")
        if not legacy_id:
            continue
        legacy_pa, legacy_dim, legacy_q = legacy_id.split("-")
        policy_area_id = pa_mapping[legacy_pa]
        dimension_id = dim_mapping[legacy_dim]
        cluster_id = cluster_by_pa.get(policy_area_id, "")

        global_order = index
        policy_area_sequence[policy_area_id] += 1
        combination_key = (policy_area_id, dimension_id)
        combination_sequence[combination_key] += 1

        question_id = f"Q{index:03d}"
        legacy_to_new_qid[legacy_id] = question_id

        modality = "TYPE_A"
        if legacy_modalities and legacy_id in legacy_modalities:
            modality = legacy_modalities[legacy_id]

        question_entries.append(
            {
                "question_id": question_id,
                "legacy_id": legacy_id,
                "policy_area_id": policy_area_id,
                "dimension_id": dimension_id,
                "cluster_id": cluster_id,
                "order": {
                    "global": global_order,
                    "within_policy_area": policy_area_sequence[policy_area_id],
                    "within_policy_area_dimension": combination_sequence[combination_key],
                },
                "question_text": question.get("texto_template", ""),
                "i18n": build_i18n(question.get("texto_template", "")),
                "scoring_modality": modality,
                "required_evidence_keys": POLICY_AREA_EVIDENCE_KEYS[policy_area_id],
                "evidence_expectations": question.get("criterios_evaluacion", {}),
                "search_patterns": {
                    "regex": question.get("patrones_verificacion", []),
                },
                "scoring_criteria": question.get("scoring", {}),
                "validation_checks": question.get("verificacion_lineas_base", {}),
            }
        )

    title = metadata.get("title", "Configuración de 300 Preguntas - Sistema de Evaluación Causal FARFAN 3.0")
    description = metadata.get("description", "")

    migrated = {
        "version": "3.0.0",
        "provenance": {
            "author": "Data Contracts Team",
            "tool": "migrate_ids_v1_to_v2.py",
            "edited_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        },
        "changelog": [
            {
                "version": "3.0.0",
                "summary": "Migración a identificadores atómicos y estructura normalizada",
                "reason": "Data contract hardening",
            }
        ],
        "metadata": {
            "default_language": "es",
            "title": build_i18n(title, "Policy Evaluation Questionnaire"),
            "description": description,
            "policy_areas": policy_area_entries,
            "dimensions": dimension_entries,
            "clusters": clusters,
            "sources_of_verification": SOURCES_CATALOG,
        },
        "questions": question_entries,
    }

    return migrated, legacy_to_new_qid, pa_mapping, cluster_by_pa

def weight_vector_from_mapping(mapping: Mapping[str, Any], pa_mapping: Mapping[str, str]) -> dict[str, dict[str, float]]:
    weights_by_pa: dict[str, dict[str, float]] = {}
    for legacy_dim, payload in mapping.items():
        dim_id = map_dimension(legacy_dim)
        deca_map = payload.get("decalogo_dimension_mapping", {})
        for legacy_pa, details in deca_map.items():
            pa_id = pa_mapping[legacy_pa]
            weights_by_pa.setdefault(pa_id, {})[dim_id] = decimal_normalised(details.get("weight", 0.0))
    return {pa_id: normalise_weights(dim_weights) for pa_id, dim_weights in weights_by_pa.items()}

def normalise_weights(weights: Mapping[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if not total:
        return dict.fromkeys(weights, 0.0)
    return {k: decimal_normalised(v / total) for k, v in weights.items()}

def migrate_rubric(
    rubric: dict[str, Any],
    legacy_questionnaire: dict[str, Any],
    migrated_questionnaire: dict[str, Any],
    legacy_to_new_qid: Mapping[str, str],
    pa_mapping: Mapping[str, str],
    _cluster_by_pa: Mapping[str, str],
) -> dict[str, Any]:
    legacy_dimensions = legacy_questionnaire.get("dimensiones", {})
    modality_definitions = rubric.get("scoring_modalities", {})
    legacy_questions = rubric.get("questions", [])
    cluster_weights = rubric.get("meso_clusters", {})
    aggregation_levels = rubric.get("aggregation_levels", {})

    question_modality: dict[str, str] = {}
    for question in legacy_questions:
        legacy_id = question.get("id")
        modality = question.get("scoring_modality", "TYPE_A")
        if legacy_id and legacy_id in legacy_to_new_qid:
            question_modality[legacy_to_new_qid[legacy_id]] = modality

    # Build rubric matrix with allowed modalities per PA/DIM
    modality_counter: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for legacy_id, new_qid in legacy_to_new_qid.items():
        pa_legacy, dim_legacy, _ = legacy_id.split("-")
        pa_id = pa_mapping[pa_legacy]
        dim_id = map_dimension(dim_legacy)
        modality = question_modality.get(new_qid, "TYPE_A")
        modality_counter[(pa_id, dim_id)][modality] += 1

    rubric_matrix: dict[str, dict[str, Any]] = {}
    for pa_id in POLICY_AREA_IDS:
        rubric_matrix[pa_id] = {}
        for dim_id in DIMENSION_IDS:
            counter = modality_counter.get((pa_id, dim_id), Counter({"TYPE_A": 1}))
            allowed = sorted(counter.keys())
            default_modality = max(counter.items(), key=lambda kv: kv[1])[0]
            rubric_matrix[pa_id][dim_id] = {
                "default_modality": default_modality,
                "allowed_modalities": allowed,
                "required_evidence_keys": POLICY_AREA_EVIDENCE_KEYS[pa_id],
            }

    # Build dimension -> question weights
    dimension_question_weights: dict[str, dict[str, float]] = {dim: {} for dim in DIMENSION_IDS}
    for question in migrated_questionnaire["questions"]:
        dim_id = question["dimension_id"]
        qid = question["question_id"]
        dimension_question_weights[dim_id].setdefault(qid, 0.0)

    for _dim_id, questions_dict in dimension_question_weights.items():
        count = len(questions_dict)
        if not count:
            continue
        weight = decimal_normalised(1 / count)
        for qid in list(questions_dict.keys()):
            questions_dict[qid] = weight

    # Policy area -> dimension weights
    policy_area_dimension_weights = weight_vector_from_mapping(legacy_dimensions, pa_mapping)

    # Cluster weights (policy areas within cluster)
    cluster_policy_area_weights: dict[str, dict[str, float]] = {}
    for cluster_id, payload in cluster_weights.items():
        pa_weights = {pa_mapping[pa]: weight for pa, weight in payload.get("weights", {}).items()}
        cluster_policy_area_weights[cluster_id] = {
            pa_id: decimal_normalised(weight) for pa_id, weight in normalise_weights(pa_weights).items()
        }

    macro_weights = aggregation_levels.get("level_4", {}).get("cluster_weights", {})
    macro_cluster_weights = {cluster: decimal_normalised(weight) for cluster, weight in normalise_weights(macro_weights).items()}

    # Scoring modalities enriched metadata
    scoring_modalities: dict[str, Any] = {}
    for modality_id, payload in modality_definitions.items():
        enriched = {
            "name": payload.get("id", modality_id),
            "description": payload.get("description", ""),
            "score_range": {
                "min": 0.0,
                "max": payload.get("max_score", 3.0),
            },
            "rounding": ROUNDING_RULES["question"],
            "required_evidence_keys": ALL_EVIDENCE_KEYS,
        }
        if "expected_elements" in payload:
            enriched["expected_elements"] = payload["expected_elements"]
        if "conversion_table" in payload:
            enriched["conversion_table"] = payload["conversion_table"]
        if payload.get("uses_semantic_matching"):
            enriched["determinism"] = {"seed_required": True, "seed_source": "seed_factory_v1"}
        scoring_modalities[modality_id] = enriched

    rubric_payload = {
        "version": "3.0.0",
        "requires_questionnaire_version": "3.0.0",
        "provenance": {
            "author": "Data Contracts Team",
            "tool": "migrate_ids_v1_to_v2.py",
            "edited_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        },
        "changelog": [
            {
                "version": "3.0.0",
                "summary": "Migración de rúbrica a esquema con pesos únicos e imputación NA",
                "reason": "Data contract hardening",
            }
        ],
        "metadata": {
            "default_language": "es",
            "rounding": ROUNDING_RULES,
            "uncertainty": UNCERTAINTY_POLICY,
            "tie_breaker_notes": "Los puntajes exactos en los límites superiores (p. ej. 84.5) se asignan a la banda superior tras redondeo half_up.",
        },
        "scoring_modalities": scoring_modalities,
        "na_rules": {
            "modalities": DEFAULT_MODALITY_NA_RULES,
            "policy_areas": {
                pa_id: {
                    "imputation": ("mean" if pa_id not in {"PA03", "PA08"} else "median"),
                    "scope": "policy_area",
                    "exclude_from_global": pa_id in {"PA03", "PA08"},
                }
                for pa_id in POLICY_AREA_IDS
            },
        },
        "penalties": PENALTY_RULES,
        "aggregation": {
            "dimension_question_weights": dimension_question_weights,
            "policy_area_dimension_weights": policy_area_dimension_weights,
            "cluster_policy_area_weights": cluster_policy_area_weights,
            "macro_cluster_weights": macro_cluster_weights,
        },
        "score_bands": rubric.get("score_bands", {}),
        "rubric_matrix": rubric_matrix,
        "recommendation_rules": RECOMMENDATION_RULES,
        "imbalance": IMBALANCE_POLICY,
        "uncertainty": UNCERTAINTY_POLICY,
        "required_evidence_keys": POLICY_AREA_EVIDENCE_KEYS,
    }

    return rubric_payload

def update_metadata_checksums(questionnaire_path: Path, rubric_path: Path, execution_mapping_path: Path, output_path: Path) -> dict[str, str]:
    questionnaire_payload = load_json(questionnaire_path)
    rubric_payload = load_json(rubric_path)

    def canonical_yaml_hash_from_file(path: Path) -> str:
        raw = path.read_text(encoding="utf-8")
        normalised_lines = [line.rstrip() for line in raw.splitlines()]
        normalised_text = "\n".join(normalised_lines).strip() + "\n"
        return hashlib.sha256(normalised_text.encode("utf-8")).hexdigest()

    checksums = {
        "questionnaire.json": canonical_hash(questionnaire_payload),
        "rubric_scoring.json": canonical_hash(rubric_payload),
        "execution_mapping.yaml": canonical_yaml_hash_from_file(execution_mapping_path),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(checksums, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    return checksums

def main() -> None:
    args = parse_args()

    questionnaire = load_json(args.questionnaire)
    rubric = load_json(args.rubric)

    legacy_modalities = {
        item.get("id"): item.get("scoring_modality", "TYPE_A")
        for item in rubric.get("questions", [])
        if item.get("id")
    }

    legacy_policy_area_labels: dict[str, str] = {}
    for item in rubric.get("questions", []):
        legacy_id = item.get("id")
        if not legacy_id:
            continue
        pa_legacy = legacy_id.split("-")[0]
        if pa_legacy not in legacy_policy_area_labels and item.get("policy_area_name"):
            legacy_policy_area_labels[pa_legacy] = item["policy_area_name"]

    migrated_questionnaire, legacy_to_new_qid, pa_mapping, cluster_by_pa = migrate_questionnaire(
        questionnaire,
        legacy_modalities,
        legacy_policy_area_labels,
    )
    migrated_rubric = migrate_rubric(
        rubric,
        questionnaire,
        migrated_questionnaire,
        legacy_to_new_qid,
        pa_mapping,
        cluster_by_pa,
    )

    output_dir = args.output_dir or args.questionnaire.parent
    questionnaire_target = output_dir / args.questionnaire.name
    rubric_target = output_dir / args.rubric.name

    if args.write:
        dump_json(questionnaire_target, migrated_questionnaire)
        dump_json(rubric_target, migrated_rubric)
        update_metadata_checksums(
            questionnaire_target,
            rubric_target,
            args.execution_mapping,
            ROOT / "config" / "metadata_checksums.json",
        )
    else:
        preview = {
            "questionnaire_sample": migrated_questionnaire["questions"][0],
            "rubric_matrix_sample": migrated_rubric["rubric_matrix"]["PA01"]["DIM01"],
        }
        json.dump(preview, fp=sys.stdout, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()

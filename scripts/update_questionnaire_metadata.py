#!/usr/bin/env python3
"""Utility to update questionnaire metadata with specificity and dependencies."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
# UPDATED: cuestionario_FIXED.json migrated to questionnaire_monolith.json
QUESTIONNAIRE_FILES = [
    ROOT / "data" / "questionnaire_monolith.json",
]

SPECIFICITY_HIGH_KEYWORDS = {
    "cuant",  # cuantificacion, cuantitativo
    "magnitud",
    "brecha",
    "trazabilidad",
    "asignacion",
    "coherencia",
    "proporcional",
    "meta",
    "impacto",
    "resultado",
    "suficiencia",
    "evidencia",
    "ambicion",
    "contradiccion",
    "cobertura",
    "linea_base",
}

SPECIFICITY_MEDIUM_KEYWORDS = {
    "vacio",
    "vacío",
    "limit",
    "sesgo",
    "riesgo",
    "particip",
    "proceso",
    "gobernanza",
    "articulacion",
    "coordinacion",
    "capacidad",
    "enfoque",
    "seguimiento",
    "soporte",
}

SPECIFICITY_LEVELS = ("HIGH", "MEDIUM", "LOW")

SCORING_LEVELS = ["excelente", "bueno", "aceptable", "insuficiente"]

DEFAULT_SCORING = {
    "excelente": {"min_score": 0.85, "criteria": ""},
    "bueno": {"min_score": 0.7, "criteria": ""},
    "aceptable": {"min_score": 0.55, "criteria": ""},
    "insuficiente": {"min_score": 0.0, "criteria": ""},
}

DEPENDENCIAS_MAP = {
    "D3-Q2": {
        "brecha_diagnosticada": "D1-Q2",
        "recursos_asignados": "D1-Q3",
    },
    "D4-Q3": {
        "inversion_total": "D1-Q3",
        "capacidad_mencionada": "D1-Q4",
    },
}

def assign_specificity(group_name: str) -> str:
    name = group_name.lower()
    if any(keyword in name for keyword in SPECIFICITY_HIGH_KEYWORDS):
        return "HIGH"
    if any(keyword in name for keyword in SPECIFICITY_MEDIUM_KEYWORDS):
        return "MEDIUM"
    return "MEDIUM"

def normalize_scoring(scoring: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for level in SCORING_LEVELS:
        entry = scoring.get(level, {})
        entry_dict = dict(entry) if isinstance(entry, dict) else {}
        # Preserve existing values but guarantee required keys
        if "min_score" not in entry_dict:
            entry_dict["min_score"] = DEFAULT_SCORING[level]["min_score"]
        if "criteria" not in entry_dict:
            entry_dict["criteria"] = DEFAULT_SCORING[level]["criteria"]
        normalized[level] = entry_dict
    # Append any additional scoring categories after the normalized block
    for level, entry in scoring.items():
        if level not in normalized:
            normalized[level] = entry
    return normalized

def update_verification_blocks(question: dict[str, Any]) -> bool:
    updated = False
    for key, value in list(question.items()):
        if not key.startswith("verificacion"):
            continue
        if isinstance(value, dict):
            for group_name, group_data in value.items():
                if isinstance(group_data, dict) and "patterns" in group_data:
                    specificity = assign_specificity(group_name)
                    if group_data.get("specificity") != specificity:
                        group_data["specificity"] = specificity
                        updated = True
    return updated

def apply_updates(path: Path) -> bool:
    if not path.exists():
        return False
    changed = False
    data = json.loads(path.read_text(encoding="utf-8"))

    preguntas = data.get("preguntas_base", [])
    if isinstance(preguntas, list):
        for question in preguntas:
            if not isinstance(question, dict):
                continue
            # Update verification specificity
            if update_verification_blocks(question):
                changed = True
            # Normalize scoring structure
            scoring = question.get("scoring")
            if isinstance(scoring, dict):
                normalized = normalize_scoring(scoring)
                if normalized != scoring:
                    question["scoring"] = normalized
                    changed = True
            # Apply dependencies if applicable
            metadata = question.get("metadata", {})
            original_id = metadata.get("original_id") if isinstance(metadata, dict) else None
            if original_id in DEPENDENCIAS_MAP:
                deps = DEPENDENCIAS_MAP[original_id]
                if question.get("dependencias_data") != deps:
                    question["dependencias_data"] = deps
                    changed = True
    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed

def main() -> None:
    any_changed = False
    for file_path in QUESTIONNAIRE_FILES:
        if apply_updates(file_path):
            print(f"Updated {file_path.relative_to(ROOT)}")
            any_changed = True
        else:
            print(f"No changes required for {file_path.relative_to(ROOT)}")
    if not any_changed:
        print("No updates were necessary")

if __name__ == "__main__":
    main()

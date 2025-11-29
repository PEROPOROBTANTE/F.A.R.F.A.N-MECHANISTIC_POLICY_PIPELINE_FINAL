"""Layer Requirements Module.

This module defines the mandatory requirements for each method type (layer).
It is the SINGLE SOURCE OF TRUTH for deciding which layers a method must pass.
"""

from typing import List, Dict, Any
import logging
from .intrinsic_loader import IntrinsicCalibrationLoader

logger = logging.getLogger(__name__)

LAYER_REQUIREMENTS = {
    "ingest": {
        "layers": ["@b", "@chain", "@u", "@m"],
        "count": 4,
        "description": "Data ingestion - simple loading",
        "min_confidence": 0.5
    },
    
    "processor": {
        "layers": ["@b", "@chain", "@u", "@m"],
        "count": 4,
        "description": "Data processing - transformation without decisions",
        "min_confidence": 0.5
    },
    
    "analyzer": {
        "layers": ["@b", "@chain", "@q", "@d", "@p", "@C", "@u", "@m"],
        "count": 8,
        "description": "Complex analysis - ALL context needed",
        "min_confidence": 0.7
    },
    
    "extractor": {
        "layers": ["@b", "@chain", "@u", "@m"],
        "count": 4,
        "description": "Feature extraction - pattern finding",
        "min_confidence": 0.5
    },
    
    "score": {
        "layers": ["@b", "@chain", "@q", "@d", "@p", "@C", "@u", "@m"],
        "count": 8,
        "description": "Scoring methods (non-executor) - ALL context",
        "min_confidence": 0.7
    },
    
    "utility": {
        "layers": ["@b", "@chain", "@m"],
        "count": 3,
        "description": "Helpers - minimal validation",
        "min_confidence": 0.3
    },
    
    "orchestrator": {
        "layers": ["@b", "@chain", "@m"],
        "count": 3,
        "description": "Coordination - minimal validation",
        "min_confidence": 0.5
    },
    
    "core": {
        "layers": ["@b", "@chain", "@q", "@d", "@p", "@C", "@u", "@m"],
        "count": 8,
        "description": "Critical foundation methods - ALL context",
        "min_confidence": 0.8
    }
}

# VALIDATION: Ensure consistency
assert all(
    len(config["layers"]) == config["count"] 
    for config in LAYER_REQUIREMENTS.values()
), "Layer count mismatch in LAYER_REQUIREMENTS"


def get_required_layers_for_method(method_id: str) -> List[str]:
    """
    OBLIGATORY: Single function that decides layers for a method.
    
    NON-NEGOTIABLE:
    - SINGLE source of truth
    - NO overrides allowed
    - NO hardcoding elsewhere
    """
    
    # 1. Load intrinsic JSON via Singleton
    loader = IntrinsicCalibrationLoader()
    metadata = loader.get_metadata(method_id)
    
    # 2. If executor -> ALWAYS 8 layers (conservative default for executors)
    # Note: Ideally this should be driven by metadata, but keeping the rule as requested.
    if "executor" in method_id.lower():
         return ["@b", "@chain", "@q", "@d", "@p", "@C", "@u", "@m"]
    
    # 3. Get "layer" from metadata
    if metadata is None:
        logger.warning(f"Method {method_id} not in intrinsic_calibration.json, using conservative ALL layers")
        return ["@b", "@chain", "@q", "@d", "@p", "@C", "@u", "@m"]
    
    method_type = metadata.get("layer")
    
    if method_type is None:
        logger.warning(f"Method {method_id} has no 'layer' field, using conservative ALL layers")
        return ["@b", "@chain", "@q", "@d", "@p", "@C", "@u", "@m"]
    
    # 4. Map to required layers
    if method_type not in LAYER_REQUIREMENTS:
        logger.error(f"Unknown method type '{method_type}' for {method_id}, using conservative ALL layers")
        return ["@b", "@chain", "@q", "@d", "@p", "@C", "@u", "@m"]
    
    required_layers = LAYER_REQUIREMENTS[method_type]["layers"]
    
    logger.debug(f"Method {method_id} (type: {method_type}) requires {len(required_layers)} layers: {required_layers}")
    
    return required_layers
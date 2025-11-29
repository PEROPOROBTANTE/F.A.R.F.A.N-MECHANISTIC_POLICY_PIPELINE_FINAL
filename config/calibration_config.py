"""Global Calibration Configuration.

This module defines system-wide constants and default values for the calibration system.
"""

# Default weights for Choquet Integral aggregation
DEFAULT_AGGREGATION_WEIGHTS = {
    "b": 0.3,      # Base layer (intrinsic quality)
    "chain": 0.2,  # Chain layer (provenance)
    "q": 0.1,      # Question layer (relevance)
    "d": 0.1,      # Dimension layer (alignment)
    "p": 0.1,      # Policy layer (consistency)
    "C": 0.1,      # Congruence layer (cross-check)
    "u": 0.05,     # Unit layer (granularity)
    "m": 0.05      # Meta layer (self-reflection)
}

# Global thresholds
DEFAULT_VALIDATION_THRESHOLD = 0.7
MIN_CONFIDENCE_LEVEL = 0.5

# Layer definitions
LAYER_NAMES = ["@b", "@chain", "@q", "@d", "@p", "@C", "@u", "@m"]

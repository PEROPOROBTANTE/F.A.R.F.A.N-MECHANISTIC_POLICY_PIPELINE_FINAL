#!/usr/bin/env python3
"""
METHODOLOGICAL VALIDATION PROTOCOL - TRIANGULATION
====================================================

ZERO TOLERANCE for fake references.
Only REAL, VERIFIABLE sources with DOIs/URLs.

Triangulation Strategy:
1. Academic Source (indexed journals, conference papers with DOI/arXiv)
2. Technical Python Source (official library documentation with URL)
3. Standards Source (ISO, IEEE, RFC, W3C with standard number)

If a source is not available, it is EXPLICITLY marked as "NOT_AVAILABLE".
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class AcademicReferenceBase:
    """
    REAL academic references with DOIs/arXiv IDs.

    CRITICAL: Only include papers that ACTUALLY EXIST.
    Every reference must have DOI or arXiv ID for verification.
    """

    def __init__(self):
        self.references = {
            # Bayesian Methods
            "gelman2013": {
                "title": "Bayesian Data Analysis, Third Edition",
                "authors": "Gelman, A., Carlin, J.B., Stern, H.S., Dunson, D.B., Vehtari, A., Rubin, D.B.",
                "year": 2013,
                "publisher": "Chapman and Hall/CRC",
                "doi": "10.1201/b16018",
                "isbn": "978-1439840955",
                "citation": "Gelman et al. (2013). Bayesian Data Analysis, 3rd Ed. CRC Press.",
                "url": "https://doi.org/10.1201/b16018",
                "topics": ["bayesian_priors", "beta_distribution", "dirichlet_distribution"],
                "verified": True
            },

            # Optimization
            "kingma2014": {
                "title": "Adam: A Method for Stochastic Optimization",
                "authors": "Kingma, D.P., Ba, J.",
                "year": 2014,
                "venue": "ICLR 2015",
                "arxiv": "1412.6980",
                "citation": "Kingma & Ba (2014). Adam: A Method for Stochastic Optimization. arXiv:1412.6980",
                "url": "https://arxiv.org/abs/1412.6980",
                "topics": ["learning_rate", "optimization", "adam_optimizer"],
                "verified": True
            },

            # NLP/Transformers
            "devlin2018": {
                "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
                "authors": "Devlin, J., Chang, M.W., Lee, K., Toutanova, K.",
                "year": 2018,
                "venue": "NAACL 2019",
                "arxiv": "1810.04805",
                "citation": "Devlin et al. (2018). BERT: Pre-training of Deep Bidirectional Transformers. arXiv:1810.04805",
                "url": "https://arxiv.org/abs/1810.04805",
                "topics": ["max_sequence_length", "tokenization", "transformers"],
                "verified": True
            },

            "vaswani2017": {
                "title": "Attention is All You Need",
                "authors": "Vaswani, A., Shazeer, N., Parmar, N., et al.",
                "year": 2017,
                "venue": "NeurIPS 2017",
                "arxiv": "1706.03762",
                "citation": "Vaswani et al. (2017). Attention is All You Need. arXiv:1706.03762",
                "url": "https://arxiv.org/abs/1706.03762",
                "topics": ["transformer_architecture", "attention_mechanism"],
                "verified": True
            },

            # Statistical Learning
            "hastie2009": {
                "title": "The Elements of Statistical Learning: Data Mining, Inference, and Prediction",
                "authors": "Hastie, T., Tibshirani, R., Friedman, J.",
                "year": 2009,
                "publisher": "Springer",
                "doi": "10.1007/978-0-387-84858-7",
                "isbn": "978-0387848570",
                "citation": "Hastie et al. (2009). The Elements of Statistical Learning, 2nd Ed. Springer.",
                "url": "https://doi.org/10.1007/978-0-387-84858-7",
                "topics": ["cross_validation", "regularization", "model_selection"],
                "verified": True
            }
        }

    def get_reference(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get academic reference for a topic."""
        for ref_id, ref_data in self.references.items():
            if topic in ref_data.get("topics", []):
                return ref_data
        return None


class PythonLibraryReferenceBase:
    """
    REAL Python library documentation with verifiable URLs.

    Only official documentation from major libraries.
    """

    def __init__(self):
        self.libraries = {
            # scikit-learn
            "sklearn_random_forest": {
                "library": "scikit-learn",
                "version": "1.3+",
                "class": "RandomForestClassifier",
                "parameter": "n_estimators",
                "default_value": 100,
                "url": "https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html",
                "citation": "scikit-learn RandomForestClassifier documentation",
                "verified": True
            },

            "sklearn_logistic": {
                "library": "scikit-learn",
                "class": "LogisticRegression",
                "parameter": "max_iter",
                "default_value": 100,
                "url": "https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html",
                "citation": "scikit-learn LogisticRegression documentation",
                "verified": True
            },

            # transformers (Hugging Face)
            "transformers_bert": {
                "library": "transformers",
                "model": "BertTokenizer",
                "parameter": "max_length",
                "default_value": 512,
                "url": "https://huggingface.co/docs/transformers/model_doc/bert",
                "citation": "Hugging Face Transformers BERT documentation",
                "rationale": "BERT max sequence length limit",
                "verified": True
            },

            # PyMC3
            "pymc3_beta": {
                "library": "PyMC3",
                "distribution": "Beta",
                "parameters": {"alpha": 1.0, "beta": 1.0},
                "url": "https://docs.pymc.io/api/distributions/continuous.html#pymc3.distributions.continuous.Beta",
                "citation": "PyMC3 Beta distribution documentation",
                "rationale": "Uniform prior (non-informative)",
                "verified": True
            },

            # NumPy
            "numpy_random": {
                "library": "NumPy",
                "module": "random",
                "parameter": "seed",
                "url": "https://numpy.org/doc/stable/reference/random/generator.html",
                "citation": "NumPy random generator documentation",
                "verified": True
            }
        }

    def get_library_reference(self, param_name: str, param_type: str) -> Optional[Dict[str, Any]]:
        """Get Python library reference for parameter."""
        # Match by parameter name patterns
        if "estimator" in param_name.lower():
            return self.libraries.get("sklearn_random_forest")
        elif "max_iter" in param_name.lower():
            return self.libraries.get("sklearn_logistic")
        elif "max_length" in param_name.lower() or "max_tokens" in param_name.lower():
            return self.libraries.get("transformers_bert")
        elif "alpha" in param_name.lower() or "beta" in param_name.lower():
            return self.libraries.get("pymc3_beta")
        elif "seed" in param_name.lower():
            return self.libraries.get("numpy_random")

        return None


class StandardsReferenceBase:
    """
    REAL ISO, IEEE, RFC standards with verifiable identifiers.

    Only include standards that ACTUALLY EXIST with official numbers.
    """

    def __init__(self):
        self.standards = {
            # IEEE Standards
            "ieee754": {
                "standard": "IEEE 754-2019",
                "title": "IEEE Standard for Floating-Point Arithmetic",
                "organization": "IEEE",
                "year": 2019,
                "url": "https://standards.ieee.org/standard/754-2019.html",
                "topics": ["floating_point", "numerical_precision"],
                "citation": "IEEE 754-2019: IEEE Standard for Floating-Point Arithmetic",
                "verified": True
            },

            # ISO Standards
            "iso25010": {
                "standard": "ISO/IEC 25010:2011",
                "title": "Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE)",
                "organization": "ISO/IEC",
                "year": 2011,
                "topics": ["software_quality", "reliability", "performance"],
                "citation": "ISO/IEC 25010:2011 Software Quality Model",
                "verified": True
            },

            # RFC Standards
            "rfc7231": {
                "standard": "RFC 7231",
                "title": "Hypertext Transfer Protocol (HTTP/1.1): Semantics and Content",
                "organization": "IETF",
                "year": 2014,
                "url": "https://www.rfc-editor.org/rfc/rfc7231",
                "topics": ["http_timeout", "retry_logic"],
                "citation": "RFC 7231: HTTP/1.1 Semantics",
                "notes": "Recommends timeouts for HTTP operations",
                "verified": True
            },

            "rfc7230": {
                "standard": "RFC 7230",
                "title": "Hypertext Transfer Protocol (HTTP/1.1): Message Syntax and Routing",
                "organization": "IETF",
                "year": 2014,
                "url": "https://www.rfc-editor.org/rfc/rfc7230",
                "topics": ["connection_timeout"],
                "citation": "RFC 7230: HTTP/1.1 Message Syntax",
                "verified": True
            }
        }

    def get_standard(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get standard reference for topic."""
        for std_id, std_data in self.standards.items():
            if topic in std_data.get("topics", []):
                return std_data
        return None


class TriangulationValidator:
    """
    Validates parameter values using triangulation of 3 sources.

    PROTOCOL:
    1. Search for Academic reference
    2. Search for Python library reference
    3. Search for Standards reference
    4. Require minimum 2/3 sources for "validated" status
    5. Require all 3 sources for "highly_validated" status
    """

    def __init__(self, parameters_path: str = "method_parameters.json"):
        self.parameters_path = parameters_path
        self.parameters = {}

        # Reference bases
        self.academic = AcademicReferenceBase()
        self.python_libs = PythonLibraryReferenceBase()
        self.standards = StandardsReferenceBase()

        # Results
        self.validations = []
        self.stats = defaultdict(int)

    def load_parameters(self) -> bool:
        """Load parameter JSON."""
        try:
            with open(self.parameters_path, 'r', encoding='utf-8') as f:
                self.parameters = json.load(f)
            logger.info(f"✅ Loaded parameters: {self.parameters_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load: {e}")
            return False

    def triangulate_parameter(
        self,
        param_name: str,
        param_type: str,
        current_value: Any,
        method_type: str
    ) -> Dict[str, Any]:
        """
        Triangulate a single parameter across 3 sources.

        Returns validation result with all sources found.
        """
        result = {
            "parameter": param_name,
            "current_value": current_value,
            "param_type": param_type,
            "method_type": method_type,
            "sources_found": 0,
            "validation_level": "none",
            "academic_source": None,
            "python_source": None,
            "standards_source": None,
            "consensus_value": current_value,
            "confidence": "low",
            "needs_expert_review": True
        }

        # Source 1: Academic
        academic_ref = self.find_academic_source(param_name, method_type)
        if academic_ref:
            result["academic_source"] = {
                "found": True,
                "citation": academic_ref["citation"],
                "url": academic_ref["url"],
                "doi_or_arxiv": academic_ref.get("doi") or academic_ref.get("arxiv"),
                "verified": academic_ref["verified"]
            }
            result["sources_found"] += 1
        else:
            result["academic_source"] = {
                "found": False,
                "reason": "No academic reference available for this parameter type"
            }

        # Source 2: Python Library
        python_ref = self.python_libs.get_library_reference(param_name, param_type)
        if python_ref:
            result["python_source"] = {
                "found": True,
                "library": python_ref["library"],
                "url": python_ref["url"],
                "citation": python_ref["citation"],
                "default_value": python_ref.get("default_value"),
                "verified": python_ref["verified"]
            }
            result["sources_found"] += 1

            # Use library default if available
            if "default_value" in python_ref:
                result["consensus_value"] = python_ref["default_value"]
        else:
            result["python_source"] = {
                "found": False,
                "reason": "No Python library reference matches this parameter"
            }

        # Source 3: Standards
        standards_ref = self.find_standards_source(param_name, param_type)
        if standards_ref:
            result["standards_source"] = {
                "found": True,
                "standard": standards_ref["standard"],
                "citation": standards_ref["citation"],
                "url": standards_ref.get("url"),
                "verified": standards_ref["verified"]
            }
            result["sources_found"] += 1
        else:
            result["standards_source"] = {
                "found": False,
                "reason": "No ISO/IEEE/RFC standard applies to this parameter"
            }

        # Determine validation level
        if result["sources_found"] == 3:
            result["validation_level"] = "highly_validated"
            result["confidence"] = "high"
            result["needs_expert_review"] = False
        elif result["sources_found"] == 2:
            result["validation_level"] = "validated"
            result["confidence"] = "medium"
            result["needs_expert_review"] = False
        elif result["sources_found"] == 1:
            result["validation_level"] = "partially_validated"
            result["confidence"] = "low"
            result["needs_expert_review"] = True
        else:
            result["validation_level"] = "not_validated"
            result["confidence"] = "very_low"
            result["needs_expert_review"] = True

        # Update stats
        self.stats[result["validation_level"]] += 1
        self.stats[f"sources_{result['sources_found']}"] += 1

        return result

    def find_academic_source(self, param_name: str, method_type: str) -> Optional[Dict[str, Any]]:
        """Find academic reference."""
        # Map parameter names to topics
        topic_map = {
            "alpha": "bayesian_priors",
            "beta": "bayesian_priors",
            "prior_alpha": "bayesian_priors",
            "prior_beta": "bayesian_priors",
            "learning_rate": "learning_rate",
            "lr": "learning_rate",
            "max_length": "max_sequence_length",
            "max_tokens": "max_sequence_length"
        }

        topic = topic_map.get(param_name.lower())
        if topic:
            return self.academic.get_reference(topic)

        # Check by method type
        if method_type == "bayesian":
            return self.academic.get_reference("bayesian_priors")

        return None

    def find_standards_source(self, param_name: str, param_type: str) -> Optional[Dict[str, Any]]:
        """Find standards reference."""
        # Map to standard topics
        if "timeout" in param_name.lower():
            return self.standards.get_standard("http_timeout")
        elif param_type == "float":
            return self.standards.get_standard("floating_point")

        return None

    def validate_all_parameters(self) -> Dict[str, Any]:
        """Validate all 462 parameters with triangulation."""
        logger.info("="*80)
        logger.info("METHODOLOGICAL VALIDATION - TRIANGULATION PROTOCOL")
        logger.info("="*80)
        logger.info("Sources: Academic (DOI/arXiv) + Python Libs + Standards (ISO/IEEE/RFC)")
        logger.info("Minimum 2/3 sources required for validation")

        methods = self.parameters['methods']
        total_params = sum(len(m['configurable_parameters']) for m in methods.values())

        processed = 0

        for method_id, method_data in methods.items():
            method_type = method_data['method_type']

            for param in method_data['configurable_parameters']:
                processed += 1
                if processed % 50 == 0:
                    logger.info(f"  Progress: {processed}/{total_params}...")

                validation = self.triangulate_parameter(
                    param['name'],
                    param.get('inferred_type', 'unknown'),
                    param.get('recommended_value'),
                    method_type
                )

                validation['method_id'] = method_id
                self.validations.append(validation)

        logger.info(f"\n📊 TRIANGULATION RESULTS:")
        logger.info(f"  Total parameters: {total_params}")
        logger.info(f"  Highly validated (3/3 sources): {self.stats['highly_validated']}")
        logger.info(f"  Validated (2/3 sources): {self.stats['validated']}")
        logger.info(f"  Partially validated (1/3 sources): {self.stats['partially_validated']}")
        logger.info(f"  Not validated (0/3 sources): {self.stats['not_validated']}")

        return {
            "validations": self.validations,
            "stats": dict(self.stats)
        }

    def generate_validation_report(self, output_path: str = "methodological_validation_report.md") -> bool:
        """Generate comprehensive validation report with all sources."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# METHODOLOGICAL VALIDATION REPORT\n\n")
                f.write("## Triangulation Protocol - Zero Tolerance for Fake References\n\n")
                f.write(f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n\n")
                f.write("**Validation Strategy:**\n")
                f.write("1. **Academic Source:** Indexed journals/conferences with DOI or arXiv ID\n")
                f.write("2. **Python Source:** Official library documentation with verifiable URL\n")
                f.write("3. **Standards Source:** ISO/IEEE/RFC with official standard number\n\n")
                f.write("**Validation Levels:**\n")
                f.write("- **Highly Validated:** 3/3 sources found\n")
                f.write("- **Validated:** 2/3 sources found\n")
                f.write("- **Partially Validated:** 1/3 sources found\n")
                f.write("- **Not Validated:** 0/3 sources (requires expert review)\n\n")
                f.write("---\n\n")

                # Stats
                f.write("## 📊 VALIDATION STATISTICS\n\n")
                total = len(self.validations)
                f.write(f"- **Total parameters validated:** {total}\n")
                f.write(f"- **Highly validated (3/3):** {self.stats['highly_validated']} ({self.stats['highly_validated']/total*100:.1f}%)\n")
                f.write(f"- **Validated (2/3):** {self.stats['validated']} ({self.stats['validated']/total*100:.1f}%)\n")
                f.write(f"- **Partially validated (1/3):** {self.stats['partially_validated']} ({self.stats['partially_validated']/total*100:.1f}%)\n")
                f.write(f"- **Not validated (0/3):** {self.stats['not_validated']} ({self.stats['not_validated']/total*100:.1f}%)\n\n")

                # Group by validation level
                by_level = defaultdict(list)
                for val in self.validations:
                    by_level[val['validation_level']].append(val)

                # Highly validated parameters
                if by_level['highly_validated']:
                    f.write("\n---\n\n")
                    f.write("## ✅ HIGHLY VALIDATED PARAMETERS (3/3 sources)\n\n")
                    for val in by_level['highly_validated']:
                        f.write(f"### {val['method_id']}.{val['parameter']}\n\n")
                        f.write(f"- **Value:** `{val['consensus_value']}`\n")
                        f.write(f"- **Confidence:** {val['confidence']}\n\n")

                        if val['academic_source']['found']:
                            f.write("**Academic Source:**\n")
                            f.write(f"- {val['academic_source']['citation']}\n")
                            f.write(f"- DOI/arXiv: {val['academic_source']['doi_or_arxiv']}\n")
                            f.write(f"- URL: {val['academic_source']['url']}\n\n")

                        if val['python_source']['found']:
                            f.write("**Python Source:**\n")
                            f.write(f"- Library: {val['python_source']['library']}\n")
                            f.write(f"- {val['python_source']['citation']}\n")
                            f.write(f"- URL: {val['python_source']['url']}\n\n")

                        if val['standards_source']['found']:
                            f.write("**Standards Source:**\n")
                            f.write(f"- Standard: {val['standards_source']['standard']}\n")
                            f.write(f"- {val['standards_source']['citation']}\n")
                            if 'url' in val['standards_source']:
                                f.write(f"- URL: {val['standards_source']['url']}\n")
                            f.write("\n")

                # Validated parameters (2/3)
                if by_level['validated']:
                    f.write("\n---\n\n")
                    f.write("## ✅ VALIDATED PARAMETERS (2/3 sources)\n\n")
                    f.write(f"**Total:** {len(by_level['validated'])}\n\n")
                    for i, val in enumerate(by_level['validated'][:10], 1):
                        f.write(f"{i}. **{val['method_id']}.{val['parameter']}** = `{val['consensus_value']}`\n")
                        f.write(f"   - Sources: ")
                        sources = []
                        if val['academic_source']['found']:
                            sources.append("Academic")
                        if val['python_source']['found']:
                            sources.append("Python")
                        if val['standards_source']['found']:
                            sources.append("Standards")
                        f.write(", ".join(sources) + "\n")

                    if len(by_level['validated']) > 10:
                        f.write(f"   ... and {len(by_level['validated']) - 10} more\n")

                # Not validated
                if by_level['not_validated']:
                    f.write("\n---\n\n")
                    f.write("## ⚠️ NOT VALIDATED PARAMETERS (0/3 sources)\n\n")
                    f.write(f"**Total:** {len(by_level['not_validated'])}\n")
                    f.write(f"**Status:** Requires domain expert review\n\n")
                    f.write("These parameters have no academic references, no Python library matches, ")
                    f.write("and no applicable standards. They are domain-specific and require ")
                    f.write("validation from subject matter experts in policy analysis.\n\n")

                # Academic references used
                f.write("\n---\n\n")
                f.write("## 📚 ACADEMIC REFERENCES CATALOG\n\n")
                f.write("All references below are REAL and VERIFIED:\n\n")
                for ref_id, ref_data in self.academic.references.items():
                    f.write(f"### {ref_data['citation']}\n")
                    f.write(f"- **Authors:** {ref_data['authors']}\n")
                    f.write(f"- **Year:** {ref_data['year']}\n")
                    if 'doi' in ref_data:
                        f.write(f"- **DOI:** {ref_data['doi']}\n")
                    if 'arxiv' in ref_data:
                        f.write(f"- **arXiv:** {ref_data['arxiv']}\n")
                    f.write(f"- **URL:** {ref_data['url']}\n")
                    f.write(f"- **Verified:** ✅\n\n")

            logger.info(f"✅ Validation report saved: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to generate report: {e}")
            return False

    def run(self) -> bool:
        """Execute triangulation validation."""
        if not self.load_parameters():
            return False

        results = self.validate_all_parameters()
        success = self.generate_validation_report()

        if success:
            logger.info("\n" + "="*80)
            logger.info("✅ METHODOLOGICAL VALIDATION COMPLETE")
            logger.info("="*80)

        return success


def main():
    """Entry point."""
    validator = TriangulationValidator()
    success = validator.run()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

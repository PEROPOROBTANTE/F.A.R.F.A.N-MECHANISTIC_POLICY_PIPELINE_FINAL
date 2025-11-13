# Prospective Defect Audit

## Ranked Findings
1. orchestrator.py:600 → Alias-mismatched orchestrator kwargs → MethodExecutor forwards a static `text/sentences/tables` bundle into every catalog method, but processors like `IndustrialPolicyProcessor.process(raw_text: str)` and `BayesianEvidenceScorer.compute_evidence_score(matches: List[str], total_corpus_size: int, ...)` expect different keyword signatures. This throws `TypeError` as soon as orchestrator wiring executes, blocking the policy pipeline. → producer signature: `MethodExecutor.execute(..., **kwargs)` → consumer expectation: e.g. `IndustrialPolicyProcessor.process(self, raw_text: str)` / `PolicyTextProcessor.segment_into_sentences(self, text: str)` →
```python
results['PP_process'] = executor.execute(
    'IndustrialPolicyProcessor',
    'process',
    text=doc.raw_text,
    sentences=doc.sentences,
    tables=doc.tables,
)
``` →
```diff
@@
-            method = getattr(instance, method_name)
-            return method(**kwargs)
+            method = getattr(instance, method_name)
+            sig = inspect.signature(method)
+            normalized = dict(kwargs)
+            alias_map = {
+                "text": ("raw_text", "document_text"),
+                "raw_text": ("text", "document_text"),
+            }
+            for source, targets in alias_map.items():
+                if source in normalized:
+                    for target in targets:
+                        if target in sig.parameters and target not in normalized:
+                            normalized[target] = normalized[source]
+                            break
+            filtered = {k: v for k, v in normalized.items() if k in sig.parameters}
+            return method(**filtered)
``` → severity: High → confidence: 0.5

2. orchestrator.py:544 → Catalog singletons instantiated without mandatory dependencies → `PolicyTextProcessor` requires a `ProcessorConfig`, `SemanticAnalyzer`/`PerformanceAnalyzer`/`TextMiningEngine` require a `MunicipalOntology`, yet `MethodExecutor` builds them bare. Python raises immediately (`TypeError: __init__() missing 1 required positional argument`). → producer signature: `PolicyTextProcessor.__init__(self, config: ProcessorConfig)` / `SemanticAnalyzer.__init__(self, ontology: MunicipalOntology)` → consumer expectation: orchestrator having usable singletons. →
```python
self.instances = {
    'PolicyTextProcessor': PolicyTextProcessor(),
    'SemanticAnalyzer': SemanticAnalyzer(),
    'PerformanceAnalyzer': PerformanceAnalyzer(),
    'TextMiningEngine': TextMiningEngine(),
}
``` →
```diff
@@
-                'PolicyTextProcessor': PolicyTextProcessor(),
-                'SemanticAnalyzer': SemanticAnalyzer(),
-                'PerformanceAnalyzer': PerformanceAnalyzer(),
-                'TextMiningEngine': TextMiningEngine(),
+                'PolicyTextProcessor': PolicyTextProcessor(ProcessorConfig()),
+                'MunicipalOntology': MunicipalOntology(),
+                'SemanticAnalyzer': SemanticAnalyzer(MunicipalOntology()),
+                'PerformanceAnalyzer': PerformanceAnalyzer(MunicipalOntology()),
+                'TextMiningEngine': TextMiningEngine(MunicipalOntology()),
``` → severity: High → confidence: 0.6

3. aggregation.py:241 → Weighted-average silently truncates mismatched configuration → `zip(scores, weights)` drops trailing scores when the questionnaire provides more weights than scores (or vice versa). Coverage validation only counts scores, so the mismatch becomes an undetected normalization error. → producer signature: `DimensionAggregator.calculate_weighted_average(scores, weights)` → consumer expectation: rubric configs supply exact-length weights →
```python
weighted_sum = sum(s * w for s, w in zip(scores, weights))
``` →
```diff
@@
-        # Calculate weighted sum
-        weighted_sum = sum(s * w for s, w in zip(scores, weights))
+        if len(weights) != len(scores):
+            msg = (
+                f"Weight length mismatch: {len(weights)} weights for {len(scores)} scores"
+            )
+            logger.error(msg)
+            if self.abort_on_insufficient:
+                raise WeightValidationError(msg)
+            return 0.0
+
+        weighted_sum = sum(s * w for s, w in zip(scores, weights))
``` → severity: Medium → confidence: 0.4

4. orchestrator.py:569 → Exception laundering hides catalog breakages → `MethodExecutor.execute` catches every exception and returns `None`, while upper layers treat `None` as valid (e.g., dimension aggregations accept missing evidence). Failures masquerade as successful completion, sabotaging QA telemetry. → producer signature: `MethodExecutor.execute(...): Any` → consumer expectation: raise on contract violations. →
```python
        try:
            instance = self.instances.get(class_name)
            if not instance:
                return None
            method = getattr(instance, method_name)
            return method(**kwargs)
        except Exception as e:
            logger.error(f"Error {class_name}.{method_name}: {e}")
            return None
``` →
```diff
@@
-        except Exception as e:
-            logger.error(f"Error {class_name}.{method_name}: {e}")
-            return None
+        except Exception as e:
+            logger.exception("Catalog invocation failed")
+            raise
``` → severity: Medium → confidence: 0.5

5. aggregation.py:485 → Score normalization assumes 0-3 domain → Dimension normalization hard-clamps at 3.0, yet upstream scoring configs (`ScoringValidator.MODALITY_CONFIGS[TYPE_A].score_range = (0, 4)`) legitimately output 4.0. High-performing Type A scores are squashed, shifting policy rankings. → producer signature: `ScoredMicroQuestion.score` (0–4 for TYPE_A) → consumer expectation: aggregator respects modality ranges. →
```python
normalized = [max(0.0, min(3.0, d.score)) / 3.0 for d in dimension_scores]
``` →
```diff
@@
-        normalized = [max(0.0, min(3.0, d.score)) / 3.0 for d in dimension_scores]
+        normalized = []
+        for d in dimension_scores:
+            max_expected = d.validation_details.get('score_max', 3.0) if d.validation_details else 3.0
+            normalized.append(max(0.0, min(max_expected, d.score)) / max_expected)
``` → severity: Medium → confidence: 0.3

## Top 10 Prospective Risks
1. Alias-mismatched kwargs in MethodExecutor (`text` vs `raw_text`/`matches`) break every processor call.【F:orchestrator.py†L600-L649】【F:policy_processor.py†L657-L706】
2. Missing constructor dependencies for text/semantic analyzers create immediate `TypeError`s.【F:orchestrator.py†L540-L558】【F:Analyzer_one.py†L151-L218】
3. Weighted-average truncation silently accepts questionnaire weight drift.【F:aggregation.py†L216-L249】
4. Exception laundering in MethodExecutor misreports catalog health.【F:orchestrator.py†L569-L579】
5. Dimension normalization clamps to 3.0, conflicting with modality ranges up to 4.0.【F:aggregation.py†L475-L487】【F:scoring/scoring.py†L180-L189】
6. Policy chunker embeddings remain numpy arrays, risking JSON serialization downstream (evidence exports expect lists).【F:embedding_policy.py†L823-L876】
7. Recommendation engine assumes all `score_lt` thresholds exist; missing thresholds trigger `TypeError` during comparison (`None` is not orderable).【F:recommendation_engine.py†L184-L212】
8. Evidence registry caches mutable dicts directly, enabling mutation after hashing and invalidating deduplication.【F:evidence_registry.py†L32-L93】
9. `BayesianEvidenceScorer` entropy weighting expects non-empty numpy arrays; orchestrator currently sends strings, leading to runtime errors once alias bug fixed.【F:policy_processor.py†L399-L418】
10. `SemanticChunker` stores global caches without locks while orchestrator runs tasks concurrently, inviting race conditions.【F:semantic_chunking_policy.py†L132-L210】【F:orchestrator.py†L7380-L7496】

## Call-Graph Excerpt (New Risky Edges)
- `Orchestrator._run_micro_flow → MethodExecutor.execute → IndustrialPolicyProcessor.process(raw_text: str)` (alias mismatch `text=`)
- `Orchestrator._run_micro_flow → MethodExecutor.execute → PolicyTextProcessor.segment_into_sentences(text: str)` (extra kwargs `sentences`/`tables` dropped only after proposed fix)
- `Orchestrator._run_micro_flow → MethodExecutor.execute → BayesianEvidenceScorer.compute_evidence_score(matches: List[str], total_corpus_size: int, ...)` (wrong kwarg types lead to runtime failures)

## Hardening Plan
1. **Registry Harmonization**: extend `MethodExecutor` with signature-aware kwarg normalization (alias map + filtering) and initialize catalog components with validated dependencies before enabling orchestrator concurrency.
2. **Argument Router Deployment**: encode per-method adapters (e.g., dataclasses describing required doc attributes) so orchestrator builds kwarg payloads deterministically rather than spraying `text/sentences/tables` everywhere.
3. **Schema & Scale Enforcement**: enhance aggregation validators to compare score ranges/weight lengths against questionnaire schema, and persist normalized max ranges inside `validation_details` for downstream policies.
4. **Telemetry & Concurrency Guards**: stop exception laundering, surface failures to instrumentation, and guard shared caches (chunkers, embedding caches) with locks to avoid concurrent mutation.
5. **Serialization & Registry QA**: ensure numpy payloads are converted via `.tolist()` before any evidence export, and add regression tests covering rule thresholds (`score_lt` presence) plus recommendation schema evolution.

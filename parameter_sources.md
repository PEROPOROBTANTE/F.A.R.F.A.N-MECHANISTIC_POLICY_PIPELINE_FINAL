# PARAMETER VALUE SOURCES - COMPLETE AUDIT TRAIL

**Generated:** 2025-11-18T17:02:06.740407+00:00

**Purpose:** Document every parameter value determination decision

**Hierarchy Applied:**
1. Formal Specification (papers, standards)
2. Reference Implementation (sklearn, PyMC3, etc.)
3. Empirical Validation (cross-validation)
4. Conservative Default (code default, needs validation)

---

## 📊 SUMMARY STATISTICS

- **Total decisions:** 462
- **KB recommendations:** 4
- **Conservative defaults:** 458
- **Values changed from code:** 4

## 📂 DECISIONS BY SOURCE TYPE

### CONSERVATIVE DEFAULT
**Count:** 461

### REFERENCE IMPLEMENTATION
**Count:** 1


---

## 📋 DETAILED DECISIONS

### 1. src.saaaaaa.audit.audit_system.AuditSystem.add_finding.details

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.audit.audit_system.AuditSystem.add_finding
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 2. src.saaaaaa.audit.audit_system.AuditSystem.generate_audit_report.output_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.audit.audit_system.AuditSystem.generate_audit_report
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 3. src.saaaaaa.config.paths.get_output_path.suffix

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.config.paths.get_output_path
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** ``
- **Current Default:** ``
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 4. src.saaaaaa.compat.safe_imports.ImportErrorDetailed.__init__.hint

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.compat.safe_imports.ImportErrorDetailed.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** ``
- **Current Default:** ``
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 5. src.saaaaaa.compat.safe_imports.ImportErrorDetailed.__init__.install_cmd

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.compat.safe_imports.ImportErrorDetailed.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** ``
- **Current Default:** ``
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 6. src.saaaaaa.compat.safe_imports.try_import.required

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.compat.safe_imports.try_import
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 7. src.saaaaaa.compat.safe_imports.try_import.hint

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.compat.safe_imports.try_import
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** ``
- **Current Default:** ``
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 8. src.saaaaaa.compat.safe_imports.try_import.alt

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.compat.safe_imports.try_import
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 9. src.saaaaaa.compat.safe_imports.lazy_import.hint

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.compat.safe_imports.lazy_import
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** ``
- **Current Default:** ``
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 10. src.saaaaaa.observability.opentelemetry_integration.Span.add_event.attributes

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.observability.opentelemetry_integration.Span.add_event
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 11. src.saaaaaa.observability.opentelemetry_integration.Span.set_status.description

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.observability.opentelemetry_integration.Span.set_status
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 12. src.saaaaaa.observability.opentelemetry_integration.Tracer.__init__.version

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.observability.opentelemetry_integration.Tracer.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `1.0.0`
- **Current Default:** `1.0.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 13. src.saaaaaa.observability.opentelemetry_integration.Tracer.start_span.kind

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.observability.opentelemetry_integration.Tracer.start_span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `SpanKind.INTERNAL`
- **Current Default:** `SpanKind.INTERNAL`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 14. src.saaaaaa.observability.opentelemetry_integration.Tracer.start_span.attributes

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.observability.opentelemetry_integration.Tracer.start_span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 15. src.saaaaaa.observability.opentelemetry_integration.Tracer.start_span.parent_context

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.observability.opentelemetry_integration.Tracer.start_span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 16. src.saaaaaa.observability.opentelemetry_integration.Tracer.start_as_current_span.kind

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.observability.opentelemetry_integration.Tracer.start_as_current_span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `SpanKind.INTERNAL`
- **Current Default:** `SpanKind.INTERNAL`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 17. src.saaaaaa.observability.opentelemetry_integration.Tracer.start_as_current_span.attributes

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.observability.opentelemetry_integration.Tracer.start_as_current_span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 18. src.saaaaaa.observability.opentelemetry_integration.Tracer.get_spans.trace_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.observability.opentelemetry_integration.Tracer.get_spans
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 19. src.saaaaaa.observability.opentelemetry_integration.ExecutorSpanDecorator.__call__.span_name

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.observability.opentelemetry_integration.ExecutorSpanDecorator.__call__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 20. src.saaaaaa.observability.opentelemetry_integration.OpenTelemetryObservability.__init__.service_name

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.observability.opentelemetry_integration.OpenTelemetryObservability.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `farfan-pipeline`
- **Current Default:** `farfan-pipeline`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 21. src.saaaaaa.observability.opentelemetry_integration.OpenTelemetryObservability.__init__.service_version

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.observability.opentelemetry_integration.OpenTelemetryObservability.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `1.0.0`
- **Current Default:** `1.0.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 22. src.saaaaaa.observability.opentelemetry_integration.OpenTelemetryObservability.get_executor_decorator.tracer_name

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.observability.opentelemetry_integration.OpenTelemetryObservability.get_executor_decorator
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `executors`
- **Current Default:** `executors`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 23. src.saaaaaa.observability.opentelemetry_integration.executor_span.span_name

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.observability.opentelemetry_integration.executor_span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 24. src.saaaaaa.api.auth_admin.AdminSession.is_expired.timeout_minutes

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.api.auth_admin.AdminSession.is_expired
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `60`
- **Current Default:** `60`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 25. src.saaaaaa.api.auth_admin.AdminAuthenticator.__init__.session_timeout_minutes

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.api.auth_admin.AdminAuthenticator.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `60`
- **Current Default:** `60`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 26. src.saaaaaa.api.auth_admin.AdminAuthenticator.validate_session.ip_address

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.api.auth_admin.AdminAuthenticator.validate_session
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 27. src.saaaaaa.api.auth_admin.AdminAuthenticator.add_user.role

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.api.auth_admin.AdminAuthenticator.add_user
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `user`
- **Current Default:** `user`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 28. src.saaaaaa.api.signals_service.load_signals_from_monolith.monolith_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.api.signals_service.load_signals_from_monolith
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 29. src.saaaaaa.api.pipeline_connector.PipelineConnector.__init__.workspace_dir

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.api.pipeline_connector.PipelineConnector.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `./workspace`
- **Current Default:** `./workspace`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 30. src.saaaaaa.api.pipeline_connector.PipelineConnector.__init__.output_dir

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.api.pipeline_connector.PipelineConnector.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `./output`
- **Current Default:** `./output`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 31. src.saaaaaa.api.pipeline_connector.PipelineConnector.execute_pipeline.municipality

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.api.pipeline_connector.PipelineConnector.execute_pipeline
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `general`
- **Current Default:** `general`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 32. src.saaaaaa.api.pipeline_connector.PipelineConnector.execute_pipeline.progress_callback

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.api.pipeline_connector.PipelineConnector.execute_pipeline
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 33. src.saaaaaa.api.pipeline_connector.PipelineConnector.execute_pipeline.settings

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.api.pipeline_connector.PipelineConnector.execute_pipeline
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 34. src.saaaaaa.flux.phases.run_normalize.policy_unit_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.flux.phases.run_normalize
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 35. src.saaaaaa.flux.phases.run_normalize.correlation_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.flux.phases.run_normalize
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 36. src.saaaaaa.flux.phases.run_normalize.envelope_metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.flux.phases.run_normalize
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 37. src.saaaaaa.flux.phases.run_aggregate.policy_unit_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.flux.phases.run_aggregate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 38. src.saaaaaa.flux.phases.run_aggregate.correlation_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.flux.phases.run_aggregate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 39. src.saaaaaa.flux.phases.run_aggregate.envelope_metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.flux.phases.run_aggregate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 40. src.saaaaaa.flux.phases.run_score.policy_unit_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.flux.phases.run_score
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 41. src.saaaaaa.flux.phases.run_score.correlation_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.flux.phases.run_score
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 42. src.saaaaaa.flux.phases.run_score.envelope_metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.flux.phases.run_score
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 43. src.saaaaaa.flux.phases.run_report.policy_unit_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.flux.phases.run_report
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 44. src.saaaaaa.flux.phases.run_report.correlation_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.flux.phases.run_report
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 45. src.saaaaaa.flux.phases.run_report.envelope_metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.flux.phases.run_report
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 46. src.saaaaaa.flux.gates.QualityGates.coverage_gate.threshold

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.flux.gates.QualityGates.coverage_gate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `80.0`
- **Current Default:** `80.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 47. src.saaaaaa.processing.embedding_policy.EmbeddingProtocol.encode.batch_size

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.embedding_policy.EmbeddingProtocol.encode
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `32`
- **Current Default:** `32`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 48. src.saaaaaa.processing.embedding_policy.EmbeddingProtocol.encode.normalize

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.embedding_policy.EmbeddingProtocol.encode
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 49. src.saaaaaa.processing.embedding_policy.BayesianNumericalAnalyzer.evaluate_policy_metric.n_posterior_samples

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.embedding_policy.BayesianNumericalAnalyzer.evaluate_policy_metric
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `10000`
- **Current Default:** `10000`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 50. src.saaaaaa.processing.embedding_policy.BayesianNumericalAnalyzer.evaluate_policy_metric.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.embedding_policy.BayesianNumericalAnalyzer.evaluate_policy_metric
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 51. src.saaaaaa.processing.embedding_policy.PolicyCrossEncoderReranker.rerank.top_k

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.embedding_policy.PolicyCrossEncoderReranker.rerank
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `10`
- **Current Default:** `10`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 52. src.saaaaaa.processing.embedding_policy.PolicyCrossEncoderReranker.rerank.min_score

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.embedding_policy.PolicyCrossEncoderReranker.rerank
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.0`
- **Current Default:** `0.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 53. src.saaaaaa.processing.embedding_policy.PolicyAnalysisEmbedder.semantic_search.pdq_filter

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.embedding_policy.PolicyAnalysisEmbedder.semantic_search
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 54. src.saaaaaa.processing.embedding_policy.PolicyAnalysisEmbedder.semantic_search.use_reranking

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.embedding_policy.PolicyAnalysisEmbedder.semantic_search
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 55. src.saaaaaa.processing.embedding_policy.create_policy_embedder.model_tier

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.embedding_policy.create_policy_embedder
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `balanced`
- **Current Default:** `balanced`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 56. src.saaaaaa.processing.embedding_policy.EmbeddingPolicyProducer.semantic_search.pdq_filter

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.embedding_policy.EmbeddingPolicyProducer.semantic_search
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 57. src.saaaaaa.processing.embedding_policy.EmbeddingPolicyProducer.semantic_search.use_reranking

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.embedding_policy.EmbeddingPolicyProducer.semantic_search
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 58. src.saaaaaa.processing.factory.extract_pdf_text_single_page.total_pages

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.factory.extract_pdf_text_single_page
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 59. src.saaaaaa.processing.aggregation.DimensionAggregator.validate_coverage.expected_count

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.aggregation.DimensionAggregator.validate_coverage
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `5`
- **Current Default:** `5`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 60. src.saaaaaa.processing.aggregation.DimensionAggregator.calculate_weighted_average.weights

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.aggregation.DimensionAggregator.calculate_weighted_average
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 61. src.saaaaaa.processing.aggregation.DimensionAggregator.apply_rubric_thresholds.thresholds

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.aggregation.DimensionAggregator.apply_rubric_thresholds
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 62. src.saaaaaa.processing.aggregation.DimensionAggregator.aggregate_dimension.weights

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.aggregation.DimensionAggregator.aggregate_dimension
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 63. src.saaaaaa.processing.aggregation.run_aggregation_pipeline.abort_on_insufficient

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.aggregation.run_aggregation_pipeline
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 64. src.saaaaaa.processing.aggregation.AreaPolicyAggregator.apply_rubric_thresholds.thresholds

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.aggregation.AreaPolicyAggregator.apply_rubric_thresholds
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 65. src.saaaaaa.processing.aggregation.AreaPolicyAggregator.aggregate_area.weights

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.aggregation.AreaPolicyAggregator.aggregate_area
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 66. src.saaaaaa.processing.aggregation.ClusterAggregator.apply_cluster_weights.weights

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.aggregation.ClusterAggregator.apply_cluster_weights
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 67. src.saaaaaa.processing.aggregation.ClusterAggregator.aggregate_cluster.weights

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.aggregation.ClusterAggregator.aggregate_cluster
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 68. src.saaaaaa.processing.aggregation.MacroAggregator.apply_rubric_thresholds.thresholds

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.aggregation.MacroAggregator.apply_rubric_thresholds
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 69. src.saaaaaa.processing.policy_processor.ProcessorConfig.from_legacy.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.policy_processor.ProcessorConfig.from_legacy
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 70. src.saaaaaa.processing.policy_processor.BayesianEvidenceScorer.compute_evidence_score.pattern_specificity

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.policy_processor.BayesianEvidenceScorer.compute_evidence_score
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.8`
- **Current Default:** `0.8`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 71. src.saaaaaa.processing.policy_processor.BayesianEvidenceScorer.compute_evidence_score.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.policy_processor.BayesianEvidenceScorer.compute_evidence_score
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 72. src.saaaaaa.processing.policy_processor.PolicyTextProcessor.segment_into_sentences.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.policy_processor.PolicyTextProcessor.segment_into_sentences
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 73. src.saaaaaa.processing.policy_processor.IndustrialPolicyProcessor.process.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.policy_processor.IndustrialPolicyProcessor.process
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 74. src.saaaaaa.processing.policy_processor.PolicyAnalysisPipeline.analyze_file.output_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.policy_processor.PolicyAnalysisPipeline.analyze_file
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 75. src.saaaaaa.processing.policy_processor.create_policy_processor.preserve_structure

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.policy_processor.create_policy_processor
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 76. src.saaaaaa.processing.policy_processor.create_policy_processor.enable_semantic_tagging

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.policy_processor.create_policy_processor
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 77. src.saaaaaa.processing.policy_processor.create_policy_processor.confidence_threshold

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.policy_processor.create_policy_processor
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.65`
- **Current Default:** `0.65`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 78. src.saaaaaa.processing.policy_processor.create_policy_processor.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.policy_processor.create_policy_processor
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 79. src.saaaaaa.processing.semantic_chunking_policy.SemanticProcessor.chunk_text.preserve_structure

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.semantic_chunking_policy.SemanticProcessor.chunk_text
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 80. src.saaaaaa.processing.semantic_chunking_policy.SemanticChunkingProducer.chunk_document.preserve_structure

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.semantic_chunking_policy.SemanticChunkingProducer.chunk_document
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 81. src.saaaaaa.processing.semantic_chunking_policy.SemanticChunkingProducer.semantic_search.dimension

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.semantic_chunking_policy.SemanticChunkingProducer.semantic_search
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 82. src.saaaaaa.processing.semantic_chunking_policy.SemanticChunkingProducer.semantic_search.top_k

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.semantic_chunking_policy.SemanticChunkingProducer.semantic_search
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `5`
- **Current Default:** `5`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 83. src.saaaaaa.processing.spc_ingestion.__init__.CPPIngestionPipeline.process.document_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.spc_ingestion.__init__.CPPIngestionPipeline.process
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 84. src.saaaaaa.processing.spc_ingestion.__init__.CPPIngestionPipeline.process.title

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.spc_ingestion.__init__.CPPIngestionPipeline.process
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 85. src.saaaaaa.processing.spc_ingestion.__init__.CPPIngestionPipeline.process.max_chunks

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.processing.spc_ingestion.__init__.CPPIngestionPipeline.process
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `50`
- **Current Default:** `50`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 86. src.saaaaaa.utils.seed_factory.SeedFactory.create_deterministic_seed.file_checksums

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.seed_factory.SeedFactory.create_deterministic_seed
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 87. src.saaaaaa.utils.seed_factory.SeedFactory.create_deterministic_seed.context

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.seed_factory.SeedFactory.create_deterministic_seed
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 88. src.saaaaaa.utils.seed_factory.create_deterministic_seed.file_checksums

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.seed_factory.create_deterministic_seed
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 89. src.saaaaaa.utils.seed_factory.create_deterministic_seed.**context_kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.seed_factory.create_deterministic_seed
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 90. src.saaaaaa.utils.adapters.adapt_document_metadata_to_v1.strict

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.adapters.adapt_document_metadata_to_v1
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 91. src.saaaaaa.utils.adapters.handle_renamed_param.removal_version

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.adapters.handle_renamed_param
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `v2.0.0`
- **Current Default:** `v2.0.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 92. src.saaaaaa.utils.adapters.adapt_to_sequence.allow_strings

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.adapters.adapt_to_sequence
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 93. src.saaaaaa.utils.deterministic_execution.DeterministicSeedManager.__init__.base_seed

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.deterministic_execution.DeterministicSeedManager.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `42`
- **Current Default:** `42`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 94. src.saaaaaa.utils.deterministic_execution.DeterministicSeedManager.get_event_id.timestamp_utc

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.deterministic_execution.DeterministicSeedManager.get_event_id
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 95. src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.__init__.base_seed

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `42`
- **Current Default:** `42`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 96. src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.__init__.logger_name

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `deterministic_executor`
- **Current Default:** `deterministic_executor`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 97. src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.__init__.enable_logging

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 98. src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.deterministic.log_inputs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.deterministic
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 99. src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.deterministic.log_outputs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.deterministic
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 100. src.saaaaaa.utils.flow_adapters.wrap_payload.correlation_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.flow_adapters.wrap_payload
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 101. src.saaaaaa.utils.flow_adapters.unwrap_payload.expected_model

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.flow_adapters.unwrap_payload
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 102. src.saaaaaa.utils.contract_io.ContractEnvelope.wrap.correlation_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.contract_io.ContractEnvelope.wrap
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 103. src.saaaaaa.utils.contract_io.ContractEnvelope.wrap.schema_version

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.contract_io.ContractEnvelope.wrap
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `CANONICAL_SCHEMA_VERSION`
- **Current Default:** `CANONICAL_SCHEMA_VERSION`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 104. src.saaaaaa.utils.json_logger.get_json_logger.name

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.json_logger.get_json_logger
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `saaaaaa`
- **Current Default:** `saaaaaa`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 105. src.saaaaaa.utils.determinism_helpers.deterministic.policy_unit_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.determinism_helpers.deterministic
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 106. src.saaaaaa.utils.determinism_helpers.deterministic.correlation_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.determinism_helpers.deterministic
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 107. src.saaaaaa.utils.metadata_loader.MetadataLoader.load_and_validate_metadata.schema_ref

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.metadata_loader.MetadataLoader.load_and_validate_metadata
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 108. src.saaaaaa.utils.metadata_loader.MetadataLoader.load_and_validate_metadata.required_version

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.metadata_loader.MetadataLoader.load_and_validate_metadata
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 109. src.saaaaaa.utils.metadata_loader.MetadataLoader.load_and_validate_metadata.expected_checksum

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.metadata_loader.MetadataLoader.load_and_validate_metadata
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 110. src.saaaaaa.utils.metadata_loader.MetadataLoader.load_and_validate_metadata.checksum_algorithm

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.metadata_loader.MetadataLoader.load_and_validate_metadata
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `sha256`
- **Current Default:** `sha256`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 111. src.saaaaaa.utils.metadata_loader.load_execution_mapping.path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.metadata_loader.load_execution_mapping
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 112. src.saaaaaa.utils.metadata_loader.load_execution_mapping.required_version

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.metadata_loader.load_execution_mapping
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `2.0.0`
- **Current Default:** `2.0.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 113. src.saaaaaa.utils.metadata_loader.load_rubric_scoring.path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.metadata_loader.load_rubric_scoring
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 114. src.saaaaaa.utils.metadata_loader.load_rubric_scoring.required_version

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.metadata_loader.load_rubric_scoring
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `2.0.0`
- **Current Default:** `2.0.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 115. src.saaaaaa.utils.paths.normalize_unicode.form

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.paths.normalize_unicode
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `NFC`
- **Current Default:** `NFC`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 116. src.saaaaaa.utils.paths.validate_write_path.allow_source_tree

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.paths.validate_write_path
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 117. src.saaaaaa.utils.cpp_adapter.adapt_cpp_to_orchestrator.*args

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.cpp_adapter.adapt_cpp_to_orchestrator
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `()`
- **Current Default:** `()`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 118. src.saaaaaa.utils.cpp_adapter.adapt_cpp_to_orchestrator.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.cpp_adapter.adapt_cpp_to_orchestrator
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 119. src.saaaaaa.utils.contract_adapters.adapt_document_metadata_v1_to_v2.file_content

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.contract_adapters.adapt_document_metadata_v1_to_v2
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 120. src.saaaaaa.utils.contract_adapters.adapt_dict_to_processed_text_v2.language

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.contract_adapters.adapt_dict_to_processed_text_v2
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `es`
- **Current Default:** `es`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 121. src.saaaaaa.utils.contract_adapters.adapt_dict_to_processed_text_v2.processing_latency_ms

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.contract_adapters.adapt_dict_to_processed_text_v2
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.0`
- **Current Default:** `0.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 122. src.saaaaaa.utils.contract_adapters.adapt_dict_to_processed_text_v2.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.contract_adapters.adapt_dict_to_processed_text_v2
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 123. src.saaaaaa.utils.contract_adapters.ContractMigrationHelper.wrap_v1_function_with_v2_contracts.adapt_input

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.contract_adapters.ContractMigrationHelper.wrap_v1_function_with_v2_contracts
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 124. src.saaaaaa.utils.contract_adapters.ContractMigrationHelper.wrap_v1_function_with_v2_contracts.adapt_output

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.contract_adapters.ContractMigrationHelper.wrap_v1_function_with_v2_contracts
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 125. src.saaaaaa.utils.evidence_registry.EvidenceRecord.create.timestamp

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.evidence_registry.EvidenceRecord.create
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 126. src.saaaaaa.utils.evidence_registry.EvidenceRegistry.append.metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.evidence_registry.EvidenceRegistry.append
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 127. src.saaaaaa.utils.evidence_registry.EvidenceRegistry.append.monolith_hash

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.evidence_registry.EvidenceRegistry.append
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 128. src.saaaaaa.utils.qmcm_hooks.QMCMRecorder.record_call.execution_status

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.qmcm_hooks.QMCMRecorder.record_call
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `success`
- **Current Default:** `success`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 129. src.saaaaaa.utils.qmcm_hooks.QMCMRecorder.record_call.execution_time_ms

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.qmcm_hooks.QMCMRecorder.record_call
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.0`
- **Current Default:** `0.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 130. src.saaaaaa.utils.qmcm_hooks.QMCMRecorder.record_call.monolith_hash

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.qmcm_hooks.QMCMRecorder.record_call
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 131. src.saaaaaa.utils.qmcm_hooks.qmcm_record.method

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.qmcm_hooks.qmcm_record
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 132. src.saaaaaa.utils.qmcm_hooks.qmcm_record.monolith_hash

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.qmcm_hooks.qmcm_record
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 133. src.saaaaaa.utils.schema_monitor.SchemaDriftDetector.get_alerts.source

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.schema_monitor.SchemaDriftDetector.get_alerts
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 134. src.saaaaaa.utils.schema_monitor.SchemaDriftDetector.get_metrics.source

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.schema_monitor.SchemaDriftDetector.get_metrics
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 135. src.saaaaaa.utils.schema_monitor.PayloadValidator.validate.strict

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.schema_monitor.PayloadValidator.validate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 136. src.saaaaaa.utils.contracts.AnalyzerProtocol.analyze.metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.contracts.AnalyzerProtocol.analyze
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 137. src.saaaaaa.utils.signature_validator.validate_signature.enforce

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.signature_validator.validate_signature
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 138. src.saaaaaa.utils.signature_validator.validate_signature.track

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.signature_validator.validate_signature
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 139. src.saaaaaa.utils.signature_validator.validate_call_signature.*args

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.signature_validator.validate_call_signature
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `()`
- **Current Default:** `()`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 140. src.saaaaaa.utils.signature_validator.validate_call_signature.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.signature_validator.validate_call_signature
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 141. src.saaaaaa.utils.signature_validator.create_adapter.param_mapping

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.signature_validator.create_adapter
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 142. src.saaaaaa.utils.enhanced_contracts.ContractValidationError.__init__.field

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.ContractValidationError.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 143. src.saaaaaa.utils.enhanced_contracts.ContractValidationError.__init__.event_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.ContractValidationError.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 144. src.saaaaaa.utils.enhanced_contracts.DataIntegrityError.__init__.expected

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.DataIntegrityError.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 145. src.saaaaaa.utils.enhanced_contracts.DataIntegrityError.__init__.got

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.DataIntegrityError.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 146. src.saaaaaa.utils.enhanced_contracts.DataIntegrityError.__init__.event_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.DataIntegrityError.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 147. src.saaaaaa.utils.enhanced_contracts.SystemConfigError.__init__.config_key

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.SystemConfigError.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 148. src.saaaaaa.utils.enhanced_contracts.SystemConfigError.__init__.event_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.SystemConfigError.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 149. src.saaaaaa.utils.enhanced_contracts.FlowCompatibilityError.__init__.producer

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.FlowCompatibilityError.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 150. src.saaaaaa.utils.enhanced_contracts.FlowCompatibilityError.__init__.consumer

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.FlowCompatibilityError.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 151. src.saaaaaa.utils.enhanced_contracts.FlowCompatibilityError.__init__.event_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.FlowCompatibilityError.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 152. src.saaaaaa.utils.enhanced_contracts.AnalysisInputV2.create_from_text.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.AnalysisInputV2.create_from_text
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 153. src.saaaaaa.utils.enhanced_contracts.StructuredLogger.log_contract_validation.payload_size_bytes

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.StructuredLogger.log_contract_validation
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0`
- **Current Default:** `0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 154. src.saaaaaa.utils.enhanced_contracts.StructuredLogger.log_contract_validation.content_digest

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.StructuredLogger.log_contract_validation
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 155. src.saaaaaa.utils.enhanced_contracts.StructuredLogger.log_contract_validation.error

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.StructuredLogger.log_contract_validation
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 156. src.saaaaaa.utils.enhanced_contracts.StructuredLogger.log_execution.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.enhanced_contracts.StructuredLogger.log_execution
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 157. src.saaaaaa.utils.method_config_loader.MethodConfigLoader.get_method_parameter.override

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.method_config_loader.MethodConfigLoader.get_method_parameter
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 158. src.saaaaaa.utils.validation.aggregation_models.validate_weights.tolerance

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.validation.aggregation_models.validate_weights
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `1e-06`
- **Current Default:** `1e-06`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 159. src.saaaaaa.utils.validation.aggregation_models.validate_dimension_config.weights

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.validation.aggregation_models.validate_dimension_config
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 160. src.saaaaaa.utils.validation.aggregation_models.validate_dimension_config.expected_question_count

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.validation.aggregation_models.validate_dimension_config
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `5`
- **Current Default:** `5`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 161. src.saaaaaa.utils.validation.schema_validator.MonolithSchemaValidator.validate_monolith.strict

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.validation.schema_validator.MonolithSchemaValidator.validate_monolith
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 162. src.saaaaaa.utils.validation.schema_validator.validate_monolith_schema.schema_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.validation.schema_validator.validate_monolith_schema
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 163. src.saaaaaa.utils.validation.schema_validator.validate_monolith_schema.strict

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.validation.schema_validator.validate_monolith_schema
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 164. src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_contract_mismatch.index

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_contract_mismatch
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 165. src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_contract_mismatch.file

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_contract_mismatch
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 166. src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_contract_mismatch.line

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_contract_mismatch
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 167. src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_contract_mismatch.remediation

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_contract_mismatch
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 168. src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_type_violation.file

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_type_violation
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 169. src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_type_violation.line

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_type_violation
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 170. src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_type_violation.remediation

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_type_violation
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 171. src.saaaaaa.core.dependency_lockdown.DependencyLockdown.check_online_model_access.operation

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.dependency_lockdown.DependencyLockdown.check_online_model_access
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `model download`
- **Current Default:** `model download`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 172. src.saaaaaa.core.dependency_lockdown.DependencyLockdown.check_critical_dependency.phase

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.dependency_lockdown.DependencyLockdown.check_critical_dependency
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 173. src.saaaaaa.core.layer_coexistence.LayerScore.__new__.weight

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.layer_coexistence.LayerScore.__new__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `1.0`
- **Current Default:** `1.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 174. src.saaaaaa.core.layer_coexistence.LayerScore.__new__.metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.layer_coexistence.LayerScore.__new__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 175. src.saaaaaa.core.layer_coexistence.create_fusion_operator.parameters

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.layer_coexistence.create_fusion_operator
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 176. src.saaaaaa.core.ports.FilePort.read_text.encoding

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.ports.FilePort.read_text
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `utf-8`
- **Current Default:** `utf-8`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 177. src.saaaaaa.core.ports.FilePort.write_text.encoding

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.ports.FilePort.write_text
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `utf-8`
- **Current Default:** `utf-8`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 178. src.saaaaaa.core.ports.FilePort.mkdir.parents

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.ports.FilePort.mkdir
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 179. src.saaaaaa.core.ports.FilePort.mkdir.exist_ok

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.ports.FilePort.mkdir
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 180. src.saaaaaa.core.ports.JsonPort.dumps.indent

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.ports.JsonPort.dumps
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 181. src.saaaaaa.core.ports.EnvPort.get.default

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.ports.EnvPort.get
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 182. src.saaaaaa.core.ports.LogPort.debug.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.ports.LogPort.debug
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 183. src.saaaaaa.core.ports.LogPort.info.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.ports.LogPort.info
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 184. src.saaaaaa.core.ports.LogPort.warning.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.ports.LogPort.warning
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 185. src.saaaaaa.core.ports.LogPort.error.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.ports.LogPort.error
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 186. src.saaaaaa.core.ports.PortExecutor.run.overrides

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.ports.PortExecutor.run
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 187. src.saaaaaa.core.wiring.observability.trace_wiring_link.**attributes

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.wiring.observability.trace_wiring_link
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 188. src.saaaaaa.core.wiring.observability.trace_wiring_init.**attributes

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.wiring.observability.trace_wiring_init
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 189. src.saaaaaa.core.wiring.observability.log_wiring_metric.**labels

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.wiring.observability.log_wiring_metric
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 190. src.saaaaaa.core.orchestrator.signals.SignalPack.is_valid.now

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.signals.SignalPack.is_valid
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 191. src.saaaaaa.core.orchestrator.signals.SignalClient.fetch_signal_pack.etag

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.signals.SignalClient.fetch_signal_pack
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 192. src.saaaaaa.core.orchestrator.executors.ExecutionMetrics.record_execution.method_key

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.ExecutionMetrics.record_execution
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 193. src.saaaaaa.core.orchestrator.executors.QuantumState.measure.rng

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.QuantumState.measure
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 194. src.saaaaaa.core.orchestrator.executors.QuantumState.optimize_path.iterations

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.QuantumState.optimize_path
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `3`
- **Current Default:** `3`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 195. src.saaaaaa.core.orchestrator.executors.QuantumState.optimize_path.rng

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.QuantumState.optimize_path
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 196. src.saaaaaa.core.orchestrator.executors.QuantumExecutionOptimizer.select_optimal_path.rng

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.QuantumExecutionOptimizer.select_optimal_path
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 197. src.saaaaaa.core.orchestrator.executors.SpikingNeuron.get_firing_rate.window

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.SpikingNeuron.get_firing_rate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `10`
- **Current Default:** `10`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 198. src.saaaaaa.core.orchestrator.executors.CausalGraph.learn_structure.alpha

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.CausalGraph.learn_structure
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.05`
- **Current Default:** `0.05`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 199. src.saaaaaa.core.orchestrator.executors.MetaLearningStrategy.select_strategy.rng

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.MetaLearningStrategy.select_strategy
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 200. src.saaaaaa.core.orchestrator.executors.PersistentHomology.compute_persistence.max_dimension

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.PersistentHomology.compute_persistence
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `1`
- **Current Default:** `1`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 201. src.saaaaaa.core.orchestrator.executors.CategoryTheoryExecutor.compose.*morphism_names

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.CategoryTheoryExecutor.compose
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `()`
- **Current Default:** `()`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 202. src.saaaaaa.core.orchestrator.executors.ProbabilisticExecutor.define_prior.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.ProbabilisticExecutor.define_prior
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 203. src.saaaaaa.core.orchestrator.executors.ProbabilisticExecutor.sample_prior.rng

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.ProbabilisticExecutor.sample_prior
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 204. src.saaaaaa.core.orchestrator.executors.ProbabilisticExecutor.get_credible_interval.alpha

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.ProbabilisticExecutor.get_credible_interval
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.95`
- **Current Default:** `0.95`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 205. src.saaaaaa.core.orchestrator.executors.AdvancedDataFlowExecutor.execute_with_optimization.policy_unit_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.AdvancedDataFlowExecutor.execute_with_optimization
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 206. src.saaaaaa.core.orchestrator.executors.AdvancedDataFlowExecutor.execute_with_optimization.correlation_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executors.AdvancedDataFlowExecutor.execute_with_optimization
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 207. src.saaaaaa.core.orchestrator.signal_loader.build_signal_pack_from_monolith.monolith

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.signal_loader.build_signal_pack_from_monolith
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 208. src.saaaaaa.core.orchestrator.signal_loader.build_signal_pack_from_monolith.questionnaire

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.signal_loader.build_signal_pack_from_monolith
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 209. src.saaaaaa.core.orchestrator.signal_loader.build_all_signal_packs.monolith

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.signal_loader.build_all_signal_packs
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 210. src.saaaaaa.core.orchestrator.signal_loader.build_all_signal_packs.questionnaire

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.signal_loader.build_all_signal_packs
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 211. src.saaaaaa.core.orchestrator.signal_loader.build_signal_manifests.monolith

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.signal_loader.build_signal_manifests
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 212. src.saaaaaa.core.orchestrator.signal_loader.build_signal_manifests.questionnaire

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.signal_loader.build_signal_manifests
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 213. src.saaaaaa.core.orchestrator.factory.load_questionnaire_monolith.path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.load_questionnaire_monolith
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 214. src.saaaaaa.core.orchestrator.factory.load_catalog.path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.load_catalog
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 215. src.saaaaaa.core.orchestrator.factory.load_method_map.path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.load_method_map
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 216. src.saaaaaa.core.orchestrator.factory.get_canonical_dimensions.questionnaire_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.get_canonical_dimensions
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 217. src.saaaaaa.core.orchestrator.factory.get_canonical_policy_areas.questionnaire_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.get_canonical_policy_areas
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 218. src.saaaaaa.core.orchestrator.factory.load_schema.path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.load_schema
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 219. src.saaaaaa.core.orchestrator.factory.construct_semantic_analyzer_input.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.construct_semantic_analyzer_input
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 220. src.saaaaaa.core.orchestrator.factory.construct_cdaf_input.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.construct_cdaf_input
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 221. src.saaaaaa.core.orchestrator.factory.construct_pdet_input.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.construct_pdet_input
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 222. src.saaaaaa.core.orchestrator.factory.construct_teoria_cambio_input.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.construct_teoria_cambio_input
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 223. src.saaaaaa.core.orchestrator.factory.construct_contradiction_detector_input.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.construct_contradiction_detector_input
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 224. src.saaaaaa.core.orchestrator.factory.construct_embedding_policy_input.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.construct_embedding_policy_input
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 225. src.saaaaaa.core.orchestrator.factory.construct_semantic_chunking_input.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.construct_semantic_chunking_input
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 226. src.saaaaaa.core.orchestrator.factory.construct_policy_processor_input.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.construct_policy_processor_input
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 227. src.saaaaaa.core.orchestrator.factory.CoreModuleFactory.load_catalog.path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.CoreModuleFactory.load_catalog
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 228. src.saaaaaa.core.orchestrator.factory.build_processor.questionnaire_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.build_processor
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 229. src.saaaaaa.core.orchestrator.factory.build_processor.data_dir

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.build_processor
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 230. src.saaaaaa.core.orchestrator.factory.build_processor.factory

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.build_processor
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 231. src.saaaaaa.core.orchestrator.factory.build_processor.enable_signals

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.factory.build_processor
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 232. src.saaaaaa.core.orchestrator.chunk_router.ChunkRouter.should_use_full_graph.class_name

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.chunk_router.ChunkRouter.should_use_full_graph
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** ``
- **Current Default:** ``
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 233. src.saaaaaa.core.orchestrator.contract_loader.LoadResult.add_error.line_number

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.contract_loader.LoadResult.add_error
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 234. src.saaaaaa.core.orchestrator.contract_loader.JSONContractLoader.load_directory.pattern

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.contract_loader.JSONContractLoader.load_directory
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `*.json`
- **Current Default:** `*.json`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 235. src.saaaaaa.core.orchestrator.contract_loader.JSONContractLoader.load_directory.recursive

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.contract_loader.JSONContractLoader.load_directory
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 236. src.saaaaaa.core.orchestrator.contract_loader.JSONContractLoader.load_directory.aggregate_errors

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.contract_loader.JSONContractLoader.load_directory
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 237. src.saaaaaa.core.orchestrator.contract_loader.JSONContractLoader.load_multiple.aggregate_errors

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.contract_loader.JSONContractLoader.load_multiple
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 238. src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.__init__.hmac_secret

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 239. src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_determinism.base_seed

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_determinism
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 240. src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_determinism.policy_unit_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_determinism
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 241. src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_determinism.correlation_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_determinism
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 242. src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_determinism.seeds_by_component

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_determinism
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 243. src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_ingestion.chunk_strategy

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_ingestion
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 244. src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_ingestion.chunk_overlap

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_ingestion
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 245. src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.add_phase.duration_ms

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.add_phase
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 246. src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.add_phase.items_processed

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.add_phase
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 247. src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.add_phase.error

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.add_phase
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 248. src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.add_artifact.size_bytes

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.add_artifact
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 249. src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.build_json.indent

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.build_json
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `2`
- **Current Default:** `2`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 250. src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_env.prefix

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_env
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `EXECUTOR_`
- **Current Default:** `EXECUTOR_`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 251. src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.max_tokens

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 252. src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.temperature

- **Hierarchy Level:** 1
- **Source Type:** reference_implementation
- **Source:** Softmax_Standard
- **Citation:** Standard softmax temperature (no adjustment)
- **Rationale:** Neutral temperature preserves original logits
- **Confidence:** high
- **Recommended Value:** `1.0`
- **Current Default:** `None`
- **Changed:** ✅ YES
- **Needs Validation:** ✅ NO

### 253. src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.timeout_s

- **Hierarchy Level:** 1
- **Source Type:** conservative_default
- **Source:** Conservative_Default
- **Citation:** Standard timeout
- **Rationale:** 30s default for operations
- **Confidence:** medium
- **Recommended Value:** `30.0`
- **Current Default:** `None`
- **Changed:** ✅ YES
- **Needs Validation:** ⚠️ YES

### 254. src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.retry

- **Hierarchy Level:** 1
- **Source Type:** conservative_default
- **Source:** Conservative_Default
- **Citation:** Standard retry count for resilient operations
- **Rationale:** 3 retries balances reliability vs latency
- **Confidence:** medium
- **Recommended Value:** `3`
- **Current Default:** `None`
- **Changed:** ✅ YES
- **Needs Validation:** ⚠️ YES

### 255. src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.policy_area

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 256. src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.regex_pack

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 257. src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.thresholds

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 258. src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.entities_whitelist

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 259. src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.enable_symbolic_sparse

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 260. src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.seed

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 261. src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli.app

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 262. src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.validate_latency_budget.max_latency_s

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.validate_latency_budget
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `120.0`
- **Current Default:** `120.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 263. src.saaaaaa.core.orchestrator.calibration_registry.resolve_calibration_with_context.question_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.calibration_registry.resolve_calibration_with_context
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 264. src.saaaaaa.core.orchestrator.calibration_registry.resolve_calibration_with_context.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.calibration_registry.resolve_calibration_with_context
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 265. src.saaaaaa.core.orchestrator.seed_registry.SeedRegistry.get_manifest_entry.policy_unit_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.seed_registry.SeedRegistry.get_manifest_entry
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 266. src.saaaaaa.core.orchestrator.seed_registry.SeedRegistry.get_manifest_entry.correlation_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.seed_registry.SeedRegistry.get_manifest_entry
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 267. src.saaaaaa.core.orchestrator.bayesian_module_factory.BayesianModuleFactory.__init__.signal_registry

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.bayesian_module_factory.BayesianModuleFactory.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 268. src.saaaaaa.core.orchestrator.bayesian_module_factory.BayesianModuleFactory.__init__.signal_client

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.bayesian_module_factory.BayesianModuleFactory.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 269. src.saaaaaa.core.orchestrator.bayesian_module_factory.BayesianModuleFactory.__init__.enable_signals

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.bayesian_module_factory.BayesianModuleFactory.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 270. src.saaaaaa.core.orchestrator.bayesian_module_factory.BayesianModuleFactory.load_catalog.path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.bayesian_module_factory.BayesianModuleFactory.load_catalog
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 271. src.saaaaaa.core.orchestrator.provider.get_questionnaire_payload.force_reload

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.provider.get_questionnaire_payload
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 272. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.verify_integrity.previous_record

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.verify_integrity
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 273. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create.source_method

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 274. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create.parent_evidence_ids

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 275. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create.question_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 276. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create.document_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 277. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create.execution_time_ms

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.0`
- **Current Default:** `0.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 278. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create.metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 279. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create.previous_hash

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 280. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence.source_method

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 281. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence.parent_evidence_ids

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 282. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence.question_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 283. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence.document_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 284. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence.execution_time_ms

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.0`
- **Current Default:** `0.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 285. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence.metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 286. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.verify_evidence.verify_chain

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.verify_evidence
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 287. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.export_provenance_dag.format

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.export_provenance_dag
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `dict`
- **Current Default:** `dict`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 288. src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.export_provenance_dag.output_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.export_provenance_dag
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 289. src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout.coro

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 290. src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout.*varargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `()`
- **Current Default:** `()`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 291. src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout.handler

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 292. src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout.args

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 293. src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout.timeout_s

- **Hierarchy Level:** 1
- **Source Type:** conservative_default
- **Source:** Conservative_Default
- **Citation:** Standard timeout
- **Rationale:** 30s default for operations
- **Confidence:** medium
- **Recommended Value:** `30.0`
- **Current Default:** `300.0`
- **Changed:** ✅ YES
- **Needs Validation:** ⚠️ YES

### 294. src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 295. src.saaaaaa.core.orchestrator.core.PreprocessedDocument.ensure.document_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.PreprocessedDocument.ensure
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 296. src.saaaaaa.core.orchestrator.core.PreprocessedDocument.ensure.use_spc_ingestion

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.PreprocessedDocument.ensure
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 297. src.saaaaaa.core.orchestrator.core.ResourceLimits.check_memory_exceeded.usage

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.ResourceLimits.check_memory_exceeded
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 298. src.saaaaaa.core.orchestrator.core.ResourceLimits.check_cpu_exceeded.usage

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.ResourceLimits.check_cpu_exceeded
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 299. src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.start.items_total

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.start
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 300. src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.increment.count

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.increment
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `1`
- **Current Default:** `1`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 301. src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.increment.latency

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.increment
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 302. src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.record_warning.**extra

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.record_warning
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 303. src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.record_error.**extra

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.record_error
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 304. src.saaaaaa.core.orchestrator.core.MethodExecutor.execute.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.MethodExecutor.execute
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 305. src.saaaaaa.core.orchestrator.core.Orchestrator.process_development_plan.preprocessed_document

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.Orchestrator.process_development_plan
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 306. src.saaaaaa.core.orchestrator.core.Orchestrator.process_development_plan_async.preprocessed_document

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.Orchestrator.process_development_plan_async
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 307. src.saaaaaa.core.orchestrator.core.Orchestrator.monitor_progress_async.poll_interval

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.Orchestrator.monitor_progress_async
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `2.0`
- **Current Default:** `2.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 308. src.saaaaaa.core.orchestrator.core.describe_pipeline_shape.monolith

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.describe_pipeline_shape
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 309. src.saaaaaa.core.orchestrator.core.describe_pipeline_shape.executor_instances

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.core.describe_pipeline_shape
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 310. src.saaaaaa.core.orchestrator.signal_consumption.generate_signal_manifests.source_file_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.signal_consumption.generate_signal_manifests
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 311. src.saaaaaa.core.orchestrator.calibration_context.resolve_contextual_calibration.context

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.orchestrator.calibration_context.resolve_contextual_calibration
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 312. src.saaaaaa.core.calibration.validators.CalibrationValidator.__init__.config_dir

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.validators.CalibrationValidator.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 313. src.saaaaaa.core.calibration.validators.validate_config_files.config_dir

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.validators.validate_config_files
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 314. src.saaaaaa.core.calibration.engine.CalibrationEngine.__init__.config_dir

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.engine.CalibrationEngine.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 315. src.saaaaaa.core.calibration.engine.CalibrationEngine.__init__.monolith_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.engine.CalibrationEngine.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 316. src.saaaaaa.core.calibration.engine.CalibrationEngine.__init__.catalog_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.engine.CalibrationEngine.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 317. src.saaaaaa.core.calibration.engine.calibrate.config_dir

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.engine.calibrate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 318. src.saaaaaa.core.calibration.engine.calibrate.monolith_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.engine.calibrate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 319. src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__.config

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 320. src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__.intrinsic_calibration_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 321. src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__.compatibility_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 322. src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__.method_registry_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 323. src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__.method_signatures_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 324. src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__.intrinsic_calibration_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 325. src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.calibrate.graph_config

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.calibrate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `default`
- **Current Default:** `default`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 326. src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.calibrate.subgraph_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.calibrate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `default`
- **Current Default:** `default`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 327. src.saaaaaa.core.calibration.choquet_aggregator.ChoquetAggregator.aggregate.metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.choquet_aggregator.ChoquetAggregator.aggregate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 328. src.saaaaaa.core.calibration.compatibility.CompatibilityRegistry.validate_anti_universality.threshold

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.compatibility.CompatibilityRegistry.validate_anti_universality
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.9`
- **Current Default:** `0.9`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 329. src.saaaaaa.core.calibration.intrinsic_loader.IntrinsicScoreLoader.__init__.calibration_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.intrinsic_loader.IntrinsicScoreLoader.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `config/intrinsic_calibration.json`
- **Current Default:** `config/intrinsic_calibration.json`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 330. src.saaaaaa.core.calibration.intrinsic_loader.IntrinsicScoreLoader.get_score.default

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.intrinsic_loader.IntrinsicScoreLoader.get_score
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.5`
- **Current Default:** `0.5`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 331. src.saaaaaa.core.calibration.config.UnitLayerConfig.from_env.prefix

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.config.UnitLayerConfig.from_env
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `UNIT_LAYER_`
- **Current Default:** `UNIT_LAYER_`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 332. src.saaaaaa.core.calibration.congruence_layer.CongruenceLayerEvaluator.evaluate.fusion_rule

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.congruence_layer.CongruenceLayerEvaluator.evaluate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `weighted_average`
- **Current Default:** `weighted_average`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 333. src.saaaaaa.core.calibration.congruence_layer.CongruenceLayerEvaluator.evaluate.provided_inputs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.congruence_layer.CongruenceLayerEvaluator.evaluate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 334. src.saaaaaa.core.calibration.chain_layer.ChainLayerEvaluator.evaluate.upstream_outputs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.chain_layer.ChainLayerEvaluator.evaluate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 335. src.saaaaaa.core.calibration.protocols.LayerEvaluator.evaluate.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.protocols.LayerEvaluator.evaluate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 336. src.saaaaaa.core.calibration.data_structures.CompatibilityMapping.check_anti_universality.threshold

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.data_structures.CompatibilityMapping.check_anti_universality
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.9`
- **Current Default:** `0.9`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 337. src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate.formula_exported

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 338. src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate.full_trace

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 339. src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate.logs_conform

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 340. src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate.signature_valid

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 341. src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate.execution_time_s

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 342. src.saaaaaa.analysis.financiero_viabilidad_tablas.PDETMunicipalPlanAnalyzer.analyze_municipal_plan_sync.output_dir

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.financiero_viabilidad_tablas.PDETMunicipalPlanAnalyzer.analyze_municipal_plan_sync
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 343. src.saaaaaa.analysis.financiero_viabilidad_tablas.PDETMunicipalPlanAnalyzer.analyze_municipal_plan.output_dir

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.financiero_viabilidad_tablas.PDETMunicipalPlanAnalyzer.analyze_municipal_plan
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 344. src.saaaaaa.analysis.financiero_viabilidad_tablas.setup_logging.log_level

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.financiero_viabilidad_tablas.setup_logging
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `INFO`
- **Current Default:** `INFO`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 345. src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.segment_text.method

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.segment_text
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `sentence`
- **Current Default:** `sentence`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 346. src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.load_canonical_question_contracts.questionnaire_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.load_canonical_question_contracts
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `questionnaire.json`
- **Current Default:** `questionnaire.json`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 347. src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.load_canonical_question_contracts.rubric_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.load_canonical_question_contracts
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `rubric_scoring_FIXED.json`
- **Current Default:** `rubric_scoring_FIXED.json`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 348. src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.segment_by_canonical_questionnaire.questionnaire_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.segment_by_canonical_questionnaire
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `questionnaire.json`
- **Current Default:** `questionnaire.json`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 349. src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.segment_by_canonical_questionnaire.rubric_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.segment_by_canonical_questionnaire
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `rubric_scoring_FIXED.json`
- **Current Default:** `rubric_scoring_FIXED.json`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 350. src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.segment_by_canonical_questionnaire.segmentation_method

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.segment_by_canonical_questionnaire
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `paragraph`
- **Current Default:** `paragraph`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 351. src.saaaaaa.analysis.Analyzer_one.BatchProcessor.process_directory.pattern

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.Analyzer_one.BatchProcessor.process_directory
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `*.txt`
- **Current Default:** `*.txt`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 352. src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.add_node.dependencies

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.add_node
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 353. src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.add_node.role

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.add_node
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `variable`
- **Current Default:** `variable`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 354. src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.add_node.metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.add_node
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 355. src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.add_edge.weight

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.add_edge
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `1.0`
- **Current Default:** `1.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 356. src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.export_nodes.validate

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.export_nodes
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 357. src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.export_nodes.schema_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.export_nodes
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 358. src.saaaaaa.analysis.factory.save_json.indent

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.factory.save_json
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `2`
- **Current Default:** `2`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 359. src.saaaaaa.analysis.factory.load_all_calibrations.include_metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.factory.load_all_calibrations
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `True`
- **Current Default:** `True`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 360. src.saaaaaa.analysis.factory.write_csv.headers

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.factory.write_csv
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 361. src.saaaaaa.analysis.macro_prompts.CoverageGapStressor.evaluate.baseline_confidence

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.macro_prompts.CoverageGapStressor.evaluate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `1.0`
- **Current Default:** `1.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 362. src.saaaaaa.analysis.macro_prompts.BayesianPortfolioComposer.compose.reconciliation_penalties

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.macro_prompts.BayesianPortfolioComposer.compose
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 363. src.saaaaaa.analysis.meso_cluster_analysis.compose_cluster_posterior.weighting_trace

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.meso_cluster_analysis.compose_cluster_posterior
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 364. src.saaaaaa.analysis.meso_cluster_analysis.compose_cluster_posterior.reconciliation_penalties

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.meso_cluster_analysis.compose_cluster_posterior
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 365. src.saaaaaa.analysis.bayesian_multilevel_system.BayesianRollUp.aggregate_micro_to_meso.dispersion_penalty

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.bayesian_multilevel_system.BayesianRollUp.aggregate_micro_to_meso
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.0`
- **Current Default:** `0.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 366. src.saaaaaa.analysis.bayesian_multilevel_system.BayesianRollUp.aggregate_micro_to_meso.peer_penalty

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.bayesian_multilevel_system.BayesianRollUp.aggregate_micro_to_meso
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.0`
- **Current Default:** `0.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 367. src.saaaaaa.analysis.bayesian_multilevel_system.BayesianRollUp.aggregate_micro_to_meso.additional_penalties

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.bayesian_multilevel_system.BayesianRollUp.aggregate_micro_to_meso
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 368. src.saaaaaa.analysis.bayesian_multilevel_system.MultiLevelBayesianOrchestrator.run_complete_analysis.peer_contexts

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.bayesian_multilevel_system.MultiLevelBayesianOrchestrator.run_complete_analysis
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 369. src.saaaaaa.analysis.bayesian_multilevel_system.MultiLevelBayesianOrchestrator.run_complete_analysis.total_questions

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.bayesian_multilevel_system.MultiLevelBayesianOrchestrator.run_complete_analysis
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `300`
- **Current Default:** `300`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 370. src.saaaaaa.analysis.derek_beach.ConfigLoader.get.default

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.ConfigLoader.get
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 371. src.saaaaaa.analysis.derek_beach.FinancialAuditor.trace_financial_allocation.graph

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.FinancialAuditor.trace_financial_allocation
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 372. src.saaaaaa.analysis.derek_beach.OperationalizationAuditor.bayesian_counterfactual_audit.historical_data

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.OperationalizationAuditor.bayesian_counterfactual_audit
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 373. src.saaaaaa.analysis.derek_beach.OperationalizationAuditor.bayesian_counterfactual_audit.pdet_alignment

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.OperationalizationAuditor.bayesian_counterfactual_audit
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 374. src.saaaaaa.analysis.derek_beach.AdaptivePriorCalculator.calculate_likelihood_adaptativo.test_type

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.AdaptivePriorCalculator.calculate_likelihood_adaptativo
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `hoop`
- **Current Default:** `hoop`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 375. src.saaaaaa.analysis.derek_beach.AdaptivePriorCalculator.sensitivity_analysis.test_type

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.AdaptivePriorCalculator.sensitivity_analysis
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `hoop`
- **Current Default:** `hoop`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 376. src.saaaaaa.analysis.derek_beach.AdaptivePriorCalculator.sensitivity_analysis.perturbation

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.AdaptivePriorCalculator.sensitivity_analysis
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.1`
- **Current Default:** `0.1`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 377. src.saaaaaa.analysis.derek_beach.AdaptivePriorCalculator.generate_traceability_record.seed

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.AdaptivePriorCalculator.generate_traceability_record
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `42`
- **Current Default:** `42`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 378. src.saaaaaa.analysis.derek_beach.HierarchicalGenerativeModel.infer_mechanism_posterior.n_iter

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.HierarchicalGenerativeModel.infer_mechanism_posterior
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `500`
- **Current Default:** `500`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 379. src.saaaaaa.analysis.derek_beach.HierarchicalGenerativeModel.infer_mechanism_posterior.burn_in

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.HierarchicalGenerativeModel.infer_mechanism_posterior
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `100`
- **Current Default:** `100`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 380. src.saaaaaa.analysis.derek_beach.HierarchicalGenerativeModel.infer_mechanism_posterior.n_chains

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.HierarchicalGenerativeModel.infer_mechanism_posterior
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `2`
- **Current Default:** `2`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 381. src.saaaaaa.analysis.derek_beach.HierarchicalGenerativeModel.verify_conditional_independence.independence_tests

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.HierarchicalGenerativeModel.verify_conditional_independence
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 382. src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.construct_scm.structural_equations

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.construct_scm
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 383. src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.counterfactual_query.evidence

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.counterfactual_query
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 384. src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.aggregate_risk_and_prioritize.feasibility

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.aggregate_risk_and_prioritize
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.8`
- **Current Default:** `0.8`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 385. src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.aggregate_risk_and_prioritize.cost

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.aggregate_risk_and_prioritize
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `1.0`
- **Current Default:** `1.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 386. src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.refutation_and_sanity_checks.confounders

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.refutation_and_sanity_checks
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 387. src.saaaaaa.analysis.derek_beach.DerekBeachProducer.create_hierarchical_model.mechanism_priors

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.DerekBeachProducer.create_hierarchical_model
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 388. src.saaaaaa.analysis.derek_beach.DerekBeachProducer.infer_mechanism_posterior.n_iter

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.DerekBeachProducer.infer_mechanism_posterior
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `500`
- **Current Default:** `500`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 389. src.saaaaaa.analysis.derek_beach.DerekBeachProducer.infer_mechanism_posterior.burn_in

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.DerekBeachProducer.infer_mechanism_posterior
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `100`
- **Current Default:** `100`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 390. src.saaaaaa.analysis.derek_beach.DerekBeachProducer.infer_mechanism_posterior.n_chains

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.DerekBeachProducer.infer_mechanism_posterior
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `2`
- **Current Default:** `2`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 391. src.saaaaaa.analysis.derek_beach.DerekBeachProducer.verify_conditional_independence.independence_tests

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.DerekBeachProducer.verify_conditional_independence
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 392. src.saaaaaa.analysis.derek_beach.DerekBeachProducer.construct_scm.structural_equations

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.DerekBeachProducer.construct_scm
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 393. src.saaaaaa.analysis.derek_beach.DerekBeachProducer.counterfactual_query.evidence

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.DerekBeachProducer.counterfactual_query
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 394. src.saaaaaa.analysis.derek_beach.DerekBeachProducer.aggregate_risk.feasibility

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.DerekBeachProducer.aggregate_risk
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.8`
- **Current Default:** `0.8`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 395. src.saaaaaa.analysis.derek_beach.DerekBeachProducer.aggregate_risk.cost

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.DerekBeachProducer.aggregate_risk
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `1.0`
- **Current Default:** `1.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 396. src.saaaaaa.analysis.derek_beach.DerekBeachProducer.refutation_checks.confounders

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.derek_beach.DerekBeachProducer.refutation_checks
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 397. src.saaaaaa.analysis.micro_prompts.ProvenanceAuditor.audit.method_contracts

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.micro_prompts.ProvenanceAuditor.audit
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 398. src.saaaaaa.analysis.micro_prompts.create_provenance_auditor.p95_latency

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.micro_prompts.create_provenance_auditor
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 399. src.saaaaaa.analysis.micro_prompts.create_provenance_auditor.contracts

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.micro_prompts.create_provenance_auditor
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 400. src.saaaaaa.analysis.micro_prompts.create_posterior_explainer.anti_miracle_cap

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.micro_prompts.create_posterior_explainer
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.95`
- **Current Default:** `0.95`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 401. src.saaaaaa.analysis.micro_prompts.create_stress_tester.fragility_threshold

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.micro_prompts.create_stress_tester
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.3`
- **Current Default:** `0.3`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 402. src.saaaaaa.analysis.contradiction_deteccion.BayesianConfidenceCalculator.calculate_posterior.domain_weight

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.contradiction_deteccion.BayesianConfidenceCalculator.calculate_posterior
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `1.0`
- **Current Default:** `1.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 403. src.saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector.detect.plan_name

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector.detect
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `PDM`
- **Current Default:** `PDM`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 404. src.saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector.detect.dimension

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector.detect
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `PolicyDimension.ESTRATEGICO`
- **Current Default:** `PolicyDimension.ESTRATEGICO`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 405. src.saaaaaa.analysis.report_assembly.ReportAssembler.assemble_report.report_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.report_assembly.ReportAssembler.assemble_report
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 406. src.saaaaaa.analysis.report_assembly.ReportAssembler.export_report.format

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.report_assembly.ReportAssembler.export_report
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `json`
- **Current Default:** `json`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 407. src.saaaaaa.analysis.report_assembly.create_report_assembler.evidence_registry

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.report_assembly.create_report_assembler
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 408. src.saaaaaa.analysis.report_assembly.create_report_assembler.qmcm_recorder

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.report_assembly.create_report_assembler
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 409. src.saaaaaa.analysis.report_assembly.create_report_assembler.orchestrator

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.report_assembly.create_report_assembler
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 410. src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.generate_micro_recommendations.context

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.generate_micro_recommendations
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 411. src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.generate_meso_recommendations.context

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.generate_meso_recommendations
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 412. src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.generate_macro_recommendations.context

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.generate_macro_recommendations
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 413. src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.generate_all_recommendations.context

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.generate_all_recommendations
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 414. src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.export_recommendations.format

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.export_recommendations
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `json`
- **Current Default:** `json`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 415. src.saaaaaa.analysis.recommendation_engine.load_recommendation_engine.rules_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.recommendation_engine.load_recommendation_engine
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `config/recommendation_rules_enhanced.json`
- **Current Default:** `config/recommendation_rules_enhanced.json`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 416. src.saaaaaa.analysis.recommendation_engine.load_recommendation_engine.schema_path

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.recommendation_engine.load_recommendation_engine
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `rules/recommendation_rules.schema.json`
- **Current Default:** `rules/recommendation_rules.schema.json`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 417. src.saaaaaa.analysis.scoring.scoring.apply_rounding.mode

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.scoring.scoring.apply_rounding
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `half_up`
- **Current Default:** `half_up`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 418. src.saaaaaa.analysis.scoring.scoring.apply_rounding.precision

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.scoring.scoring.apply_rounding
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `2`
- **Current Default:** `2`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 419. src.saaaaaa.analysis.scoring.scoring.determine_quality_level.thresholds

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.scoring.scoring.determine_quality_level
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 420. src.saaaaaa.analysis.scoring.scoring.apply_scoring.quality_thresholds

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.analysis.scoring.scoring.apply_scoring
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 421. src.saaaaaa.optimization.rl_strategy.BanditArm.ucb_score.c

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.optimization.rl_strategy.BanditArm.ucb_score
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `2.0`
- **Current Default:** `2.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 422. src.saaaaaa.optimization.rl_strategy.UCB1Algorithm.__init__.c

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.optimization.rl_strategy.UCB1Algorithm.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `2.0`
- **Current Default:** `2.0`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 423. src.saaaaaa.optimization.rl_strategy.EpsilonGreedyAlgorithm.__init__.epsilon

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.optimization.rl_strategy.EpsilonGreedyAlgorithm.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `0.1`
- **Current Default:** `0.1`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 424. src.saaaaaa.optimization.rl_strategy.EpsilonGreedyAlgorithm.__init__.decay

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.optimization.rl_strategy.EpsilonGreedyAlgorithm.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `False`
- **Current Default:** `False`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 425. src.saaaaaa.optimization.rl_strategy.RLStrategyOptimizer.__init__.strategy

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.optimization.rl_strategy.RLStrategyOptimizer.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `OptimizationStrategy.THOMPSON_SAMPLING`
- **Current Default:** `OptimizationStrategy.THOMPSON_SAMPLING`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 426. src.saaaaaa.optimization.rl_strategy.RLStrategyOptimizer.__init__.arms

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.optimization.rl_strategy.RLStrategyOptimizer.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 427. src.saaaaaa.optimization.rl_strategy.RLStrategyOptimizer.__init__.seed

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.optimization.rl_strategy.RLStrategyOptimizer.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `42`
- **Current Default:** `42`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 428. src.saaaaaa.patterns.event_tracking.EventSpan.complete.metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventSpan.complete
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 429. src.saaaaaa.patterns.event_tracking.EventTracker.__init__.name

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `FARFAN Pipeline`
- **Current Default:** `FARFAN Pipeline`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 430. src.saaaaaa.patterns.event_tracking.EventTracker.record_event.level

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.record_event
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `EventLevel.INFO`
- **Current Default:** `EventLevel.INFO`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 431. src.saaaaaa.patterns.event_tracking.EventTracker.record_event.metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.record_event
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 432. src.saaaaaa.patterns.event_tracking.EventTracker.record_event.parent_event_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.record_event
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 433. src.saaaaaa.patterns.event_tracking.EventTracker.record_event.tags

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.record_event
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 434. src.saaaaaa.patterns.event_tracking.EventTracker.start_span.category

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.start_span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `EventCategory.PERFORMANCE`
- **Current Default:** `EventCategory.PERFORMANCE`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 435. src.saaaaaa.patterns.event_tracking.EventTracker.start_span.parent_span_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.start_span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 436. src.saaaaaa.patterns.event_tracking.EventTracker.start_span.metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.start_span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 437. src.saaaaaa.patterns.event_tracking.EventTracker.start_span.tags

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.start_span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 438. src.saaaaaa.patterns.event_tracking.EventTracker.complete_span.metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.complete_span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 439. src.saaaaaa.patterns.event_tracking.EventTracker.span.category

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `EventCategory.PERFORMANCE`
- **Current Default:** `EventCategory.PERFORMANCE`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 440. src.saaaaaa.patterns.event_tracking.EventTracker.span.parent_span_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 441. src.saaaaaa.patterns.event_tracking.EventTracker.span.metadata

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 442. src.saaaaaa.patterns.event_tracking.EventTracker.span.tags

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 443. src.saaaaaa.patterns.event_tracking.EventTracker.filter_events.category

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.filter_events
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 444. src.saaaaaa.patterns.event_tracking.EventTracker.filter_events.level

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.filter_events
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 445. src.saaaaaa.patterns.event_tracking.EventTracker.filter_events.source

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.filter_events
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 446. src.saaaaaa.patterns.event_tracking.EventTracker.filter_events.start_time

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.filter_events
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 447. src.saaaaaa.patterns.event_tracking.EventTracker.filter_events.end_time

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.filter_events
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 448. src.saaaaaa.patterns.event_tracking.EventTracker.filter_events.tags

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.EventTracker.filter_events
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 449. src.saaaaaa.patterns.event_tracking.record_event.*args

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.record_event
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `()`
- **Current Default:** `()`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 450. src.saaaaaa.patterns.event_tracking.record_event.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.record_event
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 451. src.saaaaaa.patterns.event_tracking.span.*args

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `()`
- **Current Default:** `()`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 452. src.saaaaaa.patterns.event_tracking.span.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.event_tracking.span
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 453. src.saaaaaa.patterns.saga.SagaStep.execute.*args

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.saga.SagaStep.execute
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `()`
- **Current Default:** `()`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 454. src.saaaaaa.patterns.saga.SagaStep.execute.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.saga.SagaStep.execute
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 455. src.saaaaaa.patterns.saga.SagaStep.compensate.*args

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.saga.SagaStep.compensate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `()`
- **Current Default:** `()`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 456. src.saaaaaa.patterns.saga.SagaStep.compensate.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.saga.SagaStep.compensate
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 457. src.saaaaaa.patterns.saga.SagaOrchestrator.__init__.saga_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.saga.SagaOrchestrator.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 458. src.saaaaaa.patterns.saga.SagaOrchestrator.__init__.name

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.saga.SagaOrchestrator.__init__
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `Unnamed Saga`
- **Current Default:** `Unnamed Saga`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 459. src.saaaaaa.patterns.saga.SagaOrchestrator.add_step.step_id

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.saga.SagaOrchestrator.add_step
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 460. src.saaaaaa.patterns.saga.SagaOrchestrator.execute.*args

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.saga.SagaOrchestrator.execute
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `()`
- **Current Default:** `()`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 461. src.saaaaaa.patterns.saga.SagaOrchestrator.execute.**kwargs

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.saga.SagaOrchestrator.execute
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `{}`
- **Current Default:** `{}`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation

### 462. src.saaaaaa.patterns.saga.compensate_file_write.original_content

- **Hierarchy Level:** 4
- **Source Type:** conservative_default
- **Source:** code_default
- **Citation:** Using current code default from src.saaaaaa.patterns.saga.compensate_file_write
- **Rationale:** No formal spec or reference impl available - using conservative code default
- **Confidence:** low
- **Recommended Value:** `None`
- **Current Default:** `None`
- **Changed:** ❌ NO
- **Needs Validation:** ⚠️ YES
- **⚠️ WARNING:** This parameter requires domain expert validation


---

## ⚠️ PARAMETERS REQUIRING VALIDATION

**Total:** 461

- src.saaaaaa.audit.audit_system.AuditSystem.add_finding.details: `None` (code_default)
- src.saaaaaa.audit.audit_system.AuditSystem.generate_audit_report.output_path: `None` (code_default)
- src.saaaaaa.config.paths.get_output_path.suffix: `` (code_default)
- src.saaaaaa.compat.safe_imports.ImportErrorDetailed.__init__.hint: `` (code_default)
- src.saaaaaa.compat.safe_imports.ImportErrorDetailed.__init__.install_cmd: `` (code_default)
- src.saaaaaa.compat.safe_imports.try_import.required: `False` (code_default)
- src.saaaaaa.compat.safe_imports.try_import.hint: `` (code_default)
- src.saaaaaa.compat.safe_imports.try_import.alt: `None` (code_default)
- src.saaaaaa.compat.safe_imports.lazy_import.hint: `` (code_default)
- src.saaaaaa.observability.opentelemetry_integration.Span.add_event.attributes: `None` (code_default)
- src.saaaaaa.observability.opentelemetry_integration.Span.set_status.description: `None` (code_default)
- src.saaaaaa.observability.opentelemetry_integration.Tracer.__init__.version: `1.0.0` (code_default)
- src.saaaaaa.observability.opentelemetry_integration.Tracer.start_span.kind: `SpanKind.INTERNAL` (code_default)
- src.saaaaaa.observability.opentelemetry_integration.Tracer.start_span.attributes: `None` (code_default)
- src.saaaaaa.observability.opentelemetry_integration.Tracer.start_span.parent_context: `None` (code_default)
- src.saaaaaa.observability.opentelemetry_integration.Tracer.start_as_current_span.kind: `SpanKind.INTERNAL` (code_default)
- src.saaaaaa.observability.opentelemetry_integration.Tracer.start_as_current_span.attributes: `None` (code_default)
- src.saaaaaa.observability.opentelemetry_integration.Tracer.get_spans.trace_id: `None` (code_default)
- src.saaaaaa.observability.opentelemetry_integration.ExecutorSpanDecorator.__call__.span_name: `None` (code_default)
- src.saaaaaa.observability.opentelemetry_integration.OpenTelemetryObservability.__init__.service_name: `farfan-pipeline` (code_default)
- src.saaaaaa.observability.opentelemetry_integration.OpenTelemetryObservability.__init__.service_version: `1.0.0` (code_default)
- src.saaaaaa.observability.opentelemetry_integration.OpenTelemetryObservability.get_executor_decorator.tracer_name: `executors` (code_default)
- src.saaaaaa.observability.opentelemetry_integration.executor_span.span_name: `None` (code_default)
- src.saaaaaa.api.auth_admin.AdminSession.is_expired.timeout_minutes: `60` (code_default)
- src.saaaaaa.api.auth_admin.AdminAuthenticator.__init__.session_timeout_minutes: `60` (code_default)
- src.saaaaaa.api.auth_admin.AdminAuthenticator.validate_session.ip_address: `None` (code_default)
- src.saaaaaa.api.auth_admin.AdminAuthenticator.add_user.role: `user` (code_default)
- src.saaaaaa.api.signals_service.load_signals_from_monolith.monolith_path: `None` (code_default)
- src.saaaaaa.api.pipeline_connector.PipelineConnector.__init__.workspace_dir: `./workspace` (code_default)
- src.saaaaaa.api.pipeline_connector.PipelineConnector.__init__.output_dir: `./output` (code_default)
- src.saaaaaa.api.pipeline_connector.PipelineConnector.execute_pipeline.municipality: `general` (code_default)
- src.saaaaaa.api.pipeline_connector.PipelineConnector.execute_pipeline.progress_callback: `None` (code_default)
- src.saaaaaa.api.pipeline_connector.PipelineConnector.execute_pipeline.settings: `None` (code_default)
- src.saaaaaa.flux.phases.run_normalize.policy_unit_id: `None` (code_default)
- src.saaaaaa.flux.phases.run_normalize.correlation_id: `None` (code_default)
- src.saaaaaa.flux.phases.run_normalize.envelope_metadata: `None` (code_default)
- src.saaaaaa.flux.phases.run_aggregate.policy_unit_id: `None` (code_default)
- src.saaaaaa.flux.phases.run_aggregate.correlation_id: `None` (code_default)
- src.saaaaaa.flux.phases.run_aggregate.envelope_metadata: `None` (code_default)
- src.saaaaaa.flux.phases.run_score.policy_unit_id: `None` (code_default)
- src.saaaaaa.flux.phases.run_score.correlation_id: `None` (code_default)
- src.saaaaaa.flux.phases.run_score.envelope_metadata: `None` (code_default)
- src.saaaaaa.flux.phases.run_report.policy_unit_id: `None` (code_default)
- src.saaaaaa.flux.phases.run_report.correlation_id: `None` (code_default)
- src.saaaaaa.flux.phases.run_report.envelope_metadata: `None` (code_default)
- src.saaaaaa.flux.gates.QualityGates.coverage_gate.threshold: `80.0` (code_default)
- src.saaaaaa.processing.embedding_policy.EmbeddingProtocol.encode.batch_size: `32` (code_default)
- src.saaaaaa.processing.embedding_policy.EmbeddingProtocol.encode.normalize: `True` (code_default)
- src.saaaaaa.processing.embedding_policy.BayesianNumericalAnalyzer.evaluate_policy_metric.n_posterior_samples: `10000` (code_default)
- src.saaaaaa.processing.embedding_policy.BayesianNumericalAnalyzer.evaluate_policy_metric.**kwargs: `{}` (code_default)
- src.saaaaaa.processing.embedding_policy.PolicyCrossEncoderReranker.rerank.top_k: `10` (code_default)
- src.saaaaaa.processing.embedding_policy.PolicyCrossEncoderReranker.rerank.min_score: `0.0` (code_default)
- src.saaaaaa.processing.embedding_policy.PolicyAnalysisEmbedder.semantic_search.pdq_filter: `None` (code_default)
- src.saaaaaa.processing.embedding_policy.PolicyAnalysisEmbedder.semantic_search.use_reranking: `True` (code_default)
- src.saaaaaa.processing.embedding_policy.create_policy_embedder.model_tier: `balanced` (code_default)
- src.saaaaaa.processing.embedding_policy.EmbeddingPolicyProducer.semantic_search.pdq_filter: `None` (code_default)
- src.saaaaaa.processing.embedding_policy.EmbeddingPolicyProducer.semantic_search.use_reranking: `True` (code_default)
- src.saaaaaa.processing.factory.extract_pdf_text_single_page.total_pages: `None` (code_default)
- src.saaaaaa.processing.aggregation.DimensionAggregator.validate_coverage.expected_count: `5` (code_default)
- src.saaaaaa.processing.aggregation.DimensionAggregator.calculate_weighted_average.weights: `None` (code_default)
- src.saaaaaa.processing.aggregation.DimensionAggregator.apply_rubric_thresholds.thresholds: `None` (code_default)
- src.saaaaaa.processing.aggregation.DimensionAggregator.aggregate_dimension.weights: `None` (code_default)
- src.saaaaaa.processing.aggregation.run_aggregation_pipeline.abort_on_insufficient: `True` (code_default)
- src.saaaaaa.processing.aggregation.AreaPolicyAggregator.apply_rubric_thresholds.thresholds: `None` (code_default)
- src.saaaaaa.processing.aggregation.AreaPolicyAggregator.aggregate_area.weights: `None` (code_default)
- src.saaaaaa.processing.aggregation.ClusterAggregator.apply_cluster_weights.weights: `None` (code_default)
- src.saaaaaa.processing.aggregation.ClusterAggregator.aggregate_cluster.weights: `None` (code_default)
- src.saaaaaa.processing.aggregation.MacroAggregator.apply_rubric_thresholds.thresholds: `None` (code_default)
- src.saaaaaa.processing.policy_processor.ProcessorConfig.from_legacy.**kwargs: `{}` (code_default)
- src.saaaaaa.processing.policy_processor.BayesianEvidenceScorer.compute_evidence_score.pattern_specificity: `0.8` (code_default)
- src.saaaaaa.processing.policy_processor.BayesianEvidenceScorer.compute_evidence_score.**kwargs: `{}` (code_default)
- src.saaaaaa.processing.policy_processor.PolicyTextProcessor.segment_into_sentences.**kwargs: `{}` (code_default)
- src.saaaaaa.processing.policy_processor.IndustrialPolicyProcessor.process.**kwargs: `{}` (code_default)
- src.saaaaaa.processing.policy_processor.PolicyAnalysisPipeline.analyze_file.output_path: `None` (code_default)
- src.saaaaaa.processing.policy_processor.create_policy_processor.preserve_structure: `True` (code_default)
- src.saaaaaa.processing.policy_processor.create_policy_processor.enable_semantic_tagging: `True` (code_default)
- src.saaaaaa.processing.policy_processor.create_policy_processor.confidence_threshold: `0.65` (code_default)
- src.saaaaaa.processing.policy_processor.create_policy_processor.**kwargs: `{}` (code_default)
- src.saaaaaa.processing.semantic_chunking_policy.SemanticProcessor.chunk_text.preserve_structure: `True` (code_default)
- src.saaaaaa.processing.semantic_chunking_policy.SemanticChunkingProducer.chunk_document.preserve_structure: `True` (code_default)
- src.saaaaaa.processing.semantic_chunking_policy.SemanticChunkingProducer.semantic_search.dimension: `None` (code_default)
- src.saaaaaa.processing.semantic_chunking_policy.SemanticChunkingProducer.semantic_search.top_k: `5` (code_default)
- src.saaaaaa.processing.spc_ingestion.__init__.CPPIngestionPipeline.process.document_id: `None` (code_default)
- src.saaaaaa.processing.spc_ingestion.__init__.CPPIngestionPipeline.process.title: `None` (code_default)
- src.saaaaaa.processing.spc_ingestion.__init__.CPPIngestionPipeline.process.max_chunks: `50` (code_default)
- src.saaaaaa.utils.seed_factory.SeedFactory.create_deterministic_seed.file_checksums: `None` (code_default)
- src.saaaaaa.utils.seed_factory.SeedFactory.create_deterministic_seed.context: `None` (code_default)
- src.saaaaaa.utils.seed_factory.create_deterministic_seed.file_checksums: `None` (code_default)
- src.saaaaaa.utils.seed_factory.create_deterministic_seed.**context_kwargs: `{}` (code_default)
- src.saaaaaa.utils.adapters.adapt_document_metadata_to_v1.strict: `False` (code_default)
- src.saaaaaa.utils.adapters.handle_renamed_param.removal_version: `v2.0.0` (code_default)
- src.saaaaaa.utils.adapters.adapt_to_sequence.allow_strings: `False` (code_default)
- src.saaaaaa.utils.deterministic_execution.DeterministicSeedManager.__init__.base_seed: `42` (code_default)
- src.saaaaaa.utils.deterministic_execution.DeterministicSeedManager.get_event_id.timestamp_utc: `None` (code_default)
- src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.__init__.base_seed: `42` (code_default)
- src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.__init__.logger_name: `deterministic_executor` (code_default)
- src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.__init__.enable_logging: `True` (code_default)
- src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.deterministic.log_inputs: `False` (code_default)
- src.saaaaaa.utils.deterministic_execution.DeterministicExecutor.deterministic.log_outputs: `False` (code_default)
- src.saaaaaa.utils.flow_adapters.wrap_payload.correlation_id: `None` (code_default)
- src.saaaaaa.utils.flow_adapters.unwrap_payload.expected_model: `None` (code_default)
- src.saaaaaa.utils.contract_io.ContractEnvelope.wrap.correlation_id: `None` (code_default)
- src.saaaaaa.utils.contract_io.ContractEnvelope.wrap.schema_version: `CANONICAL_SCHEMA_VERSION` (code_default)
- src.saaaaaa.utils.json_logger.get_json_logger.name: `saaaaaa` (code_default)
- src.saaaaaa.utils.determinism_helpers.deterministic.policy_unit_id: `None` (code_default)
- src.saaaaaa.utils.determinism_helpers.deterministic.correlation_id: `None` (code_default)
- src.saaaaaa.utils.metadata_loader.MetadataLoader.load_and_validate_metadata.schema_ref: `None` (code_default)
- src.saaaaaa.utils.metadata_loader.MetadataLoader.load_and_validate_metadata.required_version: `None` (code_default)
- src.saaaaaa.utils.metadata_loader.MetadataLoader.load_and_validate_metadata.expected_checksum: `None` (code_default)
- src.saaaaaa.utils.metadata_loader.MetadataLoader.load_and_validate_metadata.checksum_algorithm: `sha256` (code_default)
- src.saaaaaa.utils.metadata_loader.load_execution_mapping.path: `None` (code_default)
- src.saaaaaa.utils.metadata_loader.load_execution_mapping.required_version: `2.0.0` (code_default)
- src.saaaaaa.utils.metadata_loader.load_rubric_scoring.path: `None` (code_default)
- src.saaaaaa.utils.metadata_loader.load_rubric_scoring.required_version: `2.0.0` (code_default)
- src.saaaaaa.utils.paths.normalize_unicode.form: `NFC` (code_default)
- src.saaaaaa.utils.paths.validate_write_path.allow_source_tree: `False` (code_default)
- src.saaaaaa.utils.cpp_adapter.adapt_cpp_to_orchestrator.*args: `()` (code_default)
- src.saaaaaa.utils.cpp_adapter.adapt_cpp_to_orchestrator.**kwargs: `{}` (code_default)
- src.saaaaaa.utils.contract_adapters.adapt_document_metadata_v1_to_v2.file_content: `None` (code_default)
- src.saaaaaa.utils.contract_adapters.adapt_dict_to_processed_text_v2.language: `es` (code_default)
- src.saaaaaa.utils.contract_adapters.adapt_dict_to_processed_text_v2.processing_latency_ms: `0.0` (code_default)
- src.saaaaaa.utils.contract_adapters.adapt_dict_to_processed_text_v2.**kwargs: `{}` (code_default)
- src.saaaaaa.utils.contract_adapters.ContractMigrationHelper.wrap_v1_function_with_v2_contracts.adapt_input: `True` (code_default)
- src.saaaaaa.utils.contract_adapters.ContractMigrationHelper.wrap_v1_function_with_v2_contracts.adapt_output: `True` (code_default)
- src.saaaaaa.utils.evidence_registry.EvidenceRecord.create.timestamp: `None` (code_default)
- src.saaaaaa.utils.evidence_registry.EvidenceRegistry.append.metadata: `None` (code_default)
- src.saaaaaa.utils.evidence_registry.EvidenceRegistry.append.monolith_hash: `None` (code_default)
- src.saaaaaa.utils.qmcm_hooks.QMCMRecorder.record_call.execution_status: `success` (code_default)
- src.saaaaaa.utils.qmcm_hooks.QMCMRecorder.record_call.execution_time_ms: `0.0` (code_default)
- src.saaaaaa.utils.qmcm_hooks.QMCMRecorder.record_call.monolith_hash: `None` (code_default)
- src.saaaaaa.utils.qmcm_hooks.qmcm_record.method: `None` (code_default)
- src.saaaaaa.utils.qmcm_hooks.qmcm_record.monolith_hash: `None` (code_default)
- src.saaaaaa.utils.schema_monitor.SchemaDriftDetector.get_alerts.source: `None` (code_default)
- src.saaaaaa.utils.schema_monitor.SchemaDriftDetector.get_metrics.source: `None` (code_default)
- src.saaaaaa.utils.schema_monitor.PayloadValidator.validate.strict: `True` (code_default)
- src.saaaaaa.utils.contracts.AnalyzerProtocol.analyze.metadata: `None` (code_default)
- src.saaaaaa.utils.signature_validator.validate_signature.enforce: `True` (code_default)
- src.saaaaaa.utils.signature_validator.validate_signature.track: `True` (code_default)
- src.saaaaaa.utils.signature_validator.validate_call_signature.*args: `()` (code_default)
- src.saaaaaa.utils.signature_validator.validate_call_signature.**kwargs: `{}` (code_default)
- src.saaaaaa.utils.signature_validator.create_adapter.param_mapping: `None` (code_default)
- src.saaaaaa.utils.enhanced_contracts.ContractValidationError.__init__.field: `None` (code_default)
- src.saaaaaa.utils.enhanced_contracts.ContractValidationError.__init__.event_id: `None` (code_default)
- src.saaaaaa.utils.enhanced_contracts.DataIntegrityError.__init__.expected: `None` (code_default)
- src.saaaaaa.utils.enhanced_contracts.DataIntegrityError.__init__.got: `None` (code_default)
- src.saaaaaa.utils.enhanced_contracts.DataIntegrityError.__init__.event_id: `None` (code_default)
- src.saaaaaa.utils.enhanced_contracts.SystemConfigError.__init__.config_key: `None` (code_default)
- src.saaaaaa.utils.enhanced_contracts.SystemConfigError.__init__.event_id: `None` (code_default)
- src.saaaaaa.utils.enhanced_contracts.FlowCompatibilityError.__init__.producer: `None` (code_default)
- src.saaaaaa.utils.enhanced_contracts.FlowCompatibilityError.__init__.consumer: `None` (code_default)
- src.saaaaaa.utils.enhanced_contracts.FlowCompatibilityError.__init__.event_id: `None` (code_default)
- src.saaaaaa.utils.enhanced_contracts.AnalysisInputV2.create_from_text.**kwargs: `{}` (code_default)
- src.saaaaaa.utils.enhanced_contracts.StructuredLogger.log_contract_validation.payload_size_bytes: `0` (code_default)
- src.saaaaaa.utils.enhanced_contracts.StructuredLogger.log_contract_validation.content_digest: `None` (code_default)
- src.saaaaaa.utils.enhanced_contracts.StructuredLogger.log_contract_validation.error: `None` (code_default)
- src.saaaaaa.utils.enhanced_contracts.StructuredLogger.log_execution.**kwargs: `{}` (code_default)
- src.saaaaaa.utils.method_config_loader.MethodConfigLoader.get_method_parameter.override: `None` (code_default)
- src.saaaaaa.utils.validation.aggregation_models.validate_weights.tolerance: `1e-06` (code_default)
- src.saaaaaa.utils.validation.aggregation_models.validate_dimension_config.weights: `None` (code_default)
- src.saaaaaa.utils.validation.aggregation_models.validate_dimension_config.expected_question_count: `5` (code_default)
- src.saaaaaa.utils.validation.schema_validator.MonolithSchemaValidator.validate_monolith.strict: `True` (code_default)
- src.saaaaaa.utils.validation.schema_validator.validate_monolith_schema.schema_path: `None` (code_default)
- src.saaaaaa.utils.validation.schema_validator.validate_monolith_schema.strict: `True` (code_default)
- src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_contract_mismatch.index: `None` (code_default)
- src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_contract_mismatch.file: `None` (code_default)
- src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_contract_mismatch.line: `None` (code_default)
- src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_contract_mismatch.remediation: `None` (code_default)
- src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_type_violation.file: `None` (code_default)
- src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_type_violation.line: `None` (code_default)
- src.saaaaaa.utils.validation.contract_logger.ContractErrorLogger.log_type_violation.remediation: `None` (code_default)
- src.saaaaaa.core.dependency_lockdown.DependencyLockdown.check_online_model_access.operation: `model download` (code_default)
- src.saaaaaa.core.dependency_lockdown.DependencyLockdown.check_critical_dependency.phase: `None` (code_default)
- src.saaaaaa.core.layer_coexistence.LayerScore.__new__.weight: `1.0` (code_default)
- src.saaaaaa.core.layer_coexistence.LayerScore.__new__.metadata: `None` (code_default)
- src.saaaaaa.core.layer_coexistence.create_fusion_operator.parameters: `None` (code_default)
- src.saaaaaa.core.ports.FilePort.read_text.encoding: `utf-8` (code_default)
- src.saaaaaa.core.ports.FilePort.write_text.encoding: `utf-8` (code_default)
- src.saaaaaa.core.ports.FilePort.mkdir.parents: `False` (code_default)
- src.saaaaaa.core.ports.FilePort.mkdir.exist_ok: `False` (code_default)
- src.saaaaaa.core.ports.JsonPort.dumps.indent: `None` (code_default)
- src.saaaaaa.core.ports.EnvPort.get.default: `None` (code_default)
- src.saaaaaa.core.ports.LogPort.debug.**kwargs: `{}` (code_default)
- src.saaaaaa.core.ports.LogPort.info.**kwargs: `{}` (code_default)
- src.saaaaaa.core.ports.LogPort.warning.**kwargs: `{}` (code_default)
- src.saaaaaa.core.ports.LogPort.error.**kwargs: `{}` (code_default)
- src.saaaaaa.core.ports.PortExecutor.run.overrides: `None` (code_default)
- src.saaaaaa.core.wiring.observability.trace_wiring_link.**attributes: `{}` (code_default)
- src.saaaaaa.core.wiring.observability.trace_wiring_init.**attributes: `{}` (code_default)
- src.saaaaaa.core.wiring.observability.log_wiring_metric.**labels: `{}` (code_default)
- src.saaaaaa.core.orchestrator.signals.SignalPack.is_valid.now: `None` (code_default)
- src.saaaaaa.core.orchestrator.signals.SignalClient.fetch_signal_pack.etag: `None` (code_default)
- src.saaaaaa.core.orchestrator.executors.ExecutionMetrics.record_execution.method_key: `None` (code_default)
- src.saaaaaa.core.orchestrator.executors.QuantumState.measure.rng: `None` (code_default)
- src.saaaaaa.core.orchestrator.executors.QuantumState.optimize_path.iterations: `3` (code_default)
- src.saaaaaa.core.orchestrator.executors.QuantumState.optimize_path.rng: `None` (code_default)
- src.saaaaaa.core.orchestrator.executors.QuantumExecutionOptimizer.select_optimal_path.rng: `None` (code_default)
- src.saaaaaa.core.orchestrator.executors.SpikingNeuron.get_firing_rate.window: `10` (code_default)
- src.saaaaaa.core.orchestrator.executors.CausalGraph.learn_structure.alpha: `0.05` (code_default)
- src.saaaaaa.core.orchestrator.executors.MetaLearningStrategy.select_strategy.rng: `None` (code_default)
- src.saaaaaa.core.orchestrator.executors.PersistentHomology.compute_persistence.max_dimension: `1` (code_default)
- src.saaaaaa.core.orchestrator.executors.CategoryTheoryExecutor.compose.*morphism_names: `()` (code_default)
- src.saaaaaa.core.orchestrator.executors.ProbabilisticExecutor.define_prior.**kwargs: `{}` (code_default)
- src.saaaaaa.core.orchestrator.executors.ProbabilisticExecutor.sample_prior.rng: `None` (code_default)
- src.saaaaaa.core.orchestrator.executors.ProbabilisticExecutor.get_credible_interval.alpha: `0.95` (code_default)
- src.saaaaaa.core.orchestrator.executors.AdvancedDataFlowExecutor.execute_with_optimization.policy_unit_id: `None` (code_default)
- src.saaaaaa.core.orchestrator.executors.AdvancedDataFlowExecutor.execute_with_optimization.correlation_id: `None` (code_default)
- src.saaaaaa.core.orchestrator.signal_loader.build_signal_pack_from_monolith.monolith: `None` (code_default)
- src.saaaaaa.core.orchestrator.signal_loader.build_signal_pack_from_monolith.questionnaire: `None` (code_default)
- src.saaaaaa.core.orchestrator.signal_loader.build_all_signal_packs.monolith: `None` (code_default)
- src.saaaaaa.core.orchestrator.signal_loader.build_all_signal_packs.questionnaire: `None` (code_default)
- src.saaaaaa.core.orchestrator.signal_loader.build_signal_manifests.monolith: `None` (code_default)
- src.saaaaaa.core.orchestrator.signal_loader.build_signal_manifests.questionnaire: `None` (code_default)
- src.saaaaaa.core.orchestrator.factory.load_questionnaire_monolith.path: `None` (code_default)
- src.saaaaaa.core.orchestrator.factory.load_catalog.path: `None` (code_default)
- src.saaaaaa.core.orchestrator.factory.load_method_map.path: `None` (code_default)
- src.saaaaaa.core.orchestrator.factory.get_canonical_dimensions.questionnaire_path: `None` (code_default)
- src.saaaaaa.core.orchestrator.factory.get_canonical_policy_areas.questionnaire_path: `None` (code_default)
- src.saaaaaa.core.orchestrator.factory.load_schema.path: `None` (code_default)
- src.saaaaaa.core.orchestrator.factory.construct_semantic_analyzer_input.**kwargs: `{}` (code_default)
- src.saaaaaa.core.orchestrator.factory.construct_cdaf_input.**kwargs: `{}` (code_default)
- src.saaaaaa.core.orchestrator.factory.construct_pdet_input.**kwargs: `{}` (code_default)
- src.saaaaaa.core.orchestrator.factory.construct_teoria_cambio_input.**kwargs: `{}` (code_default)
- src.saaaaaa.core.orchestrator.factory.construct_contradiction_detector_input.**kwargs: `{}` (code_default)
- src.saaaaaa.core.orchestrator.factory.construct_embedding_policy_input.**kwargs: `{}` (code_default)
- src.saaaaaa.core.orchestrator.factory.construct_semantic_chunking_input.**kwargs: `{}` (code_default)
- src.saaaaaa.core.orchestrator.factory.construct_policy_processor_input.**kwargs: `{}` (code_default)
- src.saaaaaa.core.orchestrator.factory.CoreModuleFactory.load_catalog.path: `None` (code_default)
- src.saaaaaa.core.orchestrator.factory.build_processor.questionnaire_path: `None` (code_default)
- src.saaaaaa.core.orchestrator.factory.build_processor.data_dir: `None` (code_default)
- src.saaaaaa.core.orchestrator.factory.build_processor.factory: `None` (code_default)
- src.saaaaaa.core.orchestrator.factory.build_processor.enable_signals: `True` (code_default)
- src.saaaaaa.core.orchestrator.chunk_router.ChunkRouter.should_use_full_graph.class_name: `` (code_default)
- src.saaaaaa.core.orchestrator.contract_loader.LoadResult.add_error.line_number: `None` (code_default)
- src.saaaaaa.core.orchestrator.contract_loader.JSONContractLoader.load_directory.pattern: `*.json` (code_default)
- src.saaaaaa.core.orchestrator.contract_loader.JSONContractLoader.load_directory.recursive: `False` (code_default)
- src.saaaaaa.core.orchestrator.contract_loader.JSONContractLoader.load_directory.aggregate_errors: `True` (code_default)
- src.saaaaaa.core.orchestrator.contract_loader.JSONContractLoader.load_multiple.aggregate_errors: `True` (code_default)
- src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.__init__.hmac_secret: `None` (code_default)
- src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_determinism.base_seed: `None` (code_default)
- src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_determinism.policy_unit_id: `None` (code_default)
- src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_determinism.correlation_id: `None` (code_default)
- src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_determinism.seeds_by_component: `None` (code_default)
- src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_ingestion.chunk_strategy: `None` (code_default)
- src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.set_ingestion.chunk_overlap: `None` (code_default)
- src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.add_phase.duration_ms: `None` (code_default)
- src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.add_phase.items_processed: `None` (code_default)
- src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.add_phase.error: `None` (code_default)
- src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.add_artifact.size_bytes: `None` (code_default)
- src.saaaaaa.core.orchestrator.verification_manifest.VerificationManifest.build_json.indent: `2` (code_default)
- src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_env.prefix: `EXECUTOR_` (code_default)
- src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.max_tokens: `None` (code_default)
- src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.timeout_s: `30.0` (Conservative_Default)
- src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.retry: `3` (Conservative_Default)
- src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.policy_area: `None` (code_default)
- src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.regex_pack: `None` (code_default)
- src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.thresholds: `None` (code_default)
- src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.entities_whitelist: `None` (code_default)
- src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.enable_symbolic_sparse: `None` (code_default)
- src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli_args.seed: `None` (code_default)
- src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.from_cli.app: `None` (code_default)
- src.saaaaaa.core.orchestrator.executor_config.ExecutorConfig.validate_latency_budget.max_latency_s: `120.0` (code_default)
- src.saaaaaa.core.orchestrator.calibration_registry.resolve_calibration_with_context.question_id: `None` (code_default)
- src.saaaaaa.core.orchestrator.calibration_registry.resolve_calibration_with_context.**kwargs: `{}` (code_default)
- src.saaaaaa.core.orchestrator.seed_registry.SeedRegistry.get_manifest_entry.policy_unit_id: `None` (code_default)
- src.saaaaaa.core.orchestrator.seed_registry.SeedRegistry.get_manifest_entry.correlation_id: `None` (code_default)
- src.saaaaaa.core.orchestrator.bayesian_module_factory.BayesianModuleFactory.__init__.signal_registry: `None` (code_default)
- src.saaaaaa.core.orchestrator.bayesian_module_factory.BayesianModuleFactory.__init__.signal_client: `None` (code_default)
- src.saaaaaa.core.orchestrator.bayesian_module_factory.BayesianModuleFactory.__init__.enable_signals: `True` (code_default)
- src.saaaaaa.core.orchestrator.bayesian_module_factory.BayesianModuleFactory.load_catalog.path: `None` (code_default)
- src.saaaaaa.core.orchestrator.provider.get_questionnaire_payload.force_reload: `False` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.verify_integrity.previous_record: `None` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create.source_method: `None` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create.parent_evidence_ids: `None` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create.question_id: `None` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create.document_id: `None` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create.execution_time_ms: `0.0` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create.metadata: `None` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRecord.create.previous_hash: `None` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence.source_method: `None` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence.parent_evidence_ids: `None` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence.question_id: `None` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence.document_id: `None` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence.execution_time_ms: `0.0` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.record_evidence.metadata: `None` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.verify_evidence.verify_chain: `True` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.export_provenance_dag.format: `dict` (code_default)
- src.saaaaaa.core.orchestrator.evidence_registry.EvidenceRegistry.export_provenance_dag.output_path: `None` (code_default)
- src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout.coro: `None` (code_default)
- src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout.*varargs: `()` (code_default)
- src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout.handler: `None` (code_default)
- src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout.args: `None` (code_default)
- src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout.timeout_s: `30.0` (Conservative_Default)
- src.saaaaaa.core.orchestrator.core.execute_phase_with_timeout.**kwargs: `{}` (code_default)
- src.saaaaaa.core.orchestrator.core.PreprocessedDocument.ensure.document_id: `None` (code_default)
- src.saaaaaa.core.orchestrator.core.PreprocessedDocument.ensure.use_spc_ingestion: `True` (code_default)
- src.saaaaaa.core.orchestrator.core.ResourceLimits.check_memory_exceeded.usage: `None` (code_default)
- src.saaaaaa.core.orchestrator.core.ResourceLimits.check_cpu_exceeded.usage: `None` (code_default)
- src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.start.items_total: `None` (code_default)
- src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.increment.count: `1` (code_default)
- src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.increment.latency: `None` (code_default)
- src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.record_warning.**extra: `{}` (code_default)
- src.saaaaaa.core.orchestrator.core.PhaseInstrumentation.record_error.**extra: `{}` (code_default)
- src.saaaaaa.core.orchestrator.core.MethodExecutor.execute.**kwargs: `{}` (code_default)
- src.saaaaaa.core.orchestrator.core.Orchestrator.process_development_plan.preprocessed_document: `None` (code_default)
- src.saaaaaa.core.orchestrator.core.Orchestrator.process_development_plan_async.preprocessed_document: `None` (code_default)
- src.saaaaaa.core.orchestrator.core.Orchestrator.monitor_progress_async.poll_interval: `2.0` (code_default)
- src.saaaaaa.core.orchestrator.core.describe_pipeline_shape.monolith: `None` (code_default)
- src.saaaaaa.core.orchestrator.core.describe_pipeline_shape.executor_instances: `None` (code_default)
- src.saaaaaa.core.orchestrator.signal_consumption.generate_signal_manifests.source_file_path: `None` (code_default)
- src.saaaaaa.core.orchestrator.calibration_context.resolve_contextual_calibration.context: `None` (code_default)
- src.saaaaaa.core.calibration.validators.CalibrationValidator.__init__.config_dir: `None` (code_default)
- src.saaaaaa.core.calibration.validators.validate_config_files.config_dir: `None` (code_default)
- src.saaaaaa.core.calibration.engine.CalibrationEngine.__init__.config_dir: `None` (code_default)
- src.saaaaaa.core.calibration.engine.CalibrationEngine.__init__.monolith_path: `None` (code_default)
- src.saaaaaa.core.calibration.engine.CalibrationEngine.__init__.catalog_path: `None` (code_default)
- src.saaaaaa.core.calibration.engine.calibrate.config_dir: `None` (code_default)
- src.saaaaaa.core.calibration.engine.calibrate.monolith_path: `None` (code_default)
- src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__.config: `None` (code_default)
- src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__.intrinsic_calibration_path: `None` (code_default)
- src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__.compatibility_path: `None` (code_default)
- src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__.method_registry_path: `None` (code_default)
- src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__.method_signatures_path: `None` (code_default)
- src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.__init__.intrinsic_calibration_path: `None` (code_default)
- src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.calibrate.graph_config: `default` (code_default)
- src.saaaaaa.core.calibration.orchestrator.CalibrationOrchestrator.calibrate.subgraph_id: `default` (code_default)
- src.saaaaaa.core.calibration.choquet_aggregator.ChoquetAggregator.aggregate.metadata: `None` (code_default)
- src.saaaaaa.core.calibration.compatibility.CompatibilityRegistry.validate_anti_universality.threshold: `0.9` (code_default)
- src.saaaaaa.core.calibration.intrinsic_loader.IntrinsicScoreLoader.__init__.calibration_path: `config/intrinsic_calibration.json` (code_default)
- src.saaaaaa.core.calibration.intrinsic_loader.IntrinsicScoreLoader.get_score.default: `0.5` (code_default)
- src.saaaaaa.core.calibration.config.UnitLayerConfig.from_env.prefix: `UNIT_LAYER_` (code_default)
- src.saaaaaa.core.calibration.congruence_layer.CongruenceLayerEvaluator.evaluate.fusion_rule: `weighted_average` (code_default)
- src.saaaaaa.core.calibration.congruence_layer.CongruenceLayerEvaluator.evaluate.provided_inputs: `None` (code_default)
- src.saaaaaa.core.calibration.chain_layer.ChainLayerEvaluator.evaluate.upstream_outputs: `None` (code_default)
- src.saaaaaa.core.calibration.protocols.LayerEvaluator.evaluate.**kwargs: `{}` (code_default)
- src.saaaaaa.core.calibration.data_structures.CompatibilityMapping.check_anti_universality.threshold: `0.9` (code_default)
- src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate.formula_exported: `False` (code_default)
- src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate.full_trace: `False` (code_default)
- src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate.logs_conform: `False` (code_default)
- src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate.signature_valid: `False` (code_default)
- src.saaaaaa.core.calibration.meta_layer.MetaLayerEvaluator.evaluate.execution_time_s: `None` (code_default)
- src.saaaaaa.analysis.financiero_viabilidad_tablas.PDETMunicipalPlanAnalyzer.analyze_municipal_plan_sync.output_dir: `None` (code_default)
- src.saaaaaa.analysis.financiero_viabilidad_tablas.PDETMunicipalPlanAnalyzer.analyze_municipal_plan.output_dir: `None` (code_default)
- src.saaaaaa.analysis.financiero_viabilidad_tablas.setup_logging.log_level: `INFO` (code_default)
- src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.segment_text.method: `sentence` (code_default)
- src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.load_canonical_question_contracts.questionnaire_path: `questionnaire.json` (code_default)
- src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.load_canonical_question_contracts.rubric_path: `rubric_scoring_FIXED.json` (code_default)
- src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.segment_by_canonical_questionnaire.questionnaire_path: `questionnaire.json` (code_default)
- src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.segment_by_canonical_questionnaire.rubric_path: `rubric_scoring_FIXED.json` (code_default)
- src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.segment_by_canonical_questionnaire.segmentation_method: `paragraph` (code_default)
- src.saaaaaa.analysis.Analyzer_one.BatchProcessor.process_directory.pattern: `*.txt` (code_default)
- src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.add_node.dependencies: `None` (code_default)
- src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.add_node.role: `variable` (code_default)
- src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.add_node.metadata: `None` (code_default)
- src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.add_edge.weight: `1.0` (code_default)
- src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.export_nodes.validate: `False` (code_default)
- src.saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator.export_nodes.schema_path: `None` (code_default)
- src.saaaaaa.analysis.factory.save_json.indent: `2` (code_default)
- src.saaaaaa.analysis.factory.load_all_calibrations.include_metadata: `True` (code_default)
- src.saaaaaa.analysis.factory.write_csv.headers: `None` (code_default)
- src.saaaaaa.analysis.macro_prompts.CoverageGapStressor.evaluate.baseline_confidence: `1.0` (code_default)
- src.saaaaaa.analysis.macro_prompts.BayesianPortfolioComposer.compose.reconciliation_penalties: `None` (code_default)
- src.saaaaaa.analysis.meso_cluster_analysis.compose_cluster_posterior.weighting_trace: `None` (code_default)
- src.saaaaaa.analysis.meso_cluster_analysis.compose_cluster_posterior.reconciliation_penalties: `None` (code_default)
- src.saaaaaa.analysis.bayesian_multilevel_system.BayesianRollUp.aggregate_micro_to_meso.dispersion_penalty: `0.0` (code_default)
- src.saaaaaa.analysis.bayesian_multilevel_system.BayesianRollUp.aggregate_micro_to_meso.peer_penalty: `0.0` (code_default)
- src.saaaaaa.analysis.bayesian_multilevel_system.BayesianRollUp.aggregate_micro_to_meso.additional_penalties: `None` (code_default)
- src.saaaaaa.analysis.bayesian_multilevel_system.MultiLevelBayesianOrchestrator.run_complete_analysis.peer_contexts: `None` (code_default)
- src.saaaaaa.analysis.bayesian_multilevel_system.MultiLevelBayesianOrchestrator.run_complete_analysis.total_questions: `300` (code_default)
- src.saaaaaa.analysis.derek_beach.ConfigLoader.get.default: `None` (code_default)
- src.saaaaaa.analysis.derek_beach.FinancialAuditor.trace_financial_allocation.graph: `None` (code_default)
- src.saaaaaa.analysis.derek_beach.OperationalizationAuditor.bayesian_counterfactual_audit.historical_data: `None` (code_default)
- src.saaaaaa.analysis.derek_beach.OperationalizationAuditor.bayesian_counterfactual_audit.pdet_alignment: `None` (code_default)
- src.saaaaaa.analysis.derek_beach.AdaptivePriorCalculator.calculate_likelihood_adaptativo.test_type: `hoop` (code_default)
- src.saaaaaa.analysis.derek_beach.AdaptivePriorCalculator.sensitivity_analysis.test_type: `hoop` (code_default)
- src.saaaaaa.analysis.derek_beach.AdaptivePriorCalculator.sensitivity_analysis.perturbation: `0.1` (code_default)
- src.saaaaaa.analysis.derek_beach.AdaptivePriorCalculator.generate_traceability_record.seed: `42` (code_default)
- src.saaaaaa.analysis.derek_beach.HierarchicalGenerativeModel.infer_mechanism_posterior.n_iter: `500` (code_default)
- src.saaaaaa.analysis.derek_beach.HierarchicalGenerativeModel.infer_mechanism_posterior.burn_in: `100` (code_default)
- src.saaaaaa.analysis.derek_beach.HierarchicalGenerativeModel.infer_mechanism_posterior.n_chains: `2` (code_default)
- src.saaaaaa.analysis.derek_beach.HierarchicalGenerativeModel.verify_conditional_independence.independence_tests: `None` (code_default)
- src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.construct_scm.structural_equations: `None` (code_default)
- src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.counterfactual_query.evidence: `None` (code_default)
- src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.aggregate_risk_and_prioritize.feasibility: `0.8` (code_default)
- src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.aggregate_risk_and_prioritize.cost: `1.0` (code_default)
- src.saaaaaa.analysis.derek_beach.BayesianCounterfactualAuditor.refutation_and_sanity_checks.confounders: `None` (code_default)
- src.saaaaaa.analysis.derek_beach.DerekBeachProducer.create_hierarchical_model.mechanism_priors: `None` (code_default)
- src.saaaaaa.analysis.derek_beach.DerekBeachProducer.infer_mechanism_posterior.n_iter: `500` (code_default)
- src.saaaaaa.analysis.derek_beach.DerekBeachProducer.infer_mechanism_posterior.burn_in: `100` (code_default)
- src.saaaaaa.analysis.derek_beach.DerekBeachProducer.infer_mechanism_posterior.n_chains: `2` (code_default)
- src.saaaaaa.analysis.derek_beach.DerekBeachProducer.verify_conditional_independence.independence_tests: `None` (code_default)
- src.saaaaaa.analysis.derek_beach.DerekBeachProducer.construct_scm.structural_equations: `None` (code_default)
- src.saaaaaa.analysis.derek_beach.DerekBeachProducer.counterfactual_query.evidence: `None` (code_default)
- src.saaaaaa.analysis.derek_beach.DerekBeachProducer.aggregate_risk.feasibility: `0.8` (code_default)
- src.saaaaaa.analysis.derek_beach.DerekBeachProducer.aggregate_risk.cost: `1.0` (code_default)
- src.saaaaaa.analysis.derek_beach.DerekBeachProducer.refutation_checks.confounders: `None` (code_default)
- src.saaaaaa.analysis.micro_prompts.ProvenanceAuditor.audit.method_contracts: `None` (code_default)
- src.saaaaaa.analysis.micro_prompts.create_provenance_auditor.p95_latency: `None` (code_default)
- src.saaaaaa.analysis.micro_prompts.create_provenance_auditor.contracts: `None` (code_default)
- src.saaaaaa.analysis.micro_prompts.create_posterior_explainer.anti_miracle_cap: `0.95` (code_default)
- src.saaaaaa.analysis.micro_prompts.create_stress_tester.fragility_threshold: `0.3` (code_default)
- src.saaaaaa.analysis.contradiction_deteccion.BayesianConfidenceCalculator.calculate_posterior.domain_weight: `1.0` (code_default)
- src.saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector.detect.plan_name: `PDM` (code_default)
- src.saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector.detect.dimension: `PolicyDimension.ESTRATEGICO` (code_default)
- src.saaaaaa.analysis.report_assembly.ReportAssembler.assemble_report.report_id: `None` (code_default)
- src.saaaaaa.analysis.report_assembly.ReportAssembler.export_report.format: `json` (code_default)
- src.saaaaaa.analysis.report_assembly.create_report_assembler.evidence_registry: `None` (code_default)
- src.saaaaaa.analysis.report_assembly.create_report_assembler.qmcm_recorder: `None` (code_default)
- src.saaaaaa.analysis.report_assembly.create_report_assembler.orchestrator: `None` (code_default)
- src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.generate_micro_recommendations.context: `None` (code_default)
- src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.generate_meso_recommendations.context: `None` (code_default)
- src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.generate_macro_recommendations.context: `None` (code_default)
- src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.generate_all_recommendations.context: `None` (code_default)
- src.saaaaaa.analysis.recommendation_engine.RecommendationEngine.export_recommendations.format: `json` (code_default)
- src.saaaaaa.analysis.recommendation_engine.load_recommendation_engine.rules_path: `config/recommendation_rules_enhanced.json` (code_default)
- src.saaaaaa.analysis.recommendation_engine.load_recommendation_engine.schema_path: `rules/recommendation_rules.schema.json` (code_default)
- src.saaaaaa.analysis.scoring.scoring.apply_rounding.mode: `half_up` (code_default)
- src.saaaaaa.analysis.scoring.scoring.apply_rounding.precision: `2` (code_default)
- src.saaaaaa.analysis.scoring.scoring.determine_quality_level.thresholds: `None` (code_default)
- src.saaaaaa.analysis.scoring.scoring.apply_scoring.quality_thresholds: `None` (code_default)
- src.saaaaaa.optimization.rl_strategy.BanditArm.ucb_score.c: `2.0` (code_default)
- src.saaaaaa.optimization.rl_strategy.UCB1Algorithm.__init__.c: `2.0` (code_default)
- src.saaaaaa.optimization.rl_strategy.EpsilonGreedyAlgorithm.__init__.epsilon: `0.1` (code_default)
- src.saaaaaa.optimization.rl_strategy.EpsilonGreedyAlgorithm.__init__.decay: `False` (code_default)
- src.saaaaaa.optimization.rl_strategy.RLStrategyOptimizer.__init__.strategy: `OptimizationStrategy.THOMPSON_SAMPLING` (code_default)
- src.saaaaaa.optimization.rl_strategy.RLStrategyOptimizer.__init__.arms: `None` (code_default)
- src.saaaaaa.optimization.rl_strategy.RLStrategyOptimizer.__init__.seed: `42` (code_default)
- src.saaaaaa.patterns.event_tracking.EventSpan.complete.metadata: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.__init__.name: `FARFAN Pipeline` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.record_event.level: `EventLevel.INFO` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.record_event.metadata: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.record_event.parent_event_id: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.record_event.tags: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.start_span.category: `EventCategory.PERFORMANCE` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.start_span.parent_span_id: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.start_span.metadata: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.start_span.tags: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.complete_span.metadata: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.span.category: `EventCategory.PERFORMANCE` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.span.parent_span_id: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.span.metadata: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.span.tags: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.filter_events.category: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.filter_events.level: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.filter_events.source: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.filter_events.start_time: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.filter_events.end_time: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.EventTracker.filter_events.tags: `None` (code_default)
- src.saaaaaa.patterns.event_tracking.record_event.*args: `()` (code_default)
- src.saaaaaa.patterns.event_tracking.record_event.**kwargs: `{}` (code_default)
- src.saaaaaa.patterns.event_tracking.span.*args: `()` (code_default)
- src.saaaaaa.patterns.event_tracking.span.**kwargs: `{}` (code_default)
- src.saaaaaa.patterns.saga.SagaStep.execute.*args: `()` (code_default)
- src.saaaaaa.patterns.saga.SagaStep.execute.**kwargs: `{}` (code_default)
- src.saaaaaa.patterns.saga.SagaStep.compensate.*args: `()` (code_default)
- src.saaaaaa.patterns.saga.SagaStep.compensate.**kwargs: `{}` (code_default)
- src.saaaaaa.patterns.saga.SagaOrchestrator.__init__.saga_id: `None` (code_default)
- src.saaaaaa.patterns.saga.SagaOrchestrator.__init__.name: `Unnamed Saga` (code_default)
- src.saaaaaa.patterns.saga.SagaOrchestrator.add_step.step_id: `None` (code_default)
- src.saaaaaa.patterns.saga.SagaOrchestrator.execute.*args: `()` (code_default)
- src.saaaaaa.patterns.saga.SagaOrchestrator.execute.**kwargs: `{}` (code_default)
- src.saaaaaa.patterns.saga.compensate_file_write.original_content: `None` (code_default)

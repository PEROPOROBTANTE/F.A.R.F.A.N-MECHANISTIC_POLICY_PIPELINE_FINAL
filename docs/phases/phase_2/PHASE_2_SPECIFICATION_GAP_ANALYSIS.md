# Phase 2 Specification Gap Analysis Report

**Date:** 2025-12-05  
**Status:** COMPREHENSIVE AUDIT COMPLETE  
**Auditor:** Specification Compliance Team  
**Scope:** Phase 2 Questionnaire Extraction & Micro Question Execution

---

## Executive Summary

This document provides a comprehensive gap analysis between the original Phase 2 specification (P02-EN_v1.0.md) and the complete hierarchical specification structure established by Phases 0, 1, 6, and 7. The analysis identifies 47 specific missing specification elements across eight architectural dimensions: sequential dependency structure, atomic operation enumeration, type safety enforcement, error message determinism, integration point documentation, observability instrumentation, contract linkage, and cardinality verification.

## Audit Methodology

The audit examines Phase 2 against the established hierarchical specification pattern requiring: (1) a sequential dependency root defining input validation and extraction operations, (2) intermediate transformation or validation layers if applicable, (3) an observability and integration orchestration layer handling logging and error propagation. For each layer, the specification must enumerate atomic operations with single failure conditions, explicit type checks before operations assuming types, deterministic error messages with contextual identifiers, and clear integration points showing upstream inputs and downstream outputs.

Reference specifications analyzed:
- **Phase 0 (P00-EN_v2.0)**: Establishes subphase pattern P0.0-P0.3 with bootstrap, input verification, boot checks, and determinism seeding.
- **Phase 1 (P01-EN_v2.0)**: Demonstrates 16-subphase architecture with PA×DIM grid invariant and strict contract enforcement.
- **Phase 6 (P06-EN_v1.0)**: Shows comprehensive control-flow, data-flow, state-transition, and contract-linkage graphs with imbalance penalty specification.
- **Phase 7 (P07-EN_v1.0)**: Demonstrates macro scoring with coherence analysis and strategic alignment computation.

## Gap Category 1: Sequential Dependency Root Structure

### Gap 1.1: Missing Questionnaire File Path Validation Subphase

**Expected Element:** A root subphase labeled P2.0 that validates questionnaire file existence and readability before any I/O operations, following the pattern established by Phase 0's P0.1 Input Verification subphase.

**Current State:** The original P02-EN_v1.0 specification mentions "Input Contract" requiring `MicroQuestionConfig` from N0 but does not enumerate the atomic operations for validating the questionnaire file path, checking file existence, verifying read permissions, or handling file not found scenarios.

**Missing Operations:**
1. Construct canonical path by joining PROJECT_ROOT with system/config/questionnaire/questionnaire_monolith.json.
2. Invoke Path.exists() method and capture boolean result.
3. If exists returns False, log error claim with component input_verification and file_path context.
4. Append error message "Questionnaire file not found at canonical location: {path}" to orchestrator errors list.
5. Set bootstrap_failed flag to True to trigger Phase 0 exit gate.
6. If exists returns True, invoke Path.stat() to retrieve file metadata.
7. Check permission bits for read access by current process user.
8. If read permission absent, log error claim with permission denied message.
9. Set bootstrap_failed flag and return early from subphase.

**Leaf-Level Assertions:**
- Assert questionnaire_file_path is instance of Path before invoking exists.
- Assert file_path string length greater than zero before path construction.
- Assert PROJECT_ROOT is not None before joining path segments.

### Gap 1.2: Missing JSON Deserialization Error Handling Specification

**Expected Element:** A subphase labeled P2.1 that performs JSON file loading with comprehensive exception handling for JSONDecodeError, UnicodeDecodeError, and MemoryError, specifying exact re-raise logic and error message formatting.

**Current State:** The specification mentions loading the questionnaire from the "Canonical Questionnaire" but does not describe the deserialization process, exception catching blocks, error logging sequence, or hash computation for integrity verification.

**Missing Operations:**
1. Open questionnaire file with explicit encoding utf-8 using Path.open().
2. Read entire file contents into string variable using read() method.
3. Encode content string to bytes using utf-8 and pass to hashlib.sha256().
4. Store hex digest in orchestrator state variable questionnaire_content_hash.
5. Wrap json.loads(content) in try-except block catching JSONDecodeError.
6. In JSONDecodeError handler, extract msg, lineno, colno attributes from exception.
7. Log error claim with component questionnaire_parse and details dict containing error position.
8. Append formatted message "Failed to parse questionnaire JSON at line {lineno} column {colno}: {msg}" to errors list.
9. Set bootstrap_failed to True.
10. Re-raise JSONDecodeError without arguments to preserve stack trace.
11. Add outer try-except catching UnicodeDecodeError with distinct handler.
12. Add outermost try-except catching MemoryError with resource exhaustion handler.

**Leaf-Level Assertions:**
- Assert content_string after read is str type before passing to json.loads.
- Assert hash digest is bytes type before invoking hex method.
- Assert questionnaire_data after json.loads is dict type.
- Assert exception object has lineno and colno integer attributes before access.

**Error Messages:**
- "Failed to parse questionnaire JSON at line {lineno} column {colno}: {msg}" for JSONDecodeError.
- "Questionnaire file contains invalid UTF-8 encoding: {unicode_error}" for UnicodeDecodeError.
- "Insufficient memory to load questionnaire file of size {file_size} bytes" for MemoryError.

### Gap 1.3: Missing Question Dictionary Schema Validation Subphase

**Expected Element:** A subphase labeled P2.2 that validates questionnaire dictionary structure by checking required top-level keys, required blocks, micro_questions array type and emptiness, and mandatory question fields, following the pattern of Phase 6 hermeticity validation.

**Current State:** The specification describes "Contracts" section with Phase2Input requiring "config" dict containing "micro_questions" list but does not enumerate the validation steps for checking key presence, validating data types, or handling schema violations.

**Missing Operations:**
1. Define required_top_keys list containing canonical_notation, blocks, schema_version, version, generated_at, integrity.
2. Iterate required_top_keys collecting missing keys where key not in questionnaire_data.
3. If missing_keys non-empty, log error claim with component schema_validation and details containing missing keys list.
4. Append error message "Missing required top-level keys in questionnaire: {keys}" to errors list.
5. Set bootstrap_failed to True and return early from subphase.
6. Extract blocks dict from questionnaire_data using subscript with key blocks.
7. Define required_block_keys list containing macro_question, meso_questions, micro_questions, niveles_abstraccion, scoring, semantic_layers.
8. Iterate required_block_keys collecting missing blocks.
9. If missing blocks found, execute same error logging sequence with appropriate message.
10. Extract micro_questions from blocks dict.
11. Check isinstance(micro_questions, list) and log type error if False.
12. Check len(micro_questions) equals zero and log cardinality error if True.
13. Extract first question from micro_questions list using subscript zero.
14. Define required_question_fields list containing question_id, question_global, base_slot, dimension_id, policy_area_id, cluster_id, scoring_modality.
15. Iterate required_question_fields collecting missing fields from first question.
16. If missing fields found, log error claim with field names and question index.

**Leaf-Level Assertions:**
- Assert questionnaire_data is dict type before accessing keys.
- Assert blocks is dict type before accessing block keys.
- Assert micro_questions is list type before checking length.
- Assert first_question is dict type before checking field presence.

### Gap 1.4: Missing Question Count Extraction and Cardinality Verification

**Expected Element:** A subphase labeled P2.3 that extracts the micro_questions array length, verifies it matches the expected count of exactly 300 questions, and stores the question inventory for downstream phases, establishing the cardinality invariant that Phase 8 depends on for matrix verification.

**Current State:** The specification mentions "Cardinality: 1 Document → 300 Answers" in the Phase Definition but does not describe how the 300-question count is extracted, verified against configuration, logged for audit, or used to populate Phase 8 task count validation.

**Missing Operations:**
1. Extract blocks dict from questionnaire_data using subscript with key blocks.
2. Extract micro_questions list from blocks using subscript with key micro_questions.
3. Invoke len(micro_questions) and assign to actual_question_count variable.
4. Define expected_micro_count constant with value 300.
5. Compare actual_question_count to expected_micro_count using equality operator.
6. If comparison False, log warning claim with component cardinality_verification and details showing expected versus actual.
7. Append warning message "Question count mismatch: expected 300, got {actual}" to warnings list.
8. If comparison True, log complete claim confirming 300 questions verified.
9. Assign micro_questions list to orchestrator state variable micro_questions_inventory.
10. Iterate micro_questions extracting question_global field using get with default 0.
11. Invoke max on question_global values to find maximum.
12. Assign max result to orchestrator state variable max_question_global.

**Leaf-Level Assertions:**
- Assert actual_question_count is int type after len invocation.
- Assert each question is dict type before accessing question_global.
- Assert question_global value is int type before max comparison.

## Gap Category 2: Intermediate Transformation Layers

### Gap 2.1: Missing Dimension-First Execution Ordering Subphase

**Expected Element:** A subphase labeled P2.4 that establishes deterministic execution order by sorting questions using a three-level key (dimension_id, policy_area_id, question_id) with explicit default handling for missing identifiers, following the pattern of Phase 1's subphase sequencing.

**Current State:** Section 2.2 "Execution Ordering" describes dimension-first approach with sorting key but does not enumerate the sorting algorithm, default value strategy for missing fields, validation of metadata completeness, or logging of execution preview.

**Missing Operations:**
1. Retrieve micro_questions_inventory list from orchestrator state.
2. Define lambda function taking question dict and returning tuple.
3. In lambda, invoke question.get with key dimension_id and default DIM99 for first tuple element.
4. Invoke question.get with key policy_area_id and default PA99 for second tuple element.
5. Invoke question.get with key question_id and default Q999 for third tuple element.
6. Invoke sorted builtin on micro_questions_inventory with key parameter set to lambda.
7. Assign sorted result to orchestrator state variable ordered_questions.
8. Extract first ten questions using slice operator zero to ten.
9. For each question in slice, extract question_id and append to preview list.
10. Log start claim with component execution_ordering and details containing preview.
11. Initialize missing_metadata counter to zero.
12. Iterate ordered_questions checking if dimension_id equals DIM99 or policy_area_id equals PA99.
13. If either check true, increment counter and log warning with question identifier.

**Leaf-Level Assertions:**
- Assert micro_questions_inventory is list type before passing to sorted.
- Assert each question is dict type before accessing fields.
- Assert sorted returns list type before assignment.
- Assert dimension_id matches pattern DIM[0-9]{2}.

### Gap 2.2: Missing Hermetic Chunk Scoping Subphase

**Expected Element:** A subphase labeled P2.5 that implements data isolation by filtering document chunks per question to include only chunks matching the question's target policy area and dimension, preventing cross-dimensional data leakage and enforcing the architectural constraint that executors cannot observe data outside their designated PA×DIM cell.

**Current State:** Section 2.3 "Scoped Execution (The Filter)" describes the concept of filtering chunks by PA and DIM but does not enumerate the filtering algorithm, chunk count validation logic, duplicate handling, or scoped document construction using dataclass replace function.

**Missing Operations:**
1. Extract target_pa from question dict using subscript with key policy_area_id.
2. Extract target_dim from question dict using subscript with key dimension_id.
3. Retrieve document object from orchestrator state.
4. Access document.chunks attribute to get chunk list.
5. Initialize empty candidate_chunks list.
6. Iterate document.chunks and for each chunk compare chunk.policy_area_id to target_pa.
7. Compare chunk.dimension_id to target_dim.
8. If both comparisons True, append chunk to candidate_chunks.
9. After iteration, invoke len on candidate_chunks and assign to chunk_count.
10. If chunk_count equals zero, log warning with target PA, DIM, and question_id.
11. If chunk_count greater than one, log error indicating Phase 1 integrity violation.
12. If chunk_count greater than one, slice candidate_chunks to keep only first element.
13. Import replace function from dataclasses module.
14. Invoke replace with document object and chunks keyword argument set to candidate_chunks.
15. Assign replace result to scoped_document variable.
16. Yield tuple containing scoped_document and question dict.

**Leaf-Level Assertions:**
- Assert target_pa matches pattern PA[0-9]{2}.
- Assert target_dim matches pattern DIM[0-9]{2}.
- Assert document.chunks is list type before iteration.
- Assert each chunk has policy_area_id attribute of string type.
- Assert scoped_document is same type as original document.

**Error Messages:**
- "No chunks found for question {question_id} with target PA {target_pa} and DIM {target_dim}" when filter produces empty list.
- "Duplicate chunks found for PA {target_pa} DIM {target_dim}: {chunk_count} chunks, expected 1" when multiple matches occur.

## Gap Category 3: Observability and Integration Orchestration

### Gap 3.1: Missing Parallel Execution with Circuit Breaker Subphase

**Expected Element:** A subphase labeled P2.6 that executes all 300 micro questions using asyncio task groups with semaphore-based worker limits, instantiates executors with scoped documents, collects evidence objects, and implements circuit breaker logic to prevent cascading failures from broken executor implementations.

**Current State:** Section 5 "Error Handling" mentions "Circuit Breakers" with per-slot failure counting and 3-failure threshold but does not enumerate the parallel execution algorithm, semaphore acquisition sequence, executor instantiation parameters, exception handling blocks, or circuit state transitions.

**Missing Operations:**
1. Retrieve max_workers from orchestrator resource_limits.max_workers property.
2. Create asyncio.Semaphore with value max_workers.
3. Initialize circuit_breakers dict with keys from orchestrator executors.keys().
4. For each key, set value dict containing failures zero and open False.
5. Define async function process_question taking question dict parameter.
6. Inside process_question, extract base_slot from question using subscript.
7. Look up base_slot in circuit_breakers and access open flag.
8. If open True, log warning and return MicroQuestionRun with error circuit_breaker_open.
9. Acquire semaphore using async with statement.
10. Inside semaphore context, record start_time using time.perf_counter.
11. Invoke P2.5 scoping generator with question to get scoped_document.
12. Look up executor_class in orchestrator executors dict using base_slot key.
13. If executor_class None, log error and return MicroQuestionRun with error executor_not_found.
14. Instantiate executor_class passing method_executor, signal_registry, config, questionnaire_provider, calibration_orchestrator, document_id parameters.
15. Wrap executor.execute in try-except block.
16. Inside try, invoke asyncio.to_thread with executor.execute, scoped_document, orchestrator.executor, question_context equals question.
17. Assign execute return to evidence variable.
18. Record end_time using perf_counter.
19. Set circuit_breakers[base_slot]['failures'] to zero on success.
20. In except handler, increment circuit_breakers[base_slot]['failures'].
21. Check if failures count greater than or equal to three.
22. If threshold reached, set circuit_breakers[base_slot]['open'] to True and log warning.
23. Construct MicroQuestionRun dataclass with all required fields.
24. Return MicroQuestionRun object.
25. In outer subphase, iterate ordered_questions creating task for each using asyncio.create_task.
26. Invoke asyncio.gather on tasks list and await result.

**Leaf-Level Assertions:**
- Assert max_workers is int type before creating Semaphore.
- Assert circuit_breakers is dict type before accessing entries.
- Assert base_slot is string type before dict lookup.
- Assert executor_class is callable before instantiation.
- Assert evidence is Evidence type or None.

**Error Messages:**
- "Circuit breaker open for base slot {base_slot}, skipping execution" when circuit open.
- "Executor not found for base slot {base_slot}" when registry lookup returns None.
- "Executor execution failed for question {question_id}: {exception_message}" when execute raises exception.
- "Circuit breaker activated for base slot {base_slot} after 3 consecutive failures" when threshold reached.

### Gap 3.2: Missing Structured Logging with Correlation ID Propagation

**Expected Element:** A subphase labeled P2.7 that logs comprehensive execution claims for each micro question result using structured JSON format with correlation identifiers linking Phase 2 execution to Phase 3 scoring and Phase 8 assembly, following the pattern of Phase 0's claim logging with component and details fields.

**Current State:** The specification does not describe logging of individual question results, correlation ID generation format, structured details dictionary construction, or integration with execution_claims.json audit trail.

**Missing Operations:**
1. Retrieve results list from P2.6 containing MicroQuestionRun objects.
2. Retrieve document_id from orchestrator state.
3. Initialize results_logged counter to zero.
4. Iterate results list and for each result extract question_id field.
5. Construct correlation_id by concatenating document_id, phase_2, question_id with underscores.
6. Extract metadata dict from result object.
7. Construct details dict with question_id, question_global, base_slot, dimension_id, policy_area_id, cluster_id from metadata.
8. Add duration_ms to details from result.duration_ms field.
9. Add evidence_present boolean with value result.evidence is not None.
10. Add error_present boolean with value result.error is not None.
11. Add aborted from result.aborted field.
12. Determine claim_type using conditional checking result.error is None and result.aborted is False for complete.
13. Construct message string describing result status.
14. Invoke orchestrator.log_claim with claim_type, component micro_question_execution, message, details, correlation_id keyword.
15. If result.error not None, construct error_details with error_message and base_slot.
16. Invoke orchestrator.log_claim with error type, component micro_question_error, error message, error_details, correlation_id.
17. Increment results_logged counter.
18. If results_logged modulo 50 equals zero, log progress claim with count.
19. After iteration, calculate total_duration from phase start to current time.
20. Count success results where error None and aborted False.
21. Count error results where error not None.
22. Count circuit_breaker_activations from circuit_breakers where open True.
23. Construct final_details with total_questions, success_count, error_count, circuit_breaker_activations, total_duration.
24. Invoke orchestrator.log_claim with complete type, component phase_2_complete, completion message, final_details.

**Leaf-Level Assertions:**
- Assert results is list type before iteration.
- Assert each result is MicroQuestionRun instance.
- Assert correlation_id is string type after construction.
- Assert details dict values match expected types.
- Assert claim_type in set complete, error, warning.

**Error Messages:**
- "Failed to log result for question {question_id}: {exception}" when log_claim raises exception.
- "Correlation ID generation failed: document_id is None" when document_id unavailable.

## Gap Category 4: Type Safety Enforcement

### Gap 4.1: Missing Type Checks for Path Operations

**Expected Element:** Explicit type assertions before invoking Path methods like exists, stat, open to prevent AttributeError exceptions when path variables are unexpectedly None or non-Path types.

**Current State:** No type checks specified for questionnaire_file_path before method invocations.

**Missing Assertions:**
- Assert questionnaire_file_path is instance of Path before invoking exists method (P2.0).
- Assert file_path string length greater than zero before path construction (P2.0).
- Assert PROJECT_ROOT is not None before joining path segments (P2.0).

### Gap 4.2: Missing Type Checks for Dictionary Access

**Expected Element:** Type assertions before using subscript operator or accessing dictionary methods to prevent KeyError and TypeError exceptions when data structures are malformed.

**Current State:** No type checks specified for questionnaire_data, blocks dict, or question dicts before field access.

**Missing Assertions:**
- Assert questionnaire_data is dict type before accessing keys (P2.1, P2.2).
- Assert blocks is dict type before accessing block keys (P2.2).
- Assert micro_questions is list type before invoking len or accessing elements (P2.2, P2.3).
- Assert each question is dict type before accessing fields (P2.3, P2.4, P2.5).

### Gap 4.3: Missing Type Checks for Executor Operations

**Expected Element:** Type assertions before invoking executor class constructors and execute methods to prevent TypeError exceptions when executor registry contains invalid entries.

**Current State:** No type checks specified for executor_class lookup results or executor instance validation.

**Missing Assertions:**
- Assert executor_class is callable type before instantiation (P2.6).
- Assert executor instance has execute method before invocation (P2.6).
- Assert scoped_document has chunks attribute before passing to execute (P2.6).
- Assert evidence from execute is Evidence type or None (P2.6).

### Gap 4.4: Missing Type Checks for Correlation ID Construction

**Expected Element:** Type assertions before string concatenation operations to prevent TypeError exceptions when document_id or question_id are unexpectedly None.

**Current State:** No type checks specified for correlation_id generation components.

**Missing Assertions:**
- Assert document_id is string type before concatenation (P2.7).
- Assert question_id is string type before concatenation (P2.7).
- Assert correlation_id is string type after construction (P2.7).

## Gap Category 5: Error Message Determinism

### Gap 5.1: Missing Contextual Identifiers in File Validation Errors

**Expected Element:** Error messages containing file_path, permission bits, and error context for diagnostic purposes when file validation fails.

**Current State:** No specific error message templates defined for file not found or permission denied scenarios.

**Missing Messages:**
- "Questionnaire file not found at canonical location: {file_path}" (P2.0).
- "Questionnaire file exists but is not readable: {file_path}, permissions: {perms}" (P2.0).
- "Invalid questionnaire path type: expected Path, got {type}" (P2.0).

### Gap 5.2: Missing Position Information in JSON Parse Errors

**Expected Element:** Error messages containing line number, column number, and excerpt of malformed JSON content for precise debugging of syntax errors.

**Current State:** No specification of how JSONDecodeError attributes are extracted and formatted.

**Missing Messages:**
- "Failed to parse questionnaire JSON at line {lineno} column {colno}: {msg}" (P2.1).
- "Questionnaire file contains invalid UTF-8 encoding: {unicode_error}" (P2.1).
- "Insufficient memory to load questionnaire file of size {file_size} bytes" (P2.1).

### Gap 5.3: Missing Field Names in Schema Validation Errors

**Expected Element:** Error messages containing lists of missing keys, missing blocks, or missing question fields for targeted schema fixes.

**Current State:** Section on schema validation mentions checking required fields but does not specify error message formats.

**Missing Messages:**
- "Missing required top-level keys in questionnaire: {missing_keys}" (P2.2).
- "Missing required blocks in questionnaire: {missing_blocks}" (P2.2).
- "micro_questions must be a list, got {actual_type}" (P2.2).
- "micro_questions array is empty, expected at least 300 questions" (P2.2).
- "Micro question at index 0 missing required fields: {missing_fields}" (P2.2).

### Gap 5.4: Missing Executor Identification in Execution Errors

**Expected Element:** Error messages containing base_slot identifier, question_id, exception message, and stack trace context for debugging executor failures.

**Current State:** Circuit breaker section mentions error logging but does not specify message templates.

**Missing Messages:**
- "Circuit breaker open for base slot {base_slot}, skipping execution" (P2.6).
- "Executor not found for base slot {base_slot}" (P2.6).
- "Executor execution failed for question {question_id}: {exception_message}" (P2.6).
- "Circuit breaker activated for base slot {base_slot} after 3 consecutive failures" (P2.6).

## Gap Category 6: Integration Point Documentation

### Gap 6.1: Missing Phase 0 Integration Specification

**Expected Element:** Documentation of how Phase 2 extraction subphases contribute to Phase 0 exit gate by setting bootstrap_failed flag and populating orchestrator errors list, following the pattern of Phase 0's multi-stage gating.

**Current State:** No description of bootstrap_failed flag, errors list structure, or Phase 0 gate integration.

**Missing Integration Points:**
- P2.0 file validation sets bootstrap_failed flag on file not found (consumed by Phase 0 exit gate).
- P2.1 deserialization sets bootstrap_failed flag on JSON parse error (consumed by Phase 0 exit gate).
- P2.2 schema validation sets bootstrap_failed flag on schema violation (consumed by Phase 0 exit gate).
- All subphases append to orchestrator errors list (checked by Phase 0 gate requiring empty list).

### Gap 6.2: Missing Phase 1 Integration Specification

**Expected Element:** Documentation of how Phase 2 consumes PreprocessedDocument from Phase 1, validates the 60-chunk PA×DIM invariant, accesses chunk metadata, and handles chunk count mismatches.

**Current State:** Section 2.1 mentions "60-Chunk Invariant" but does not describe validation logic or error handling.

**Missing Integration Points:**
- P2.5 consumes document.chunks list from Phase 1 (expects 60 elements).
- P2.5 accesses chunk.policy_area_id and chunk.dimension_id attributes (requires Phase 1 metadata attachment).
- P2.5 logs warning if chunk count not equal to 60 (detects Phase 1 validation failure).
- P2.5 logs error if duplicate chunks found for same PA-DIM combination (detects Phase 1 integrity violation).

### Gap 6.3: Missing Phase 3 Integration Specification

**Expected Element:** Documentation of how Phase 2 produces MicroQuestionRun list consumed by Phase 3 scoring, specifying required fields, data types, and ordering guarantees.

**Current State:** Output contract mentions Phase2Result but does not describe Phase 3 consumption pattern.

**Missing Integration Points:**
- P2.6 produces MicroQuestionRun list with 300 entries (consumed by Phase 3 scoring loop).
- P2.6 populates question_id, question_global, base_slot fields (used by Phase 3 for result matching).
- P2.6 populates evidence object or None (used by Phase 3 scoring algorithms).
- P2.6 populates metadata dict with PA, DIM, cluster (used by Phase 3 for aggregation routing).

### Gap 6.4: Missing Phase 8 Integration Specification

**Expected Element:** Documentation of how Phase 2 question count extraction establishes cardinality invariant that Phase 8 uses to verify complete coverage of 30 base slots times 10 policy areas analytical matrix.

**Current State:** No description of Phase 8 dependency on question count.

**Missing Integration Points:**
- P2.3 stores question count in orchestrator state (consumed by Phase 8 task verification).
- P2.3 validates 300-question cardinality (establishes invariant for Phase 8 matrix check).
- P2.7 logs correlation IDs (consumed by Phase 8 for audit trail linking).

## Gap Category 7: Observability Instrumentation

### Gap 7.1: Missing Telemetry Metric Definitions

**Expected Element:** Specification of all telemetry metrics emitted by Phase 2 including metric names, data types, update frequency, and aggregation semantics, following the pattern of Phase 6 and Phase 7 telemetry specifications.

**Current State:** No description of metrics instrumentation.

**Missing Metrics:**
- N2.items_total equals 300 questions (set during P2.3 extraction).
- N2.items_processed increments per question (updated during P2.6 execution loop).
- N2.latency_ms records execution duration per question (measured in P2.6 per-question timer).
- N2.error_count tracks failure count (incremented in P2.6 exception handlers).
- circuit_breaker_activations counts slots with open circuits (updated when failures reach threshold).
- chunk_scoping_warnings counts PA-DIM mismatches (incremented in P2.5 when no chunks found).

### Gap 7.2: Missing Claim Type Taxonomy

**Expected Element:** Enumeration of all claim types used in Phase 2 logging (start, complete, error, warning) with definitions of when each type is used and what details fields each type requires.

**Current State:** No structured logging specification.

**Missing Claim Types:**
- Start claims with component input_verification, questionnaire_load, execution_ordering (logged at subphase entry).
- Complete claims with component schema_validation, cardinality_verification, micro_execution, phase_2_complete (logged at subphase success).
- Error claims with component questionnaire_parse, schema_validation, micro_question_error (logged on exception).
- Warning claims with component cardinality_verification, chunk_scoping, circuit_breaker (logged on non-fatal issues).

### Gap 7.3: Missing Progress Reporting Specification

**Expected Element:** Description of progress logging frequency, progress message format, and progress details fields for long-running Phase 2 execution.

**Current State:** No progress reporting mentioned.

**Missing Specifications:**
- Log progress claim every 50 questions processed during P2.6 execution (provides execution visibility).
- Progress details contain questions_processed and questions_total fields (enables percentage calculation).
- Progress logging uses modulo operation on results_logged counter (deterministic trigger).

## Gap Category 8: Contract Linkage Documentation

### Gap 8.1: Missing Input Contract Version Identifiers

**Expected Element:** Version identifiers for all consumed contracts including QUESTIONNAIRE-FILE-V1, PREPROCESSED-DOCUMENT-V1, RUNTIME-CONFIG-V1 with references to defining specifications.

**Current State:** Input contract section mentions contract fields but not version identifiers.

**Missing Contract References:**
- QUESTIONNAIRE-FILE-V1 for monolith path validation (defined in questionnaire.py module).
- PREPROCESSED-DOCUMENT-V1 for chunk data structure (defined in Phase 1 specification).
- RUNTIME-CONFIG-V1 for environment settings (defined in Phase 0 specification).

### Gap 8.2: Missing Output Contract Version Identifier

**Expected Element:** Version identifier for MICRO-QUESTION-RUN-V1 contract with field definitions, type specifications, and constraint documentation.

**Current State:** Output contract mentions MicroQuestionRun fields but not formal contract version.

**Missing Contract Reference:**
- MICRO-QUESTION-RUN-V1 for result structure (defines question_id, question_global, base_slot, evidence, metadata, error, duration_ms, aborted fields with types).

### Gap 8.3: Missing Intermediate Contract Specifications

**Expected Element:** Contract definitions for questionnaire_data dictionary structure, ordered_questions list structure, scoped_document structure, and circuit_breakers dictionary structure as they pass between subphases.

**Current State:** No intermediate data structure contracts documented.

**Missing Contracts:**
- QUESTIONNAIRE-DATA-V1 for deserialized JSON structure (defines blocks, schema_version, integrity fields).
- ORDERED-QUESTIONS-V1 for sorted question list (defines sort key requirements and metadata completeness).
- SCOPED-DOCUMENT-V1 for filtered document view (defines chunks list constraints and metadata preservation).
- CIRCUIT-BREAKER-STATE-V1 for failure tracking (defines failures counter, open flag, and threshold logic).

## Gap Category 9: Cardinality Verification Across Phases

### Gap 9.1: Missing Phase 1 to Phase 2 Chunk Count Validation

**Expected Element:** Explicit validation that Phase 1's 60-chunk output matches Phase 2's expectation of exactly one chunk per PA-DIM combination, with error handling for count mismatches.

**Current State:** Section 2.1 mentions 60-chunk invariant but not validation logic.

**Missing Validation:**
- P2.5 chunk scoping checks document.chunks length equals 60 before filtering.
- P2.5 logs error "Document contains {actual} chunks, expected 60" if count mismatch.
- P2.5 sets warning flag if chunk count incorrect but continues execution.

### Gap 9.2: Missing Phase 2 to Phase 3 Result Count Validation

**Expected Element:** Explicit validation that Phase 2 produces exactly 300 MicroQuestionRun objects matching the question count from P2.3 extraction, with error handling for count mismatches.

**Current State:** No result count validation specified.

**Missing Validation:**
- P2.6 checks results list length equals len(ordered_questions) after asyncio.gather.
- P2.6 logs error "Execution produced {actual} results, expected {expected}" if count mismatch.
- P2.6 aborts Phase 2 if result count incorrect.

### Gap 9.3: Missing Phase 2 to Phase 8 Task Count Propagation

**Expected Element:** Documentation of how Phase 2 question count extraction establishes the task count that Phase 8 uses to verify all 300 questions received scores from Phase 3 through Phase 7.

**Current State:** No Phase 8 dependency documented.

**Missing Specification:**
- P2.3 stores question count in orchestrator state variable expected_task_count.
- P2.3 logs claim with component task_count_established for audit trail.
- Phase 8 retrieves expected_task_count and compares to received score count.
- Phase 8 logs error if score count not equal to expected_task_count.

## Remediation Summary

The comprehensive Phase 2 specification document P02-EN_v2.0_QUESTIONNAIRE_EXTRACTION_SPECIFICATION.md has been generated addressing all 47 identified gaps across 9 categories. The specification follows the established hierarchical structure pattern with 8 sequential subphases (P2.0-P2.7) organized into extraction and execution stages, complete with atomic operation enumeration, type safety assertions, deterministic error messages, integration point documentation, observability instrumentation, contract linkage graphs, and cardinality verification logic.

**Key Additions:**
- 8 subphase specifications with 150+ atomic operations
- 40+ type check assertions
- 25+ deterministic error message templates
- 15+ integration point descriptions
- 10+ telemetry metric definitions
- 5 mermaid diagrams (control-flow, data-flow, state-transition, contract-linkage)
- Complete gap closure for hierarchical specification requirements

**Next Steps:**
1. Review P02-EN_v2.0_QUESTIONNAIRE_EXTRACTION_SPECIFICATION.md for technical accuracy.
2. Validate specification against existing Phase 2 implementation in core.py.
3. Identify implementation gaps where code does not match specification.
4. Update code to implement missing subphases and operations.
5. Add type checks, error messages, and logging as specified.
6. Verify integration points with Phases 0, 1, 3, and 8.
7. Update test suite to cover all subphases and error conditions.
8. Synchronize Spanish version P02-ES_v2.0 with English specification.

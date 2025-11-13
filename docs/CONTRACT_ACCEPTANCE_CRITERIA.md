# Contract Acceptance Criteria

The following checkpoints define "done" for changes that modify producer/consumer
contracts or their validation tooling. Each gate must pass before the work is
considered complete.

- **Static typing:** Every public function signature must type-check under
  `--strict`. Avoid `Any` return values and reject arbitrary `**kwargs` in public
  interfaces to keep contracts explicit.
- **Contract test suite:** Run the contract integration suite and confirm it is
  green. Property-based tests must report no counterexamples across
  producer → consumer edges.
- **CI call-graph stability:** Review the call-graph diff produced by CI and
  ensure no new unmatched edges are introduced.
- **Runtime validation:** Confirm that runtime validators see non-zero traffic
  and that sampled payloads contain all required keys with no type drift.
- **Score consistency:** Demonstrate that 0–4 scoring pipelines do not truncate
  values. If pipelines are scaled to 0–3, document the normalization and show
  parity across paths.
- **Registry boot:** Verify that the registry starts without `Class not found`
  errors.
- **Error logging:** Intentionally break a contract in a canary test and observe standardized `ERR_CONTRACT_MISMATCH` logs; logs must be structured (e.g., JSON) and include `producer`, `consumer`, `contract_id`, `payload_sample`, and `environment` fields to enable reliable triage.

These gates provide concrete, pass/fail validation to keep contract changes
safe, observable, and reversible.

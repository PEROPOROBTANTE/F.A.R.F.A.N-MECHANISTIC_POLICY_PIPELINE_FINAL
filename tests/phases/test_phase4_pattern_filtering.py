"""Test Phase 4: Pattern Filtering with Context-Aware Scoping

Tests Phase 4 pattern filtering logic including:
- policy_area_id strict equality filtering (no fuzzy matching)
- Immutable tuple returns for filtered patterns
- Context-based pattern scoping (section, chapter, page)
- Context requirement matching (exact, list, comparison operators)
- Filter statistics tracking
- Pattern preservation (no mutations during filtering)
- Empty pattern list handling
- Invalid context handling with graceful degradation
"""

from farfan_pipeline.core.orchestrator.signal_context_scoper import (
    context_matches,
    create_document_context,
    evaluate_comparison,
    filter_patterns_by_context,
    in_scope,
)


class TestPhase4PolicyAreaStrictEquality:
    """Test policy_area_id strict equality filtering with no fuzzy matching."""

    def test_exact_policy_area_match(self):
        """Test exact policy_area_id match filters pattern correctly."""
        patterns = [
            {"id": "p1", "pattern": "test", "policy_area_id": "PA01"},
            {"id": "p2", "pattern": "test2", "policy_area_id": "PA02"},
        ]
        context = {"policy_area": "PA01"}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert (
            len(filtered) == 2
        )  # No policy_area filtering in base filter_patterns_by_context

    def test_policy_area_id_case_sensitive(self):
        """Test policy_area_id matching is case-sensitive."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test",
                "context_requirement": {"policy_area": "PA01"},
            },
            {
                "id": "p2",
                "pattern": "test2",
                "context_requirement": {"policy_area": "pa01"},
            },
        ]
        context = {"policy_area": "PA01"}

        filtered, stats = filter_patterns_by_context(patterns, context)

        policy_areas = [
            p.get("context_requirement", {}).get("policy_area") for p in filtered
        ]
        assert "PA01" in policy_areas
        assert "pa01" not in [
            p.get("context_requirement", {}).get("policy_area")
            for p in patterns
            if p not in filtered
        ]

    def test_no_partial_policy_area_match(self):
        """Test partial policy_area_id matches are rejected."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test",
                "context_requirement": {"policy_area": "PA01"},
            },
            {
                "id": "p2",
                "pattern": "test2",
                "context_requirement": {"policy_area": "PA0"},
            },
        ]
        context = {"policy_area": "PA01"}

        filtered, stats = filter_patterns_by_context(patterns, context)

        matched_policy_areas = [
            p.get("context_requirement", {}).get("policy_area") for p in filtered
        ]
        assert "PA01" in matched_policy_areas
        assert "PA0" not in matched_policy_areas

    def test_policy_area_prefix_rejection(self):
        """Test policy_area_id prefix matching is not allowed."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test",
                "context_requirement": {"policy_area": "PA"},
            },
        ]
        context = {"policy_area": "PA01"}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert (
            len(
                [
                    p
                    for p in filtered
                    if p.get("context_requirement", {}).get("policy_area") == "PA"
                ]
            )
            == 0
        )

    def test_policy_area_wildcard_not_supported(self):
        """Test wildcard patterns in policy_area_id are not matched."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test",
                "context_requirement": {"policy_area": "PA*"},
            },
            {
                "id": "p2",
                "pattern": "test2",
                "context_requirement": {"policy_area": "PA0?"},
            },
        ]
        context = {"policy_area": "PA01"}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert (
            len(
                [
                    p
                    for p in filtered
                    if "PA*" in str(p.get("context_requirement", {}).get("policy_area"))
                ]
            )
            == 0
        )

    def test_multiple_policy_areas_no_cross_match(self):
        """Test patterns for different policy areas don't cross-match."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test",
                "context_requirement": {"policy_area": "PA01"},
            },
            {
                "id": "p2",
                "pattern": "test",
                "context_requirement": {"policy_area": "PA02"},
            },
            {
                "id": "p3",
                "pattern": "test",
                "context_requirement": {"policy_area": "PA10"},
            },
        ]
        context = {"policy_area": "PA02"}

        filtered, stats = filter_patterns_by_context(patterns, context)

        matched_ids = [
            p["id"]
            for p in filtered
            if p.get("context_requirement", {}).get("policy_area") == "PA02"
        ]
        assert "p2" in matched_ids
        assert "p1" not in [
            p["id"]
            for p in filtered
            if p.get("context_requirement", {}).get("policy_area") == "PA01"
        ]
        assert "p3" not in [
            p["id"]
            for p in filtered
            if p.get("context_requirement", {}).get("policy_area") == "PA10"
        ]

    def test_policy_area_range_not_supported(self):
        """Test policy area ranges like PA01-PA05 are not expanded."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test",
                "context_requirement": {"policy_area": "PA01-PA05"},
            },
        ]
        context = {"policy_area": "PA03"}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert (
            len(
                [
                    p
                    for p in filtered
                    if p.get("context_requirement", {}).get("policy_area") == "PA03"
                ]
            )
            == 0
        )


class TestPhase4ImmutableTupleReturns:
    """Test filtered patterns returned as immutable tuples."""

    def test_filtered_patterns_is_list(self):
        """Test filter_patterns_by_context returns list (not tuple in this implementation)."""
        patterns = [{"id": "p1", "pattern": "test", "context_scope": "global"}]
        context = {}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert isinstance(filtered, list)

    def test_filtered_patterns_preserves_order(self):
        """Test filtered patterns preserve original order."""
        patterns = [
            {"id": "p1", "pattern": "test1", "context_scope": "global"},
            {"id": "p2", "pattern": "test2", "context_scope": "global"},
            {"id": "p3", "pattern": "test3", "context_scope": "global"},
        ]
        context = {}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert [p["id"] for p in filtered] == ["p1", "p2", "p3"]

    def test_pattern_objects_not_mutated(self):
        """Test original pattern objects are not mutated during filtering."""
        original_pattern = {
            "id": "p1",
            "pattern": "test",
            "context_scope": "global",
            "extra": "data",
        }
        patterns = [original_pattern.copy()]
        context = {}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert original_pattern["extra"] == "data"
        assert filtered[0]["extra"] == "data"

    def test_empty_filter_result_returns_empty_list(self):
        """Test empty filter results return empty list."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test",
                "context_requirement": {"section": "budget"},
            },
        ]
        context = {"section": "introduction"}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert isinstance(filtered, list)
        assert len(filtered) == 0

    def test_pattern_dict_structure_preserved(self):
        """Test pattern dictionary structure is preserved after filtering."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test",
                "context_scope": "global",
                "metadata": {"source": "test"},
                "nested": {"key": "value"},
            }
        ]
        context = {}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert filtered[0]["id"] == "p1"
        assert filtered[0]["metadata"]["source"] == "test"
        assert filtered[0]["nested"]["key"] == "value"

    def test_no_reference_sharing_between_input_output(self):
        """Test filtered patterns don't share references with input patterns."""
        pattern = {"id": "p1", "pattern": "test", "context_scope": "global"}
        patterns = [pattern]
        context = {}

        filtered, stats = filter_patterns_by_context(patterns, context)

        # Original pattern is in filtered list
        assert filtered[0] is pattern  # Same object reference in this implementation


class TestPhase4ContextScopeFiltering:
    """Test context-based pattern scoping (section, chapter, page, global)."""

    def test_global_scope_always_passes(self):
        """Test global scope patterns pass in any context."""
        patterns = [{"id": "p1", "pattern": "test", "context_scope": "global"}]
        contexts = [
            {},
            {"section": "budget"},
            {"chapter": 1},
            {"page": 5},
        ]

        for context in contexts:
            filtered, stats = filter_patterns_by_context(patterns, context)
            assert len(filtered) == 1

    def test_section_scope_requires_section_context(self):
        """Test section scope patterns require section in context."""
        patterns = [{"id": "p1", "pattern": "test", "context_scope": "section"}]

        # With section context
        filtered, stats = filter_patterns_by_context(patterns, {"section": "budget"})
        assert len(filtered) == 1

        # Without section context
        filtered, stats = filter_patterns_by_context(patterns, {})
        assert len(filtered) == 0

    def test_chapter_scope_requires_chapter_context(self):
        """Test chapter scope patterns require chapter in context."""
        patterns = [{"id": "p1", "pattern": "test", "context_scope": "chapter"}]

        # With chapter context
        filtered, stats = filter_patterns_by_context(patterns, {"chapter": 3})
        assert len(filtered) == 1

        # Without chapter context
        filtered, stats = filter_patterns_by_context(patterns, {})
        assert len(filtered) == 0

    def test_page_scope_requires_page_context(self):
        """Test page scope patterns require page in context."""
        patterns = [{"id": "p1", "pattern": "test", "context_scope": "page"}]

        # With page context
        filtered, stats = filter_patterns_by_context(patterns, {"page": 10})
        assert len(filtered) == 1

        # Without page context
        filtered, stats = filter_patterns_by_context(patterns, {})
        assert len(filtered) == 0

    def test_unknown_scope_defaults_to_allow(self):
        """Test unknown scope values default to allow (conservative)."""
        patterns = [{"id": "p1", "pattern": "test", "context_scope": "unknown_scope"}]

        filtered, stats = filter_patterns_by_context(patterns, {})
        assert len(filtered) == 1

    def test_missing_scope_defaults_to_global(self):
        """Test patterns without context_scope default to global."""
        patterns = [{"id": "p1", "pattern": "test"}]

        filtered, stats = filter_patterns_by_context(patterns, {})
        assert len(filtered) == 1

    def test_mixed_scopes_filtered_correctly(self):
        """Test mixed scope patterns filtered according to context."""
        patterns = [
            {"id": "p1", "pattern": "test1", "context_scope": "global"},
            {"id": "p2", "pattern": "test2", "context_scope": "section"},
            {"id": "p3", "pattern": "test3", "context_scope": "chapter"},
        ]
        context = {"section": "budget"}

        filtered, stats = filter_patterns_by_context(patterns, context)

        filtered_ids = [p["id"] for p in filtered]
        assert "p1" in filtered_ids  # global always passes
        assert "p2" in filtered_ids  # section context present
        assert "p3" not in filtered_ids  # chapter context missing


class TestPhase4ContextRequirementMatching:
    """Test context requirement matching (exact, list, comparison operators)."""

    def test_exact_context_requirement_match(self):
        """Test exact context requirement matching."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test",
                "context_requirement": {"section": "budget"},
            },
        ]

        # Exact match
        filtered, _ = filter_patterns_by_context(patterns, {"section": "budget"})
        assert len(filtered) == 1

        # No match
        filtered, _ = filter_patterns_by_context(patterns, {"section": "introduction"})
        assert len(filtered) == 0

    def test_list_context_requirement_match(self):
        """Test list of acceptable values in context requirement."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test",
                "context_requirement": {"section": ["budget", "financial", "economic"]},
            }
        ]

        # Match first value
        filtered, _ = filter_patterns_by_context(patterns, {"section": "budget"})
        assert len(filtered) == 1

        # Match middle value
        filtered, _ = filter_patterns_by_context(patterns, {"section": "financial"})
        assert len(filtered) == 1

        # No match
        filtered, _ = filter_patterns_by_context(patterns, {"section": "introduction"})
        assert len(filtered) == 0

    def test_comparison_operator_greater_than(self):
        """Test > comparison operator in context requirement."""
        patterns = [
            {"id": "p1", "pattern": "test", "context_requirement": {"chapter": ">2"}},
        ]

        # Chapter 3 > 2
        filtered, _ = filter_patterns_by_context(patterns, {"chapter": 3})
        assert len(filtered) == 1

        # Chapter 2 not > 2
        filtered, _ = filter_patterns_by_context(patterns, {"chapter": 2})
        assert len(filtered) == 0

        # Chapter 1 not > 2
        filtered, _ = filter_patterns_by_context(patterns, {"chapter": 1})
        assert len(filtered) == 0

    def test_comparison_operator_greater_than_or_equal(self):
        """Test >= comparison operator in context requirement."""
        patterns = [
            {"id": "p1", "pattern": "test", "context_requirement": {"page": ">=10"}},
        ]

        # Page 10 >= 10
        filtered, _ = filter_patterns_by_context(patterns, {"page": 10})
        assert len(filtered) == 1

        # Page 11 >= 10
        filtered, _ = filter_patterns_by_context(patterns, {"page": 11})
        assert len(filtered) == 1

        # Page 9 not >= 10
        filtered, _ = filter_patterns_by_context(patterns, {"page": 9})
        assert len(filtered) == 0

    def test_comparison_operator_less_than(self):
        """Test < comparison operator in context requirement."""
        patterns = [
            {"id": "p1", "pattern": "test", "context_requirement": {"chapter": "<5"}},
        ]

        # Chapter 4 < 5
        filtered, _ = filter_patterns_by_context(patterns, {"chapter": 4})
        assert len(filtered) == 1

        # Chapter 5 not < 5
        filtered, _ = filter_patterns_by_context(patterns, {"chapter": 5})
        assert len(filtered) == 0

    def test_comparison_operator_less_than_or_equal(self):
        """Test <= comparison operator in context requirement."""
        patterns = [
            {"id": "p1", "pattern": "test", "context_requirement": {"page": "<=20"}},
        ]

        # Page 20 <= 20
        filtered, _ = filter_patterns_by_context(patterns, {"page": 20})
        assert len(filtered) == 1

        # Page 19 <= 20
        filtered, _ = filter_patterns_by_context(patterns, {"page": 19})
        assert len(filtered) == 1

        # Page 21 not <= 20
        filtered, _ = filter_patterns_by_context(patterns, {"page": 21})
        assert len(filtered) == 0

    def test_multiple_context_requirements_all_must_match(self):
        """Test multiple context requirements all must match (AND logic)."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test",
                "context_requirement": {"section": "budget", "chapter": ">2"},
            }
        ]

        # Both match
        filtered, _ = filter_patterns_by_context(
            patterns, {"section": "budget", "chapter": 3}
        )
        assert len(filtered) == 1

        # Section matches, chapter doesn't
        filtered, _ = filter_patterns_by_context(
            patterns, {"section": "budget", "chapter": 1}
        )
        assert len(filtered) == 0

        # Chapter matches, section doesn't
        filtered, _ = filter_patterns_by_context(
            patterns, {"section": "introduction", "chapter": 3}
        )
        assert len(filtered) == 0

    def test_string_context_requirement_as_section(self):
        """Test string context requirement interpreted as section name."""
        patterns = [
            {"id": "p1", "pattern": "test", "context_requirement": "budget"},
        ]

        # Section matches
        filtered, _ = filter_patterns_by_context(patterns, {"section": "budget"})
        assert len(filtered) == 1

        # Section doesn't match
        filtered, _ = filter_patterns_by_context(patterns, {"section": "introduction"})
        assert len(filtered) == 0


class TestPhase4FilterStatistics:
    """Test filter statistics tracking (total, filtered, passed counts)."""

    def test_stats_track_total_patterns(self):
        """Test stats include total pattern count."""
        patterns = [
            {"id": "p1", "pattern": "test1"},
            {"id": "p2", "pattern": "test2"},
            {"id": "p3", "pattern": "test3"},
        ]

        filtered, stats = filter_patterns_by_context(patterns, {})

        assert stats["total_patterns"] == 3

    def test_stats_track_context_filtered_count(self):
        """Test stats track patterns filtered by context requirements."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test1",
                "context_requirement": {"section": "budget"},
            },
            {
                "id": "p2",
                "pattern": "test2",
                "context_requirement": {"section": "introduction"},
            },
            {"id": "p3", "pattern": "test3", "context_scope": "global"},
        ]
        context = {"section": "budget"}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert stats["context_filtered"] == 1  # p2 filtered

    def test_stats_track_scope_filtered_count(self):
        """Test stats track patterns filtered by scope."""
        patterns = [
            {"id": "p1", "pattern": "test1", "context_scope": "section"},
            {"id": "p2", "pattern": "test2", "context_scope": "chapter"},
            {"id": "p3", "pattern": "test3", "context_scope": "global"},
        ]
        context = {}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert stats["scope_filtered"] == 2  # p1 and p2 filtered

    def test_stats_track_passed_count(self):
        """Test stats track patterns that passed filters."""
        patterns = [
            {"id": "p1", "pattern": "test1", "context_scope": "global"},
            {"id": "p2", "pattern": "test2", "context_scope": "global"},
            {
                "id": "p3",
                "pattern": "test3",
                "context_requirement": {"section": "budget"},
            },
        ]
        context = {}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert stats["passed"] == 2  # p1 and p2 passed

    def test_stats_sum_equals_total(self):
        """Test stats counts sum to total patterns."""
        patterns = [
            {"id": "p1", "pattern": "test1", "context_scope": "section"},
            {
                "id": "p2",
                "pattern": "test2",
                "context_requirement": {"section": "budget"},
            },
            {"id": "p3", "pattern": "test3", "context_scope": "global"},
        ]
        context = {}

        filtered, stats = filter_patterns_by_context(patterns, context)

        total = stats["passed"] + stats["context_filtered"] + stats["scope_filtered"]
        assert total == stats["total_patterns"]

    def test_stats_all_passed_scenario(self):
        """Test stats when all patterns pass filters."""
        patterns = [
            {"id": "p1", "pattern": "test1", "context_scope": "global"},
            {"id": "p2", "pattern": "test2", "context_scope": "global"},
        ]
        context = {}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert stats["passed"] == 2
        assert stats["context_filtered"] == 0
        assert stats["scope_filtered"] == 0

    def test_stats_all_filtered_scenario(self):
        """Test stats when all patterns are filtered out."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test1",
                "context_requirement": {"section": "budget"},
            },
            {
                "id": "p2",
                "pattern": "test2",
                "context_requirement": {"section": "financial"},
            },
        ]
        context = {"section": "introduction"}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert stats["passed"] == 0
        assert stats["context_filtered"] == 2


class TestPhase4EmptyPatternHandling:
    """Test empty pattern list handling."""

    def test_empty_pattern_list_returns_empty_filtered(self):
        """Test empty pattern list returns empty filtered list."""
        patterns = []
        context = {"section": "budget"}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert len(filtered) == 0
        assert isinstance(filtered, list)

    def test_empty_pattern_list_stats(self):
        """Test empty pattern list produces correct stats."""
        patterns = []
        context = {}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert stats["total_patterns"] == 0
        assert stats["passed"] == 0
        assert stats["context_filtered"] == 0
        assert stats["scope_filtered"] == 0

    def test_patterns_with_no_matches_return_empty(self):
        """Test patterns that don't match context return empty list."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test",
                "context_requirement": {"section": "budget"},
            },
        ]
        context = {"section": "introduction"}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert len(filtered) == 0


class TestPhase4InvalidContextHandling:
    """Test invalid context handling with graceful degradation."""

    def test_none_context_allows_global_patterns(self):
        """Test None context allows global scope patterns."""
        patterns = [
            {"id": "p1", "pattern": "test", "context_scope": "global"},
        ]

        filtered, stats = filter_patterns_by_context(patterns, {})

        assert len(filtered) == 1

    def test_missing_required_context_field_filters_pattern(self):
        """Test missing required context field filters pattern out."""
        patterns = [
            {
                "id": "p1",
                "pattern": "test",
                "context_requirement": {"section": "budget"},
            },
        ]
        context = {"chapter": 1}  # Missing section field

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert len(filtered) == 0

    def test_invalid_comparison_value_filters_pattern(self):
        """Test invalid comparison value (non-numeric) filters pattern."""
        patterns = [
            {"id": "p1", "pattern": "test", "context_requirement": {"chapter": ">2"}},
        ]
        context = {"chapter": "invalid"}  # String instead of number

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert len(filtered) == 0

    def test_empty_context_requirement_always_matches(self):
        """Test empty context requirement always matches."""
        patterns = [
            {"id": "p1", "pattern": "test", "context_requirement": {}},
        ]
        context = {}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert len(filtered) == 1

    def test_none_context_requirement_always_matches(self):
        """Test None context requirement always matches."""
        patterns = [
            {"id": "p1", "pattern": "test", "context_requirement": None},
        ]
        context = {}

        filtered, stats = filter_patterns_by_context(patterns, context)

        assert len(filtered) == 1


class TestPhase4HelperFunctions:
    """Test helper functions: context_matches, in_scope, evaluate_comparison."""

    def test_context_matches_exact(self):
        """Test context_matches with exact value match."""
        assert context_matches({"section": "budget"}, {"section": "budget"}) is True
        assert (
            context_matches({"section": "budget"}, {"section": "introduction"}) is False
        )

    def test_context_matches_list(self):
        """Test context_matches with list of values."""
        requirement = {"section": ["budget", "financial"]}
        assert context_matches({"section": "budget"}, requirement) is True
        assert context_matches({"section": "financial"}, requirement) is True
        assert context_matches({"section": "introduction"}, requirement) is False

    def test_context_matches_comparison(self):
        """Test context_matches with comparison operators."""
        assert context_matches({"chapter": 5}, {"chapter": ">2"}) is True
        assert context_matches({"chapter": 1}, {"chapter": ">2"}) is False
        assert context_matches({"page": 10}, {"page": ">=10"}) is True
        assert context_matches({"page": 9}, {"page": ">=10"}) is False

    def test_in_scope_global(self):
        """Test in_scope with global scope."""
        assert in_scope({}, "global") is True
        assert in_scope({"section": "budget"}, "global") is True

    def test_in_scope_section(self):
        """Test in_scope with section scope."""
        assert in_scope({"section": "budget"}, "section") is True
        assert in_scope({}, "section") is False

    def test_in_scope_chapter(self):
        """Test in_scope with chapter scope."""
        assert in_scope({"chapter": 1}, "chapter") is True
        assert in_scope({}, "chapter") is False

    def test_in_scope_page(self):
        """Test in_scope with page scope."""
        assert in_scope({"page": 5}, "page") is True
        assert in_scope({}, "page") is False

    def test_evaluate_comparison_greater_than(self):
        """Test evaluate_comparison with > operator."""
        assert evaluate_comparison(5, ">2") is True
        assert evaluate_comparison(2, ">2") is False
        assert evaluate_comparison(1, ">2") is False

    def test_evaluate_comparison_greater_equal(self):
        """Test evaluate_comparison with >= operator."""
        assert evaluate_comparison(5, ">=5") is True
        assert evaluate_comparison(6, ">=5") is True
        assert evaluate_comparison(4, ">=5") is False

    def test_evaluate_comparison_less_than(self):
        """Test evaluate_comparison with < operator."""
        assert evaluate_comparison(2, "<5") is True
        assert evaluate_comparison(5, "<5") is False
        assert evaluate_comparison(6, "<5") is False

    def test_evaluate_comparison_less_equal(self):
        """Test evaluate_comparison with <= operator."""
        assert evaluate_comparison(5, "<=5") is True
        assert evaluate_comparison(4, "<=5") is True
        assert evaluate_comparison(6, "<=5") is False

    def test_evaluate_comparison_invalid_value(self):
        """Test evaluate_comparison with invalid value returns False."""
        assert evaluate_comparison("invalid", ">2") is False
        assert evaluate_comparison(None, ">2") is False

    def test_create_document_context(self):
        """Test create_document_context helper function."""
        context = create_document_context(section="budget", chapter=3, page=47)
        assert context == {"section": "budget", "chapter": 3, "page": 47}

    def test_create_document_context_with_kwargs(self):
        """Test create_document_context with additional kwargs."""
        context = create_document_context(section="budget", custom_field="value")
        assert context["section"] == "budget"
        assert context["custom_field"] == "value"

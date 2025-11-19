#!/usr/bin/env python3
"""
GOLD-CANARIO Comprehensive Tests: Micro Reporting - Provenance Auditor
=======================================================================

Tests for ProvenanceAuditor (QMCM Integrity Check) including:
- QMCM correspondence validation
- Orphan node detection
- Schema compliance verification
- Latency anomaly detection
- Contribution weight calculation
- Severity assessment
- Narrative generation
"""

import time

import pytest

from saaaaaa.analysis.micro_prompts import (
    AuditResult,
    ProvenanceAuditor,
    ProvenanceDAG,
    ProvenanceNode,
    QMCMRecord,
)

class TestProvenanceAuditorBasicFunctionality:
    """Test basic functionality of ProvenanceAuditor"""

    def test_auditor_initialization_defaults(self):
        """Test auditor initializes with default values"""
        auditor = ProvenanceAuditor()
        assert auditor.p95_threshold == 1000.0
        assert auditor.method_contracts == {}

    def test_auditor_initialization_custom(self):
        """Test auditor initializes with custom values"""
        contracts = {"method1": {"field1": "string"}}
        auditor = ProvenanceAuditor(p95_latency_threshold=500.0, method_contracts=contracts)
        assert auditor.p95_threshold == 500.0
        assert auditor.method_contracts == contracts

    def test_empty_dag_audit(self):
        """Test audit with empty DAG"""
        auditor = ProvenanceAuditor()
        dag = ProvenanceDAG(nodes={}, edges=[])
        registry = {}

        result = auditor.audit(None, registry, dag)

        assert isinstance(result, AuditResult)
        assert result.severity == 'LOW'
        assert len(result.missing_qmcm) == 0
        assert len(result.orphan_nodes) == 0

class TestQMCMCorrespondence:
    """Test QMCM correspondence validation"""

    def test_perfect_correspondence(self):
        """Test DAG with perfect QMCM correspondence"""
        auditor = ProvenanceAuditor()

        # Create QMCM records
        registry = {
            "record1": QMCMRecord(
                question_id="Q1",
                method_fqn="module.method1",
                contribution_weight=1.0,
                timestamp=time.time(),
                output_schema={"result": "string"}
            )
        }

        # Create DAG with method node
        nodes = {
            "node1": ProvenanceNode(
                node_id="node1",
                node_type="method",
                parent_ids=["input1"],
                qmcm_record_id="record1"
            ),
            "input1": ProvenanceNode(
                node_id="input1",
                node_type="input",
                parent_ids=[]
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[("input1", "node1")])

        result = auditor.audit(None, registry, dag)

        assert len(result.missing_qmcm) == 0
        assert result.severity == 'LOW'

    def test_missing_qmcm_record(self):
        """Test detection of missing QMCM records"""
        auditor = ProvenanceAuditor()

        registry = {}

        # Method node without QMCM record
        nodes = {
            "node1": ProvenanceNode(
                node_id="node1",
                node_type="method",
                parent_ids=["input1"],
                qmcm_record_id=None
            ),
            "input1": ProvenanceNode(
                node_id="input1",
                node_type="input",
                parent_ids=[]
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[("input1", "node1")])

        result = auditor.audit(None, registry, dag)

        assert "node1" in result.missing_qmcm
        assert result.severity in ['MEDIUM', 'HIGH']

    def test_orphaned_qmcm_record(self):
        """Test detection of QMCM records not in registry"""
        auditor = ProvenanceAuditor()

        registry = {}  # Empty registry

        nodes = {
            "node1": ProvenanceNode(
                node_id="node1",
                node_type="method",
                parent_ids=["input1"],
                qmcm_record_id="nonexistent"
            ),
            "input1": ProvenanceNode(
                node_id="input1",
                node_type="input",
                parent_ids=[]
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[("input1", "node1")])

        result = auditor.audit(None, registry, dag)

        assert "node1" in result.missing_qmcm

class TestOrphanNodeDetection:
    """Test orphan node detection"""

    def test_no_orphan_nodes(self):
        """Test DAG without orphan nodes"""
        auditor = ProvenanceAuditor()

        nodes = {
            "input1": ProvenanceNode(
                node_id="input1",
                node_type="input",
                parent_ids=[]
            ),
            "method1": ProvenanceNode(
                node_id="method1",
                node_type="method",
                parent_ids=["input1"]
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[("input1", "method1")])

        result = auditor.audit(None, {}, dag)

        assert len(result.orphan_nodes) == 0

    def test_orphan_method_node(self):
        """Test detection of orphan method node"""
        auditor = ProvenanceAuditor()

        nodes = {
            "input1": ProvenanceNode(
                node_id="input1",
                node_type="input",
                parent_ids=[]
            ),
            "orphan_method": ProvenanceNode(
                node_id="orphan_method",
                node_type="method",
                parent_ids=[]  # No parents
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[])

        result = auditor.audit(None, {}, dag)

        assert "orphan_method" in result.orphan_nodes
        assert result.severity in ['MEDIUM', 'HIGH']

    def test_orphan_output_node(self):
        """Test detection of orphan output node"""
        auditor = ProvenanceAuditor()

        nodes = {
            "input1": ProvenanceNode(
                node_id="input1",
                node_type="input",
                parent_ids=[]
            ),
            "orphan_output": ProvenanceNode(
                node_id="orphan_output",
                node_type="output",
                parent_ids=[]
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[])

        result = auditor.audit(None, {}, dag)

        assert "orphan_output" in result.orphan_nodes

class TestLatencyAnomalies:
    """Test latency anomaly detection"""

    def test_no_latency_anomalies(self):
        """Test DAG with normal latencies"""
        auditor = ProvenanceAuditor(p95_latency_threshold=1000.0)

        nodes = {
            "node1": ProvenanceNode(
                node_id="node1",
                node_type="method",
                parent_ids=["input1"],
                timing=500.0
            ),
            "input1": ProvenanceNode(
                node_id="input1",
                node_type="input",
                parent_ids=[],
                timing=100.0
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[("input1", "node1")])

        result = auditor.audit(None, {}, dag)

        assert len(result.latency_anomalies) == 0

    def test_single_latency_anomaly(self):
        """Test detection of single latency anomaly"""
        auditor = ProvenanceAuditor(p95_latency_threshold=1000.0)

        nodes = {
            "slow_node": ProvenanceNode(
                node_id="slow_node",
                node_type="method",
                parent_ids=["input1"],
                timing=1500.0  # Exceeds threshold
            ),
            "input1": ProvenanceNode(
                node_id="input1",
                node_type="input",
                parent_ids=[],
                timing=100.0
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[("input1", "slow_node")])

        result = auditor.audit(None, {}, dag)

        assert len(result.latency_anomalies) == 1
        anomaly = result.latency_anomalies[0]
        assert anomaly['node_id'] == "slow_node"
        assert anomaly['timing'] == 1500.0
        assert anomaly['threshold'] == 1000.0
        assert anomaly['excess'] == 500.0

    def test_multiple_latency_anomalies(self):
        """Test detection of multiple latency anomalies"""
        auditor = ProvenanceAuditor(p95_latency_threshold=500.0)

        nodes = {
            "slow1": ProvenanceNode(
                node_id="slow1",
                node_type="method",
                parent_ids=["input1"],
                timing=800.0
            ),
            "slow2": ProvenanceNode(
                node_id="slow2",
                node_type="method",
                parent_ids=["input1"],
                timing=1000.0
            ),
            "input1": ProvenanceNode(
                node_id="input1",
                node_type="input",
                parent_ids=[],
                timing=50.0
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[("input1", "slow1"), ("input1", "slow2")])

        result = auditor.audit(None, {}, dag)

        assert len(result.latency_anomalies) == 2

class TestSchemaCompliance:
    """Test schema compliance verification"""

    def test_schema_compliance_pass(self):
        """Test schema compliance with matching schemas"""
        contracts = {
            "module.method1": {"result": "string", "count": "int"}
        }
        auditor = ProvenanceAuditor(method_contracts=contracts)

        registry = {
            "record1": QMCMRecord(
                question_id="Q1",
                method_fqn="module.method1",
                contribution_weight=1.0,
                timestamp=time.time(),
                output_schema={"result": "string", "count": "int"}
            )
        }

        nodes = {
            "node1": ProvenanceNode(
                node_id="node1",
                node_type="method",
                parent_ids=["input1"],
                qmcm_record_id="record1"
            ),
            "input1": ProvenanceNode(
                node_id="input1",
                node_type="input",
                parent_ids=[]
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[("input1", "node1")])

        result = auditor.audit(None, registry, dag)

        assert len(result.schema_mismatches) == 0

    def test_schema_compliance_fail_missing_field(self):
        """Test schema compliance with missing field"""
        contracts = {
            "module.method1": {"result": "string", "count": "int"}
        }
        auditor = ProvenanceAuditor(method_contracts=contracts)

        registry = {
            "record1": QMCMRecord(
                question_id="Q1",
                method_fqn="module.method1",
                contribution_weight=1.0,
                timestamp=time.time(),
                output_schema={"result": "string"}  # Missing 'count'
            )
        }

        nodes = {
            "node1": ProvenanceNode(
                node_id="node1",
                node_type="method",
                parent_ids=["input1"],
                qmcm_record_id="record1"
            ),
            "input1": ProvenanceNode(
                node_id="input1",
                node_type="input",
                parent_ids=[]
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[("input1", "node1")])

        result = auditor.audit(None, registry, dag)

        assert len(result.schema_mismatches) == 1
        mismatch = result.schema_mismatches[0]
        assert mismatch['node_id'] == "node1"
        assert mismatch['method'] == "module.method1"

class TestContributionWeights:
    """Test contribution weight calculation"""

    def test_single_method_contribution(self):
        """Test contribution weight for single method"""
        auditor = ProvenanceAuditor()

        registry = {
            "record1": QMCMRecord(
                question_id="Q1",
                method_fqn="module.method1",
                contribution_weight=0.75,
                timestamp=time.time(),
                output_schema={}
            )
        }

        result = auditor.audit(None, registry, ProvenanceDAG(nodes={}, edges=[]))

        assert "module.method1" in result.contribution_weights
        assert result.contribution_weights["module.method1"] == 0.75

    def test_multiple_methods_contribution(self):
        """Test contribution weights for multiple methods"""
        auditor = ProvenanceAuditor()

        registry = {
            "record1": QMCMRecord(
                question_id="Q1",
                method_fqn="module.method1",
                contribution_weight=0.5,
                timestamp=time.time(),
                output_schema={}
            ),
            "record2": QMCMRecord(
                question_id="Q1",
                method_fqn="module.method2",
                contribution_weight=0.3,
                timestamp=time.time(),
                output_schema={}
            ),
            "record3": QMCMRecord(
                question_id="Q1",
                method_fqn="module.method1",  # Same method as record1
                contribution_weight=0.2,
                timestamp=time.time(),
                output_schema={}
            )
        }

        result = auditor.audit(None, registry, ProvenanceDAG(nodes={}, edges=[]))

        # method1 should have combined weight of 0.5 + 0.2 = 0.7
        assert result.contribution_weights["module.method1"] == 0.7
        assert result.contribution_weights["module.method2"] == 0.3

class TestSeverityAssessment:
    """Test severity assessment logic"""

    def test_severity_low_no_issues(self):
        """Test LOW severity with no issues"""
        auditor = ProvenanceAuditor()
        dag = ProvenanceDAG(nodes={}, edges=[])

        result = auditor.audit(None, {}, dag)

        assert result.severity == 'LOW'

    def test_severity_medium_few_issues(self):
        """Test MEDIUM severity with few issues"""
        auditor = ProvenanceAuditor()

        nodes = {
            "orphan1": ProvenanceNode(
                node_id="orphan1",
                node_type="method",
                parent_ids=[]
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[])

        result = auditor.audit(None, {}, dag)

        assert result.severity in ['MEDIUM', 'HIGH']

    def test_severity_high_multiple_issues(self):
        """Test HIGH severity with multiple issues"""
        auditor = ProvenanceAuditor(p95_latency_threshold=100.0)

        nodes = {
            "orphan1": ProvenanceNode(
                node_id="orphan1",
                node_type="method",
                parent_ids=[],
                timing=200.0
            ),
            "orphan2": ProvenanceNode(
                node_id="orphan2",
                node_type="method",
                parent_ids=[],
                timing=300.0
            ),
            "orphan3": ProvenanceNode(
                node_id="orphan3",
                node_type="output",
                parent_ids=[]
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[])

        result = auditor.audit(None, {}, dag)

        assert result.severity in ['HIGH', 'CRITICAL']

    def test_severity_critical_many_issues(self):
        """Test CRITICAL severity with many issues"""
        auditor = ProvenanceAuditor(p95_latency_threshold=50.0)

        # Create 10 orphan nodes with latency issues
        nodes = {}
        for i in range(10):
            nodes[f"orphan{i}"] = ProvenanceNode(
                node_id=f"orphan{i}",
                node_type="method",
                parent_ids=[],
                timing=100.0 + i * 10
            )

        dag = ProvenanceDAG(nodes=nodes, edges=[])

        result = auditor.audit(None, {}, dag)

        assert result.severity == 'CRITICAL'

class TestNarrativeGeneration:
    """Test narrative generation"""

    def test_narrative_all_clear(self):
        """Test narrative with no issues"""
        auditor = ProvenanceAuditor()
        dag = ProvenanceDAG(nodes={}, edges=[])

        result = auditor.audit(None, {}, dag)

        assert "LOW severity" in result.narrative
        assert "critical integrity checks passed" in result.narrative

    def test_narrative_with_issues(self):
        """Test narrative with various issues"""
        auditor = ProvenanceAuditor(p95_latency_threshold=100.0)

        nodes = {
            "orphan1": ProvenanceNode(
                node_id="orphan1",
                node_type="method",
                parent_ids=[],
                timing=200.0
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[])

        result = auditor.audit(None, {}, dag)

        assert "orphan nodes" in result.narrative.lower() or "orphan" in result.narrative.lower()
        assert "latency" in result.narrative.lower() or "anomal" in result.narrative.lower()

    def test_narrative_critical_severity(self):
        """Test narrative with critical severity"""
        auditor = ProvenanceAuditor(p95_latency_threshold=10.0)

        nodes = {}
        for i in range(10):
            nodes[f"orphan{i}"] = ProvenanceNode(
                node_id=f"orphan{i}",
                node_type="method",
                parent_ids=[],
                timing=100.0
            )

        dag = ProvenanceDAG(nodes=nodes, edges=[])

        result = auditor.audit(None, {}, dag)

        assert "CRITICAL" in result.narrative
        assert "remediation" in result.narrative.lower() or "governance" in result.narrative.lower()

class TestProvenanceDAGHelpers:
    """Test ProvenanceDAG helper methods"""

    def test_get_root_nodes(self):
        """Test getting root nodes"""
        nodes = {
            "root1": ProvenanceNode(
                node_id="root1",
                node_type="input",
                parent_ids=[]
            ),
            "root2": ProvenanceNode(
                node_id="root2",
                node_type="input",
                parent_ids=[]
            ),
            "child": ProvenanceNode(
                node_id="child",
                node_type="method",
                parent_ids=["root1"]
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[("root1", "child")])

        roots = dag.get_root_nodes()

        assert len(roots) == 2
        assert "root1" in roots
        assert "root2" in roots
        assert "child" not in roots

    def test_get_orphan_nodes(self):
        """Test getting orphan nodes"""
        nodes = {
            "input1": ProvenanceNode(
                node_id="input1",
                node_type="input",
                parent_ids=[]
            ),
            "orphan_method": ProvenanceNode(
                node_id="orphan_method",
                node_type="method",
                parent_ids=[]
            ),
            "orphan_output": ProvenanceNode(
                node_id="orphan_output",
                node_type="output",
                parent_ids=[]
            )
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[])

        orphans = dag.get_orphan_nodes()

        assert len(orphans) == 2
        assert "orphan_method" in orphans
        assert "orphan_output" in orphans
        assert "input1" not in orphans

class TestJSONExport:
    """Test JSON export functionality"""

    def test_to_json_export(self):
        """Test exporting audit result to JSON"""
        auditor = ProvenanceAuditor()
        dag = ProvenanceDAG(nodes={}, edges=[])

        result = auditor.audit(None, {}, dag)
        json_output = auditor.to_json(result)

        assert isinstance(json_output, dict)
        assert 'missing_qmcm' in json_output
        assert 'orphan_nodes' in json_output
        assert 'schema_mismatches' in json_output
        assert 'latency_anomalies' in json_output
        assert 'contribution_weights' in json_output
        assert 'severity' in json_output
        assert 'narrative' in json_output
        assert 'timestamp' in json_output

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

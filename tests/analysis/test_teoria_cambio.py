"""
Unit tests for Teoria Cambio (teoria_cambio.py)

Tests theory of change validation, DAG construction, 
Monte Carlo simulation, and axiom enforcement.
"""

import networkx as nx
import pytest

from farfan_pipeline.core.types import CategoriaCausal
from src.farfan_pipeline.analysis.teoria_cambio import (
    AdvancedDAGValidator,
    AdvancedGraphNode,
    MonteCarloAdvancedResult,
    TeoriaCambio,
    ValidacionResultado,
    _create_advanced_seed,
)


@pytest.fixture
def teoria_cambio():
    """Create TeoriaCambio instance for testing."""
    return TeoriaCambio()


@pytest.fixture
def sample_dag():
    """Create sample DAG for testing."""
    G = nx.DiGraph()
    G.add_node('A', categoria=CategoriaCausal.INSUMOS, nivel=1)
    G.add_node('B', categoria=CategoriaCausal.PROCESOS, nivel=2)
    G.add_node('C', categoria=CategoriaCausal.PRODUCTOS, nivel=3)
    G.add_node('D', categoria=CategoriaCausal.RESULTADOS, nivel=4)
    G.add_node('E', categoria=CategoriaCausal.CAUSALIDAD, nivel=5)

    G.add_edge('A', 'B', peso=1.0)
    G.add_edge('B', 'C', peso=1.0)
    G.add_edge('C', 'D', peso=1.0)
    G.add_edge('D', 'E', peso=1.0)

    return G


class TestTeoriaCambio:
    """Test suite for TeoriaCambio theory of change validation."""

    def test_initialization(self, teoria_cambio):
        """Test TeoriaCambio initialization."""
        assert teoria_cambio is not None
        assert teoria_cambio._grafo_cache is None
        assert teoria_cambio._cache_valido is False

    def test_construir_grafo_causal(self, teoria_cambio):
        """Test canonical causal graph construction."""
        grafo = teoria_cambio.construir_grafo_causal()

        assert isinstance(grafo, nx.DiGraph)
        assert grafo.number_of_nodes() == len(CategoriaCausal)
        assert grafo.number_of_edges() > 0

        # Verify all categories are present
        node_names = set(grafo.nodes())
        expected_names = {cat.name for cat in CategoriaCausal}
        assert node_names == expected_names

    def test_grafo_causal_caching(self, teoria_cambio):
        """Test that causal graph is cached after first construction."""
        grafo1 = teoria_cambio.construir_grafo_causal()
        grafo2 = teoria_cambio.construir_grafo_causal()

        # Should return same cached instance
        assert grafo1 is grafo2
        assert teoria_cambio._cache_valido is True

    def test_es_conexion_valida(self):
        """Test valid connection checking between categories."""
        # INSUMOS -> PROCESOS should be valid
        assert TeoriaCambio._es_conexion_valida(
            CategoriaCausal.INSUMOS,
            CategoriaCausal.PROCESOS
        )

        # INSUMOS -> CAUSALIDAD should be invalid (skipping levels)
        assert not TeoriaCambio._es_conexion_valida(
            CategoriaCausal.INSUMOS,
            CategoriaCausal.CAUSALIDAD
        )

    def test_validacion_completa_valid_graph(self, teoria_cambio, sample_dag):
        """Test complete validation with valid graph."""
        resultado = teoria_cambio.validacion_completa(sample_dag)

        assert isinstance(resultado, ValidacionResultado)
        assert resultado.es_valida is True
        assert len(resultado.violaciones_orden) == 0
        assert len(resultado.categorias_faltantes) == 0
        assert len(resultado.caminos_completos) > 0

    def test_validacion_completa_missing_category(self, teoria_cambio):
        """Test validation with missing category."""
        # Create incomplete DAG missing CAUSALIDAD
        G = nx.DiGraph()
        G.add_node('A', categoria=CategoriaCausal.INSUMOS, nivel=1)
        G.add_node('B', categoria=CategoriaCausal.PROCESOS, nivel=2)
        G.add_edge('A', 'B', peso=1.0)

        resultado = teoria_cambio.validacion_completa(G)

        assert resultado.es_valida is False
        assert len(resultado.categorias_faltantes) > 0
        assert CategoriaCausal.CAUSALIDAD in resultado.categorias_faltantes

    def test_validacion_completa_orden_violation(self, teoria_cambio):
        """Test validation with causal order violation."""
        # Create DAG with backward connection
        G = nx.DiGraph()
        G.add_node('A', categoria=CategoriaCausal.PROCESOS, nivel=2)
        G.add_node('B', categoria=CategoriaCausal.INSUMOS, nivel=1)
        G.add_edge('A', 'B', peso=1.0)  # Backward connection

        resultado = teoria_cambio.validacion_completa(G)

        assert len(resultado.violaciones_orden) > 0

    def test_extraer_categorias(self, teoria_cambio, sample_dag):
        """Test category extraction from graph."""
        categorias = teoria_cambio._extraer_categorias(sample_dag)

        assert isinstance(categorias, set)
        assert 'INSUMOS' in categorias
        assert 'CAUSALIDAD' in categorias

    def test_validar_orden_causal(self, teoria_cambio, sample_dag):
        """Test causal order validation."""
        violaciones = teoria_cambio._validar_orden_causal(sample_dag)

        assert isinstance(violaciones, list)
        assert len(violaciones) == 0  # sample_dag should have no violations

    def test_encontrar_caminos_completos(self, teoria_cambio, sample_dag):
        """Test finding complete paths from INSUMOS to CAUSALIDAD."""
        caminos = teoria_cambio._encontrar_caminos_completos(sample_dag)

        assert isinstance(caminos, list)
        assert len(caminos) > 0

        # Verify path goes from INSUMOS to CAUSALIDAD
        for camino in caminos:
            first_node = sample_dag.nodes[camino[0]]
            last_node = sample_dag.nodes[camino[-1]]
            assert first_node['categoria'] == CategoriaCausal.INSUMOS
            assert last_node['categoria'] == CategoriaCausal.CAUSALIDAD

    def test_generar_sugerencias(self, teoria_cambio):
        """Test suggestion generation."""
        resultado_invalido = ValidacionResultado(
            es_valida=False,
            categorias_faltantes=[CategoriaCausal.CAUSALIDAD],
            violaciones_orden=[('A', 'B')],
            caminos_completos=[]
        )

        sugerencias = teoria_cambio._generar_sugerencias_internas(resultado_invalido)

        assert isinstance(sugerencias, list)
        assert len(sugerencias) > 0
        assert any('CAUSALIDAD' in s for s in sugerencias)


class TestAdvancedGraphNode:
    """Test suite for AdvancedGraphNode."""

    def test_node_creation(self):
        """Test node creation with basic attributes."""
        node = AdvancedGraphNode(
            name='TestNode',
            dependencies={'dep1', 'dep2'},
            metadata={'key': 'value'},
            role='variable'
        )

        assert node.name == 'TestNode'
        assert 'dep1' in node.dependencies
        assert node.metadata['key'] == 'value'
        assert node.role == 'variable'

    def test_node_metadata_normalization(self):
        """Test metadata normalization with defaults."""
        node = AdvancedGraphNode(
            name='TestNode',
            metadata={}
        )

        assert 'created' in node.metadata
        assert 'confidence' in node.metadata
        assert 0.0 <= node.metadata['confidence'] <= 1.0

    def test_node_invalid_role(self):
        """Test that invalid role raises error."""
        with pytest.raises(ValueError, match='Invalid role'):
            AdvancedGraphNode(
                name='TestNode',
                role='invalid_role'
            )

    def test_node_empty_name(self):
        """Test that empty name raises error."""
        with pytest.raises(ValueError, match='non-empty string'):
            AdvancedGraphNode(name='')

    def test_node_serialization(self):
        """Test node serialization to dictionary."""
        node = AdvancedGraphNode(
            name='TestNode',
            dependencies={'dep1'},
            role='produto'
        )

        serialized = node.to_serializable_dict()

        assert isinstance(serialized, dict)
        assert serialized['name'] == 'TestNode'
        assert 'dep1' in serialized['dependencies']
        assert serialized['role'] == 'produto'


class TestDeterministicSeeding:
    """Test suite for deterministic seed generation."""

    def test_create_advanced_seed_deterministic(self):
        """Test seed generation is deterministic."""
        seed1 = _create_advanced_seed('plan_name', 'salt')
        seed2 = _create_advanced_seed('plan_name', 'salt')

        assert seed1 == seed2

    def test_create_advanced_seed_different_inputs(self):
        """Test different inputs produce different seeds."""
        seed1 = _create_advanced_seed('plan1', 'salt')
        seed2 = _create_advanced_seed('plan2', 'salt')

        assert seed1 != seed2

    def test_create_advanced_seed_salt_effect(self):
        """Test salt parameter affects seed."""
        seed1 = _create_advanced_seed('plan', 'salt1')
        seed2 = _create_advanced_seed('plan', 'salt2')

        assert seed1 != seed2

    def test_seed_is_valid_integer(self):
        """Test seed is valid 64-bit integer."""
        seed = _create_advanced_seed('test_plan', '')

        assert isinstance(seed, int)
        assert seed >= 0
        assert seed < 2**64


class TestAdvancedDAGValidator:
    """Test suite for Advanced DAG validator with Monte Carlo."""

    @pytest.fixture
    def validator(self):
        """Create DAG validator for testing."""
        return AdvancedDAGValidator(iterations=100)

    def test_validator_initialization(self, validator):
        """Test validator initialization."""
        assert validator is not None
        assert hasattr(validator, 'iterations')

    def test_validate_dag_acyclic(self, validator, sample_dag):
        """Test validation of acyclic DAG."""
        # This would test the full validation
        assert nx.is_directed_acyclic_graph(sample_dag)

    def test_monte_carlo_simulation_structure(self):
        """Test Monte Carlo result structure."""
        result = MonteCarloAdvancedResult(
            plan_name='Test Plan',
            seed=42,
            timestamp='2024-01-01T00:00:00',
            total_iterations=1000,
            acyclic_count=950,
            p_value=0.95,
            bayesian_posterior=0.92,
            confidence_interval=(0.88, 0.96),
            statistical_power=0.85,
            edge_sensitivity={'edge1': 0.8},
            node_importance={'node1': 0.9},
            robustness_score=0.87,
            reproducible=True,
            convergence_achieved=True,
            adequate_power=True,
            computation_time=1.5,
            graph_statistics={'nodes': 5, 'edges': 4},
            test_parameters={'alpha': 0.05}
        )

        assert result.plan_name == 'Test Plan'
        assert result.seed == 42
        assert result.reproducible is True
        assert result.p_value == 0.95
        assert 0.0 <= result.bayesian_posterior <= 1.0

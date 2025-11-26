import matplotlib.pyplot as plt
import numpy as np
import argparse
import os

# AtroZ Dashboard Color Palette
colors = {
    'bg': '#0A0A0A',
    'ink': '#E5E7EB',
    'red': '#C41E3A',
    'blue': '#00D4FF',
    'green': '#39FF14',
    'copper': '#B2642E',
    'copper_oxide': '#17A589'
}

plt.rcParams['figure.facecolor'] = colors['bg']
plt.rcParams['axes.facecolor'] = colors['bg']
plt.rcParams['text.color'] = colors['ink']
plt.rcParams['axes.labelcolor'] = colors['ink']
plt.rcParams['xtick.color'] = colors['ink']
plt.rcParams['ytick.color'] = colors['ink']
plt.rcParams['axes.edgecolor'] = colors['copper']
plt.rcParams['font.family'] = 'JetBrains Mono'

def get_text(lang, key):
    """Gets the text for the given language and key."""
    text = {
        'en': {
            'control_flow_title': 'Control-Flow Graph',
            'input_config': 'Input config',
            'schema_validation': 'Schema & path validation',
            'load_questionnaire': 'Load canonical questionnaire',
            'derive_settings': 'Derive AggregationSettings',
            'enforce_graph': 'Enforce phase graph + dependencies',
            'emit_config': 'Emit validated config',
            'reject_run': 'Reject run',
            'fail': 'fail',
            'hash_mismatch': 'hash mismatch',
            'data_flow_title': 'Data-Flow Graph',
            'config_raw': 'ConfigRaw',
            'schema_validator': 'SchemaValidator',
            'loader': 'Loader',
            'hash_verifier': 'HashVerifier',
            'settings_builder': 'SettingsBuilder',
            'config_validated': 'ConfigValidated',
            'questionnaire_file': 'QuestionnaireFile',
            'executor_config': 'ExecutorConfig',
            'calibration_profiles': 'CalibrationProfiles',
            'dependency_validator': 'DependencyValidator',
            'state_transition_title': 'State-Transition Graph',
            'idle': 'Idle',
            'validating': 'Validating',
            'loading': 'Loading',
            'enforcing_graph': 'EnforcingGraph',
            'dependency_check': 'DependencyCheck',
            'emitting': 'Emitting',
            'faulted': 'Faulted',
            'contract_linkage_title': 'Contract-Linkage Graph'
        },
        'es': {
            'control_flow_title': 'Grafo de Flujo de Control',
            'input_config': 'Config de entrada',
            'schema_validation': 'Validación de esquema y ruta',
            'load_questionnaire': 'Cargar cuestionario canónico',
            'derive_settings': 'Derivar AggregationSettings',
            'enforce_graph': 'Hacer cumplir grafo de fases + dependencias',
            'emit_config': 'Emitir config validado',
            'reject_run': 'Rechazar ejecución',
            'fail': 'falla',
            'hash_mismatch': 'hash incorrecto',
            'data_flow_title': 'Grafo de Flujo de Datos',
            'config_raw': 'ConfigRaw',
            'schema_validator': 'ValidadorDeEsquema',
            'loader': 'Cargador',
            'hash_verifier': 'VerificadorDeHash',
            'settings_builder': 'ConstructorDeConfiguracion',
            'config_validated': 'ConfigValidada',
            'questionnaire_file': 'ArchivoDeCuestionario',
            'executor_config': 'ConfigDeEjecutor',
            'calibration_profiles': 'PerfilesDeCalibracion',
            'dependency_validator': 'ValidadorDeDependencias',
            'state_transition_title': 'Grafo de Transición de Estado',
            'idle': 'Inactivo',
            'validating': 'Validando',
            'loading': 'Cargando',
            'enforcing_graph': 'AplicandoGrafo',
            'dependency_check': 'VerificandoDeps',
            'emitting': 'Emitiendo',
            'faulted': 'Fallido',
            'contract_linkage_title': 'Grafo de Vínculos de Contrato'
        }
    }
    return text[lang][key]

def create_control_flow_graph(lang='en'):
    """Generates the control-flow graph."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    nodes = {
        'A': (1, 5, get_text(lang, 'input_config')),
        'B': (3, 5, get_text(lang, 'schema_validation')),
        'C': (5, 5, get_text(lang, 'load_questionnaire')),
        'D': (7, 5, get_text(lang, 'derive_settings')),
        'E': (9, 5, get_text(lang, 'enforce_graph')),
        'F': (7, 3, get_text(lang, 'emit_config')),
        'Z': (5, 1, get_text(lang, 'reject_run'))
    }

    for node, (x, y, label) in nodes.items():
        ax.text(x, y, label, ha='center', va='center', bbox=dict(boxstyle='round,pad=0.5', fc=colors['bg'], ec=colors['blue']))

    arrows = [
        ('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'E'), ('E', 'F'),
        ('B', 'Z', get_text(lang, 'fail')), ('C', 'Z', get_text(lang, 'hash_mismatch'))
    ]

    for start, end, *label in arrows:
        x_start, y_start, _ = nodes[start]
        x_end, y_end, _ = nodes[end]
        ax.annotate('', xy=(x_end, y_end), xytext=(x_start, y_start),
                    arrowprops=dict(arrowstyle='->', color=colors['copper'], lw=2))
        if label:
            ax.text((x_start + x_end) / 2, (y_start + y_end) / 2, label[0],
                    ha='center', va='center', color=colors['red'])

    filename = f'docs/phases/phase_0/images/control_flow_{lang}.png'
    plt.savefig(filename, bbox_inches='tight')
    plt.close()
    print(f"Generated {filename}")

def create_data_flow_graph(lang='en'):
    """Generates the data-flow graph."""
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4)
    ax.axis('off')

    nodes = {
        'ConfigRaw': (1, 3, get_text(lang, 'config_raw')),
        'SchemaValidator': (3, 3, get_text(lang, 'schema_validator')),
        'Loader': (5, 3, get_text(lang, 'loader')),
        'HashVerifier': (7, 3, get_text(lang, 'hash_verifier')),
        'SettingsBuilder': (9, 3, get_text(lang, 'settings_builder')),
        'ConfigValidated': (11, 3, get_text(lang, 'config_validated')),
        'QuestionnaireFile': (5, 1, get_text(lang, 'questionnaire_file')),
        'ExecutorConfig': (7, 1, get_text(lang, 'executor_config')),
        'CalibrationProfiles': (9, 1, get_text(lang, 'calibration_profiles')),
        'DependencyValidator': (8, 2, get_text(lang, 'dependency_validator'))
    }

    for node, (x, y, label) in nodes.items():
        ax.text(x, y, label, ha='center', va='center', bbox=dict(boxstyle='round,pad=0.5', fc=colors['bg'], ec=colors['green']))

    arrows = [
        ('ConfigRaw', 'SchemaValidator'), ('SchemaValidator', 'Loader'),
        ('QuestionnaireFile', 'Loader'), ('Loader', 'HashVerifier'),
        ('HashVerifier', 'SettingsBuilder'), ('SettingsBuilder', 'ConfigValidated'),
        ('ExecutorConfig', 'DependencyValidator'), ('CalibrationProfiles', 'DependencyValidator'),
        ('DependencyValidator', 'ConfigValidated')
    ]

    for start, end in arrows:
        x_start, y_start, _ = nodes[start]
        x_end, y_end, _ = nodes[end]
        ax.annotate('', xy=(x_end, y_end), xytext=(x_start, y_start),
                    arrowprops=dict(arrowstyle='->', color=colors['copper'], lw=2))

    filename = f'docs/phases/phase_0/images/data_flow_{lang}.png'
    plt.savefig(filename, bbox_inches='tight')
    plt.close()
    print(f"Generated {filename}")


def create_state_transition_graph(lang='en'):
    """Generates the state-transition graph."""
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    ax.set_facecolor(colors['bg'])
    ax.grid(color=colors['copper'], linestyle='--', linewidth=0.5)
    ax.spines['polar'].set_edgecolor(colors['copper'])

    states = [
        get_text(lang, 'idle'), get_text(lang, 'validating'), get_text(lang, 'loading'),
        get_text(lang, 'enforcing_graph'), get_text(lang, 'dependency_check'),
        get_text(lang, 'emitting'), get_text(lang, 'faulted')
    ]
    theta = np.linspace(0, 2 * np.pi, len(states), endpoint=False)

    ax.set_xticks(theta)
    ax.set_xticklabels(states)
    ax.set_yticklabels([])

    transitions = [
        (get_text(lang, 'idle'), get_text(lang, 'validating')),
        (get_text(lang, 'validating'), get_text(lang, 'loading')),
        (get_text(lang, 'loading'), get_text(lang, 'enforcing_graph')),
        (get_text(lang, 'enforcing_graph'), get_text(lang, 'dependency_check')),
        (get_text(lang, 'dependency_check'), get_text(lang, 'emitting')),
        (get_text(lang, 'emitting'), get_text(lang, 'idle')),
        (get_text(lang, 'validating'), get_text(lang, 'faulted')),
        (get_text(lang, 'enforcing_graph'), get_text(lang, 'faulted')),
        (get_text(lang, 'dependency_check'), get_text(lang, 'faulted'))
    ]

    for start, end in transitions:
        start_idx = states.index(start)
        end_idx = states.index(end)
        ax.annotate('', xy=(theta[end_idx], 1), xytext=(theta[start_idx], 1),
                    arrowprops=dict(arrowstyle='->', color=colors['red'],
                                    connectionstyle='arc3,rad=0.2'))

    filename = f'docs/phases/phase_0/images/state_transition_{lang}.png'
    plt.savefig(filename, bbox_inches='tight')
    plt.close()
    print(f"Generated {filename}")

def create_contract_linkage_graph(lang='en'):
    """Generates the contract-linkage graph."""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')

    contracts = {
        'C0-CONFIG-V1': (2, 7), 'QMONO-V1': (2, 5), 'HASH-V1': (2, 3),
        'AGG-SET-V1': (2, 1), 'GRAPH-V1': (8, 7), 'EXEC-CONF / CAL-V1': (8, 5)
    }

    validators = {
        get_text(lang, 'schema_validator'): (4, 7),
        get_text(lang, 'loader'): (4, 5),
        get_text(lang, 'hash_verifier'): (4, 3),
        get_text(lang, 'settings_builder'): (4, 1),
        get_text(lang, 'enforcing_graph'): (6, 7),
        get_text(lang, 'dependency_validator'): (6, 5)
    }

    for contract, (x, y) in contracts.items():
        ax.text(x, y, contract, ha='center', va='center', bbox=dict(boxstyle='sawtooth,pad=0.5', fc=colors['bg'], ec=colors['copper_oxide']))

    for validator, (x, y) in validators.items():
        ax.text(x, y, validator, ha='center', va='center', bbox=dict(boxstyle='round,pad=0.5', fc=colors['bg'], ec=colors['blue']))

    arrows = [
        ('C0-CONFIG-V1', get_text(lang, 'schema_validator')),
        ('QMONO-V1', get_text(lang, 'loader')),
        ('HASH-V1', get_text(lang, 'hash_verifier')),
        ('AGG-SET-V1', get_text(lang, 'settings_builder')),
        ('GRAPH-V1', get_text(lang, 'enforcing_graph')),
        ('EXEC-CONF / CAL-V1', get_text(lang, 'dependency_validator'))
    ]

    for start, end in arrows:
        x_start, y_start = contracts.get(start, (0,0))
        x_end, y_end = validators.get(end, (0,0))

        if (x_start,y_start) == (0,0):
             x_start, y_start = validators.get(start, (0,0))
             x_end, y_end = contracts.get(end, (0,0))


        ax.annotate('', xy=(x_end, y_end), xytext=(x_start, y_start),
                    arrowprops=dict(arrowstyle='->', color=colors['copper'], lw=2))

    filename = f'docs/phases/phase_0/images/contract_linkage_{lang}.png'
    plt.savefig(filename, bbox_inches='tight')
    plt.close()
    print(f"Generated {filename}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate graphs for the documentation.')
    parser.add_argument('--lang', type=str, default='en', help='The language to generate the graphs in (en or es).')
    args = parser.parse_args()

    output_dir = 'docs/phases/phase_0/images'
    os.makedirs(output_dir, exist_ok=True)

    create_control_flow_graph(args.lang)
    create_data_flow_graph(args.lang)
    create_state_transition_graph(args.lang)
    create_contract_linkage_graph(args.lang)
    print("Graphs generated successfully.")

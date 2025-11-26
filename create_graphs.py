
import matplotlib.pyplot as plt
import networkx as nx

def create_atroz_graph(graph_data, filename, layout='spring'):
    """
    Generates and saves a graph with the Atroz dashboard aesthetic.
    """
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('#0A0A0A')

    G = nx.DiGraph()
    for edge in graph_data['edges']:
        G.add_edge(edge[0], edge[1])

    if layout == 'spring':
        pos = nx.spring_layout(G, seed=42)
    elif layout == 'shell':
        pos = nx.shell_layout(G)
    elif layout == 'kamada_kawai':
        pos = nx.kamada_kawai_layout(G)
    else:
        pos = nx.spring_layout(G, seed=42)


    node_colors = ['#00D4FF' if node not in graph_data.get('error_nodes', []) else '#C41E3A' for node in G.nodes()]
    edge_colors = ['#B2642E' for _ in G.edges()]

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=3000, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=1.5, arrowsize=20, ax=ax)
    nx.draw_networkx_labels(G, pos, font_family='JetBrains Mono', font_size=10, font_color='#E5E7EB', ax=ax)

    ax.set_title(graph_data['title'], fontname='JetBrains Mono', fontsize=16, color='#E5E7EB')
    plt.savefig(filename, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()

if __name__ == '__main__':
    control_flow_data = {
        'title': 'Control-Flow Graph',
        'edges': [
            ('pdf_path + config', 'run SPC ingestion'),
            ('run SPC ingestion', 'adapter → PreprocessedDocument'),
            ('adapter → PreprocessedDocument', 'validate chunk graph'),
            ('validate chunk graph', 'record ingestion metadata'),
            ('validate chunk graph', 'Abort run'),
            ('record ingestion metadata', 'emit PreprocessedDocument')
        ],
        'error_nodes': ['Abort run']
    }
    create_atroz_graph(control_flow_data, 'docs/phases/phase_1/images/control_flow.png')

    data_flow_data = {
        'title': 'Data-Flow Graph',
        'edges': [
            ('pdf_path', 'SPCIngestion'),
            ('config', 'SPCIngestion'),
            ('SPCIngestion', 'Adapter'),
            ('Adapter', 'PreprocessedDocument'),
            ('PreprocessedDocument', 'Validator'),
            ('Validator', 'OrchestratorContext'),
            ('Validator', 'VerificationManifest')
        ]
    }
    create_atroz_graph(data_flow_data, 'docs/phases/phase_1/images/data_flow.png', layout='kamada_kawai')

    state_transition_data = {
        'title': 'State-Transition Graph',
        'edges': [
            ('Idle', 'Ingesting'),
            ('Ingesting', 'Adapting'),
            ('Ingesting', 'Faulted'),
            ('Adapting', 'Validating'),
            ('Adapting', 'Faulted'),
            ('Validating', 'Recording'),
            ('Validating', 'Faulted'),
            ('Recording', 'Emitting'),
            ('Emitting', 'Idle')
        ],
        'error_nodes': ['Faulted']
    }
    create_atroz_graph(state_transition_data, 'docs/phases/phase_1/images/state_transition.png', layout='shell')

    contract_linkage_data = {
        'title': 'Contract-Linkage Graph',
        'edges': [
            ('SPC-PIPELINE-V1', 'SPCIngestion'),
            ('CPP-ADAPTER-V1', 'Adapter'),
            ('SPC-CHUNK-V1', 'Validator'),
            ('PREPROC-V1', 'Validator'),
            ('VERIF-MANIFEST-V1', 'Recording')
        ]
    }
    create_atroz_graph(contract_linkage_data, 'docs/phases/phase_1/images/contract_linkage.png', layout='kamada_kawai')

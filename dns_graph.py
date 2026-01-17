"""dns_graph.py - Configuration et affichage du graphe DNS"""

import networkx as nx
import matplotlib.pyplot as plt
import os


def hierarchical_layout(G):
    """Crée un layout hiérarchique où les enfants sont proche de leur parent"""
    pos = {}
    
    """On groupe les noeuds par couche"""
    layers = {}
    for node in G.nodes():
        layer = G.nodes[node].get('layer', 1)
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(node)
    
    sorted_layers = sorted(layers.keys())
    if not sorted_layers:
        return pos
    
    x_spacing = 4.0
    y_spacing = 1.5
    
    """Première couche : on place les noeuds verticalement"""
    first_layer = sorted_layers[0]
    nodes = sorted(layers[first_layer])
    total_height = (len(nodes) - 1) * y_spacing
    start_y = total_height / 2
    for i, node in enumerate(nodes):
        pos[node] = (first_layer * x_spacing, start_y - i * y_spacing)
    
    """Couches suivantes : on place les enfants près de leur parent"""
    for layer_num in sorted_layers[1:]:
        nodes = layers[layer_num]
        node_y_targets = {}
        
        """Pour chaque noeud (on calcule la position Y moyenne de ses parents)"""
        for node in nodes:
            parent_ys = []
            for pred in G.predecessors(node):
                if pred in pos:
                    parent_ys.append(pos[pred][1])
            
            if parent_ys:
                node_y_targets[node] = sum(parent_ys) / len(parent_ys)
            else:
                node_y_targets[node] = 0
        
        """On trie les noeuds par leur position Y cible"""
        sorted_nodes = sorted(nodes, key=lambda n: node_y_targets[n], reverse=True)
        
        """On place les noeuds avec un espacement minimum"""
        x = layer_num * x_spacing
        if len(sorted_nodes) == 1:
            pos[sorted_nodes[0]] = (x, node_y_targets[sorted_nodes[0]])
        else:
            """On évite les chevauchements en espaçant les noeuds"""
            total_height = (len(sorted_nodes) - 1) * y_spacing
            center_y = sum(node_y_targets.values()) / len(node_y_targets)
            start_y = center_y + total_height / 2
            
            for i, node in enumerate(sorted_nodes):
                pos[node] = (x, start_y - i * y_spacing)
    
    return pos


def draw_dns_graph(edges, all_domains, start_domain, output_dir=None):
    """Dessine le graphe DNS avec les données de l'exploration"""
    
    G = nx.DiGraph()
    
    """On ajoute les noeuds avec leur couche"""
    for domain, layer in all_domains.items():
        G.add_node(domain, layer=layer)
    
    """On ajoute les arêtes"""
    for source, target in edges:
        G.add_edge(source, target)
    
    """Taille dynamique selon le nombre de noeuds"""
    num_nodes = G.number_of_nodes()
    if num_nodes < 20:
        fig_size = (20, 14)
        node_size = 1000
        font_size = 9
    elif num_nodes < 50:
        fig_size = (30, 20)
        node_size = 600
        font_size = 8
    elif num_nodes < 100:
        fig_size = (40, 28)
        node_size = 400
        font_size = 7
    else:
        fig_size = (50, 35)
        node_size = 300
        font_size = 6
    
    """Configuration de la figure"""
    fig = plt.figure(figsize=fig_size)
    fig.set_facecolor('#1a1a2e')
    ax = plt.gca()
    ax.set_facecolor('#1a1a2e')
    plt.title(f"Graphe DNS - {start_domain} ({num_nodes} noeuds)", 
              fontsize=18, fontweight='bold', color='white', pad=20)
    
    """Layout hiérarchique par couche"""
    pos = hierarchical_layout(G)
    
    """Mapping couleur par couche"""
    layer_colors = {
        1: '#6624a8',  # violet - départ
        2: '#e67e30',  # orange
        3: '#e60029',  # rouge
        4: '#96CEB4',  # vert
        5: '#4FC3F7',  # bleu clair
        6: '#FFD54F',  # jaune
    }
    default_color = '#DDA0DD'
    
    """Couleurs selon la couche"""
    colors = []
    for node in G.nodes():
        layer = G.nodes[node].get('layer', 1)
        colors.append(layer_colors.get(layer, default_color))
    
    """On dessine les noeuds"""
    nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=node_size, 
                           alpha=0.9, edgecolors='white', linewidths=1)
    
    """On dessine les arêtes"""
    edge_colors = []
    for source, target in G.edges():
        source_layer = G.nodes[source].get('layer', 1)
        edge_colors.append(layer_colors.get(source_layer, default_color))
    
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, arrows=True, 
                           arrowsize=15, alpha=0.6, width=1.5,
                           connectionstyle="arc3,rad=0.05")
    
    """Labels complets à côté des noeuds"""
    label_pos = {node: (x + 0.3, y) for node, (x, y) in pos.items()}
    labels = {node: node for node in G.nodes()}
    
    nx.draw_networkx_labels(G, label_pos, labels, font_size=font_size, 
                            font_weight='bold', font_color='white',
                            horizontalalignment='left')
    
    """Légende des couleurs"""
    legend_elements = [
        plt.scatter([], [], c='#6624a8', s=150, label='Couche 1'),
        plt.scatter([], [], c='#e67e30', s=150, label='Couche 2'),
        plt.scatter([], [], c='#e60029', s=150, label='Couche 3'),
        plt.scatter([], [], c='#96CEB4', s=150, label='Couche 4'),
        plt.scatter([], [], c='#4FC3F7', s=150, label='Couche 5'),
        plt.scatter([], [], c='#FFD54F', s=150, label='Couche 6'),
        plt.scatter([], [], c='#DDA0DD', s=150, label='Couche 7+'),
    ]
    plt.legend(handles=legend_elements, loc='upper left', 
               facecolor='#2d2d44', edgecolor='white', labelcolor='white',
               fontsize=10)
    
    plt.axis('off')
    plt.tight_layout()
    
    """Export si demandé"""
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        safe_name = start_domain.replace('.', '_').replace(':', '_')
        
        svg_path = os.path.join(output_dir, f"{safe_name}_graph.svg")
        plt.savefig(svg_path, format='svg', facecolor='#1a1a2e', 
                    edgecolor='none', bbox_inches='tight', dpi=150)
        print(f"  SVG sauvegardé: {svg_path}")
        
        dot_path = os.path.join(output_dir, f"{safe_name}_graph.dot")
        export_to_dot(G, dot_path, layer_colors, default_color)
        print(f"  DOT sauvegardé: {dot_path}")
        
        png_path = os.path.join(output_dir, f"{safe_name}_graph.png")
        plt.savefig(png_path, format='png', facecolor='#1a1a2e', 
                    edgecolor='none', bbox_inches='tight', dpi=150)
        print(f"  PNG sauvegardé: {png_path}")
    
    print(f"\n Ouverture du graphe ({num_nodes} noeuds, {G.number_of_edges()} liens)...")
    plt.show()
    
    return G


def export_to_dot(G, filepath, layer_colors, default_color):
    """Exporte le graphe au format DOT (Graphviz)"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('digraph DNS {\n')
        f.write('    bgcolor="#1a1a2e";\n')
        f.write('    node [style=filled, fontcolor=white, fontname="Arial", fontsize=12];\n')
        f.write('    edge [color="#666666"];\n')
        f.write('    rankdir=LR;\n')
        f.write('    overlap=false;\n')
        f.write('    splines=true;\n')
        f.write('    nodesep=0.5;\n')
        f.write('    ranksep=1.5;\n\n')
        
        for node in G.nodes():
            layer = G.nodes[node].get('layer', 1)
            color = layer_colors.get(layer, default_color)
            safe_node = node.replace('"', '\\"')
            f.write(f'    "{safe_node}" [fillcolor="{color}"];\n')
        
        f.write('\n')
        
        for source, target in G.edges():
            safe_source = source.replace('"', '\\"')
            safe_target = target.replace('"', '\\"')
            source_layer = G.nodes[source].get('layer', 1)
            edge_color = layer_colors.get(source_layer, default_color)
            f.write(f'    "{safe_source}" -> "{safe_target}" [color="{edge_color}"];\n')
        
        f.write('}\n')

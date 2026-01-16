"""dns_graph.py - Configuration et affichage du graphe DNS"""

import networkx as nx
import matplotlib.pyplot as plt
import os


def draw_dns_graph(edges, all_domains, start_domain, output_dir=None):
    """Dessine le graphe DNS avec les données de l'exploration
    
    Args:
        edges: liste de tuples (source, target)
        all_domains: dict {domain: layer}
        start_domain: domaine de départ
        output_dir: dossier pour sauvegarder les exports (optionnel)
    """
    
    G = nx.DiGraph()
    
    """On ajoute les noeuds avec leur couche"""
    for domain, layer in all_domains.items():
        G.add_node(domain, layer=layer)
    
    """On ajoute les arêtes"""
    for source, target in edges:
        G.add_edge(source, target)
    
    """Taille dynamique selon le nombre de noeuds"""
    num_nodes = G.number_of_nodes()
    if num_nodes < 30:
        fig_size = (16, 12)
        node_size = 800
        font_size = 8
        k_spacing = 2
    elif num_nodes < 100:
        fig_size = (24, 18)
        node_size = 500
        font_size = 6
        k_spacing = 3
    else:
        fig_size = (32, 24)
        node_size = 300
        font_size = 5
        k_spacing = 4
    
    """Configuration de la figure"""
    fig = plt.figure(figsize=fig_size)
    fig.set_facecolor('#1a1a2e')
    ax = plt.gca()
    ax.set_facecolor('#1a1a2e')
    plt.title(f"Graphe DNS - {start_domain} ({num_nodes} noeuds)", 
              fontsize=16, fontweight='bold', color='white')
    
    """Layout adaptatif selon la taille du graphe"""
    try:
        if num_nodes > 50:
            # Pour les grands graphes, layout hiérarchique
            pos = nx.kamada_kawai_layout(G)
        else:
            pos = nx.spring_layout(G, k=k_spacing, iterations=100, seed=42)
    except:
        pos = nx.kamada_kawai_layout(G)
    
    """Mapping couleur par couche"""
    layer_colors = {
        1: '#6624a8',  # violet - départ
        2: '#e67e30',  # orange
        3: '#e60029',  # rouge
        4: '#96CEB4',  # vert
    }
    default_color = '#DDA0DD'  # violet clair pour couches 5+
    
    """Couleurs selon la couche"""
    colors = []
    for node in G.nodes():
        layer = G.nodes[node].get('layer', 1)
        colors.append(layer_colors.get(layer, default_color))
    
    """On dessine les noeuds"""
    nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=node_size, 
                           alpha=0.9, edgecolors='white', linewidths=0.5)
    
    """On dessine les arêtes avec la couleur du noeud source"""
    edge_colors = []
    for source, target in G.edges():
        source_layer = G.nodes[source].get('layer', 1)
        edge_colors.append(layer_colors.get(source_layer, default_color))
    
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, arrows=True, 
                           arrowsize=12, alpha=0.6, connectionstyle="arc3,rad=0.1",
                           width=1.5)
    
    """Labels des noeuds (on raccourcit si trop long)"""
    labels = {}
    for node in G.nodes():
        if len(node) > 15:
            # Garde le premier sous-domaine + TLD
            parts = node.split('.')
            if len(parts) >= 2:
                labels[node] = parts[0][:8] + ".." + parts[-1]
            else:
                labels[node] = node[:12] + ".."
        else:
            labels[node] = node
    
    nx.draw_networkx_labels(G, pos, labels, font_size=font_size, 
                            font_weight='bold', font_color='white')
    
    """Légende des couleurs"""
    legend_elements = [
        plt.scatter([], [], c='#6624a8', s=100, label='Couche 1 (départ)'),
        plt.scatter([], [], c='#e67e30', s=100, label='Couche 2'),
        plt.scatter([], [], c='#e60029', s=100, label='Couche 3'),
        plt.scatter([], [], c='#96CEB4', s=100, label='Couche 4'),
        plt.scatter([], [], c='#DDA0DD', s=100, label='Couche 5+'),
    ]
    plt.legend(handles=legend_elements, loc='upper left', 
               facecolor='#2d2d44', edgecolor='white', labelcolor='white')
    
    plt.axis('off')
    plt.tight_layout()
    
    """Export DOT et SVG si demandé"""
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        safe_name = start_domain.replace('.', '_').replace(':', '_')
        
        # Export SVG
        svg_path = os.path.join(output_dir, f"{safe_name}_graph.svg")
        plt.savefig(svg_path, format='svg', facecolor='#1a1a2e', 
                    edgecolor='none', bbox_inches='tight', dpi=150)
        print(f"  SVG sauvegardé: {svg_path}")
        
        # Export DOT
        dot_path = os.path.join(output_dir, f"{safe_name}_graph.dot")
        export_to_dot(G, dot_path, layer_colors, default_color)
        print(f"  DOT sauvegardé: {dot_path}")
        
        # Export PNG aussi
        png_path = os.path.join(output_dir, f"{safe_name}_graph.png")
        plt.savefig(png_path, format='png', facecolor='#1a1a2e', 
                    edgecolor='none', bbox_inches='tight', dpi=150)
        print(f"  PNG sauvegardé: {png_path}")
    
    """Pour finir on affiche le graphe"""
    print(f"\n Ouverture du graphe ({num_nodes} noeuds, {G.number_of_edges()} liens)...")
    plt.show()
    
    return G


def export_to_dot(G, filepath, layer_colors, default_color):
    """Exporte le graphe au format DOT (Graphviz)"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('digraph DNS {\n')
        f.write('    bgcolor="#1a1a2e";\n')
        f.write('    node [style=filled, fontcolor=white, fontname="Arial"];\n')
        f.write('    edge [color="#666666"];\n')
        f.write('    rankdir=LR;\n')
        f.write('    overlap=false;\n')
        f.write('    splines=true;\n\n')
        
        # Noeuds avec leurs couleurs
        for node in G.nodes():
            layer = G.nodes[node].get('layer', 1)
            color = layer_colors.get(layer, default_color)
            safe_node = node.replace('"', '\\"')
            f.write(f'    "{safe_node}" [fillcolor="{color}"];\n')
        
        f.write('\n')
        
        # Arêtes
        for source, target in G.edges():
            safe_source = source.replace('"', '\\"')
            safe_target = target.replace('"', '\\"')
            source_layer = G.nodes[source].get('layer', 1)
            edge_color = layer_colors.get(source_layer, default_color)
            f.write(f'    "{safe_source}" -> "{safe_target}" [color="{edge_color}"];\n')
        
        f.write('}\n')

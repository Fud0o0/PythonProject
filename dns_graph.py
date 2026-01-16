"""dns_graph.py - Configuration et affichage du graphe DNS"""

import networkx as nx
import matplotlib.pyplot as plt


def draw_dns_graph(edges, all_domains, start_domain):
    """Dessine le graphe DNS avec les données de l'exploration"""
    
    G = nx.DiGraph()
    
    """On ajoute les noeuds avec leur couche"""
    for domain, layer in all_domains.items():
        G.add_node(domain, layer=layer)
    
    """On ajoute les arêtes"""
    for source, target in edges:
        G.add_edge(source, target)
    
    """Configuration de la figure"""
    fig = plt.figure(figsize=(16, 12))
    fig.set_facecolor('#1a1a2e')  # Fond sombre bleu-gris
    ax = plt.gca()
    ax.set_facecolor('#1a1a2e')
    plt.title(f"Graphe DNS - {start_domain}", fontsize=16, fontweight='bold', color='white')
    
    """Layout pour espacer les noeuds"""
    try:
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    except:
        pos = nx.kamada_kawai_layout(G)
    
    """Couleurs selon la couche"""
    colors = []
    for node in G.nodes():
        layer = G.nodes[node].get('layer', 1)
        if layer == 1:
            colors.append('#6624a8')  # rouge - départ
        elif layer == 2:
            colors.append('#4ECDC4')  # turquoise
        elif layer == 3:
            colors.append('#45B7D1')  # bleu
        elif layer == 4:
            colors.append('#96CEB4')  # vert
        else:
            colors.append('#DDA0DD')  # violet pour les couches 5+
    
    """On dessine les noeuds"""
    nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=800, alpha=0.9)
    
    """On dessine les arêtes avec des flèches"""
    nx.draw_networkx_edges(G, pos, edge_color='#666666', arrows=True, 
                           arrowsize=15, alpha=0.6, connectionstyle="arc3,rad=0.1")
    
    """Labels des noeuds (on raccourcit si trop long)"""
    labels = {}
    for node in G.nodes():
        if len(node) > 20:
            labels[node] = node.split('.')[0] + "..."
        else:
            labels[node] = node
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold', font_color='white')
    
    """légende des couleurs"""
    legend_elements = [
        plt.scatter([], [], c='#6624a8', s=100, label='Couche 1 (départ)'),
        plt.scatter([], [], c='#4ECDC4', s=100, label='Couche 2'),
        plt.scatter([], [], c='#45B7D1', s=100, label='Couche 3'),
        plt.scatter([], [], c='#96CEB4', s=100, label='Couche 4'),
        plt.scatter([], [], c='#DDA0DD', s=100, label='Couche 5+'),
    ]
    plt.legend(handles=legend_elements, loc='upper left', 
               facecolor='#2d2d44', edgecolor='white', labelcolor='white')
    
    plt.axis('off')
    plt.tight_layout()
    
    """Pour finir on affiche le graphe"""
    print(f"\n Ouverture du graphe ({G.number_of_nodes()} noeuds, {G.number_of_edges()} liens)...")
    plt.show()

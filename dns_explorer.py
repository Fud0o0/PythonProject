"""dns_explorer.py - Exploration DNS couche par couche (avec parents)"""

import dns.resolver
from dns_graph import draw_dns_graph


"""on importe le module dns.resolver pour faire les requetes DNS"""

def get_parent_domain(domain):
    """Cette fonction récupère le domaine parent
    par exemple si on a "sub.exemple.com" elle renvoi "exemple.com"
    c'est pratique pour remonter dans la hierarchie"""
    parts = domain.split(".")
    if len(parts) > 2:
        return ".".join(parts[1:])
    return None


def resolve_all_records(domain, timeout=3):
    """Ici on fait toutes les requetes DNS possible sur un domaine
    genre A, AAAA, MX, NS etc... sa permet de tout récupérer d'un coup"""
    record_types = ["A", "AAAA", "CNAME", "MX", "NS", "TXT", "SOA","PTR","CAA","SRV"]
    results = {}
    
    """on crée le resolver avec un timeout pour pas attendre trop longtemps"""
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout
    
    """on boucle sur chaque type et on essaye de résoudre"""
    for rtype in record_types:
        try:
            answers = resolver.resolve(domain, rtype)
            results[rtype] = [answer.to_text() for answer in answers]
        except:
            pass
    
    return results


def extract_domains_from_records(records, current_domain):
    """Cette fonction extrait tout les domaines qu'on trouve dans les enregistrements
    comme sa on peut les explorer après dans les prochaines couches"""
    domains = set()
    
    """CNAME -> c'est une redirection vers un autre domaine"""
    if "CNAME" in records:
        for cname in records["CNAME"]:
            domains.add(cname.rstrip("."))
    
    """MX -> c'est les serveurs mails, genre smtp.google.com"""
    if "MX" in records:
        for mx in records["MX"]:
            parts = mx.split()
            if len(parts) >= 2:
                domains.add(parts[1].rstrip("."))
    
    """NS -> les serveurs DNS qui gèrent le domaine"""
    if "NS" in records:
        for ns in records["NS"]:
            domains.add(ns.rstrip("."))
    
    """SOA -> le serveur DNS primaire du domaine"""
    if "SOA" in records:
        for soa in records["SOA"]:
            parts = soa.split()
            if parts:
                domains.add(parts[0].rstrip("."))
    
    """SRV -> des services genre _sip ou _xmpp avec leur serveur"""
    if "SRV" in records:
        for srv in records["SRV"]:
            parts = srv.split()
            if len(parts) >= 4:
                domains.add(parts[3].rstrip("."))
    
    """TXT -> ya souvent des trucs SPF dedans avec des includes"""
    if "TXT" in records:
        for txt in records["TXT"]:
            if "include:" in txt:
                import re
                includes = re.findall(r'include:([^\s"]+)', txt)
                for inc in includes:
                    domains.add(inc.rstrip("."))
            if "redirect=" in txt:
                import re
                redirects = re.findall(r'redirect=([^\s"]+)', txt)
                for redir in redirects:
                    domains.add(redir.rstrip("."))
    
    """CAA -> les autorités de certification autorisées"""
    if "CAA" in records:
        for caa in records["CAA"]:
            parts = caa.split()
            if len(parts) >= 3:
                domain_part = parts[-1].strip('"').rstrip(".")
                if "." in domain_part and not domain_part.startswith("http"):
                    domains.add(domain_part)
    
    """PTR -> résolution inverse, genre IP vers nom de domaine"""
    if "PTR" in records:
        for ptr in records["PTR"]:
            domains.add(ptr.rstrip("."))
    
    """on ajoute aussi le domaine parent pour remonter la hiérarchie"""
    parent = get_parent_domain(current_domain)
    if parent:
        domains.add(parent)
    
    return domains


def resolve_layer(domains, layer_num, all_resolved, graph_edges, domain_layers):
    """Cette fonction résoud une couche complète de domaines
    elle affiche les résultats et retourne les nouveaux domaines a explorer"""
    print(f"\n{'='*60}")
    print(f" Couche n° {layer_num}")
    print(f"{'='*60}")
    
    next_domains = set()
    
    """on boucle sur chaque domaine de la couche"""
    for domain in sorted(domains):
        print(f"\n • {domain}")
        
        """on enregistre la couche du domaine pour le graphe"""
        domain_layers[domain] = layer_num
        
        """on résoud tout les enregistrements du domaine"""
        records = resolve_all_records(domain)
        
        if not records:
            print(f" └─ Il n'y a aucun enregistement trouvé")
        else:
            """on affiche les 3 premiers de chaque type"""
            for rtype, values in records.items():
                for val in values[:3]:
                    print(f" ├─ {rtype}: {val}")
        
        """on check si le parent est pas déja exploré"""
        parent = get_parent_domain(domain)
        if parent and parent not in all_resolved and parent not in domains:
            next_domains.add(parent)
            graph_edges.append((domain, parent))

        """on extrait tout les domaines des enregistrements"""
        found = extract_domains_from_records(records, domain)
        new_domains = found - all_resolved - domains
        
        """on ajoute les liens pour le graphe"""
        for target in new_domains:
            graph_edges.append((domain, target))
        
        if new_domains:
            next_domains.update(new_domains)
    
    print(f"\n   → {len(next_domains)} nouveau(x) domaine(s) à explorer")
    return next_domains


def explore_dns(domain, max_layers, export=False, output_dir="exports"):
    """Explore un domaine DNS sur plusieurs couches
    
    Args:
        domain: Le domaine de départ
        max_layers: Nombre de couches à explorer
        export: Si True, exporte le graphe
        output_dir: Dossier pour les exports
        
    Returns:
        tuple: (all_resolved, graph_edges, domain_layers)
    """
    print("\n" + "=" * 60)
    print(" Exploration des couches DNS")
    print("=" * 60)
    print(f" Domaine: {domain}")
    print(f" Couches: {max_layers}")
    
    """on commence avec le domaine donné"""
    current_domains = {domain}
    all_resolved = set()
    
    """données pour le graphe"""
    graph_edges = []
    domain_layers = {}
    
    """on boucle sur chaque couche"""
    for layer in range(1, max_layers + 1):
        to_resolve = current_domains - all_resolved
        
        """si il y a plus rien a explorer on arrête"""
        if not to_resolve:
            print(f"\n Il n'y a plus de domaines à explorer après {layer-1} couche(s)")
            break
        
        all_resolved.update(to_resolve)
        next_domains = resolve_layer(to_resolve, layer, all_resolved, graph_edges, domain_layers)
        current_domains = next_domains
    
    """a la fin on affiche le résumé de tout ce qu'on a trouvé"""
    print(f"\n{'='*60}")
    print(f" Total: {len(all_resolved)} domaine(s) exploré(s)")
    print(f"{'='*60}")
    for d in sorted(all_resolved):
        print(f"•{d}")
    
    """on affiche le graphe à la fin"""
    if len(domain_layers) > 0:
        draw_dns_graph(graph_edges, domain_layers, domain, output_dir if export else None)
    
    return all_resolved, graph_edges, domain_layers


def parse_args():
    """Parse les arguments de la ligne de commande"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Explorateur DNS multi-couches avec visualisation graphique",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python dns_explorer.py -d google.com -l 3
  python dns_explorer.py --domain example.org --layers 5 --export
  python dns_explorer.py --loop  (mode interactif)
        """
    )
    
    parser.add_argument(
        "-d", "--domain",
        type=str,
        help="Domaine à explorer (ex: google.com)"
    )
    
    parser.add_argument(
        "-l", "--layers",
        type=int,
        default=3,
        help="Nombre de couches à explorer (défaut: 3)"
    )
    
    parser.add_argument(
        "-e", "--export",
        action="store_true",
        help="Exporter le graphe en DOT/SVG/PNG"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="exports",
        help="Dossier de sortie pour les exports (défaut: exports)"
    )
    
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Mode interactif en boucle"
    )
    
    return parser.parse_args()


def interactive_mode():
    """Mode interactif qui boucle en continu"""
    while True:
        print("\n" + "=" * 60)
        print(" Mode interactif - Exploration DNS")
        print("=" * 60)
        
        """on demande le domaine a l'utilisateur"""
        domain = input("\n Veuillez donner le nom de domaine: ").strip()
        if not domain:
            print(" Domaine invalide!")
            continue
        
        """on demande combien de couches il veut explorer"""
        try:
            max_layers = int(input(" Nombre de couches: ").strip())
        except:
            max_layers = 3
        
        """on demande si l'utilisateur veut exporter le graphe"""
        export = input(" Exporter le graphe (DOT/SVG/PNG)? (o/n): ").strip().lower()
        do_export = export in ('o', 'oui', 'y', 'yes')
        
        explore_dns(domain, max_layers, export=do_export)
        
        print("\n" + "-" * 60)
        print(" Redémarrage automatique...")
        print("-" * 60)


def main():
    """Fonction principale qui gère tout le programme"""
    args = parse_args()
    
    if args.loop or args.domain is None:
        """Mode interactif"""
        interactive_mode()
    else:
        """Mode ligne de commande"""
        explore_dns(args.domain, args.layers, export=args.export, output_dir=args.output)


if __name__ == "__main__":
    main()

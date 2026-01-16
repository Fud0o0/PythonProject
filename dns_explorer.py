"""dns_explorer.py - Exploration DNS couche par couche (avec parents)"""

import dns.resolver



def get_parent_domain(domain):
    """Extrait le domaine parent"""
    parts = domain.split(".")
    if len(parts) > 2:
        return ".".join(parts[1:])
    return None


def resolve_all_records(domain, timeout=3):
    """Résout tous les types d'enregistrements DNS"""
    record_types = ["A", "AAAA", "CNAME", "MX", "NS", "TXT", "SOA"]
    results = {}
    
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout
    
    for rtype in record_types:
        try:
            answers = resolver.resolve(domain, rtype)
            results[rtype] = [answer.to_text() for answer in answers]
        except:
            pass
    
    return results


def extract_domains_from_records(records, current_domain):
    """Extrait les domaines cibles des enregistrements + parent"""
    domains = set()
    """CNAME -> cible directe"""
    if "CNAME" in records:
        for cname in records["CNAME"]:
            domains.add(cname.rstrip("."))
    
    """MX -> serveur mail"""
    if "MX" in records:
        for mx in records["MX"]:
            parts = mx.split()
            if len(parts) >= 2:
                domains.add(parts[1].rstrip("."))
    
    """NS -> serveurs DNS"""
    if "NS" in records:
        for ns in records["NS"]:
            domains.add(ns.rstrip("."))
    
    """SOA -> serveur primaire"""
    if "SOA" in records:
        for soa in records["SOA"]:
            parts = soa.split()
            if parts:
                domains.add(parts[0].rstrip("."))
    
    """SRV -> serveur cible"""
    if "SRV" in records:
        for srv in records["SRV"]:
            parts = srv.split()
            if len(parts) >= 4:
                domains.add(parts[3].rstrip("."))
    
    """TXT -> SPF includes et autres domaines"""
    if "TXT" in records:
        for txt in records["TXT"]:
            # Extraire les includes SPF
            if "include:" in txt:
                import re
                includes = re.findall(r'include:([^\s"]+)', txt)
                for inc in includes:
                    domains.add(inc.rstrip("."))
            # Extraire les redirects SPF
            if "redirect=" in txt:
                import re
                redirects = re.findall(r'redirect=([^\s"]+)', txt)
                for redir in redirects:
                    domains.add(redir.rstrip("."))
    
    """CAA -> autorités de certification"""
    if "CAA" in records:
        for caa in records["CAA"]:
            parts = caa.split()
            if len(parts) >= 3:
                # Le dernier élément est souvent un domaine
                domain_part = parts[-1].strip('"').rstrip(".")
                if "." in domain_part and not domain_part.startswith("http"):
                    domains.add(domain_part)
    
    """PARENT DOMAIN (pour continuer l'exploration)"""
    parent = get_parent_domain(current_domain)
    if parent:
        domains.add(parent)
    
    return domains


def resolve_layer(domains, layer_num, all_resolved):
    """Résout une couche de domaines"""
    print(f"\n{'='*60}")
    print(f"Couche n° {layer_num}")
    print(f"{'='*60}")
    
    next_domains = set()
    
    for domain in sorted(domains):
        print(f"\n🔹 {domain}")
        
        """Résoudre tous les enregistrements DNS"""
        records = resolve_all_records(domain)
        
        if not records:
            print(f"   └─ Il n'y a aucun enregistement trouvé")
        else:
            """Afficher chaque type"""
            for rtype, values in records.items():
                for val in values[:3]:
                    print(f"   ├─ {rtype}: {val}")
        """Explorer le parent au lieu de l'afficher"""  
        parent = get_parent_domain(domain)
        if parent and parent not in all_resolved and parent not in domains:
            next_domains.add(parent)

        """Extraire les domaines à explorer avec les parent et les enregistrements"""
        found = extract_domains_from_records(records, domain)
        new_domains = found - all_resolved - domains
        
        if new_domains:
            next_domains.update(new_domains)
    
    print(f"\n   → {len(next_domains)} nouveau(x) domaine(s) à explorer")
    return next_domains


def main():
    """Fonction principale"""
    print("=" * 60)
    print("   exploration des couche DNS")
    print("=" * 60)
    
    """Demander le domaine"""
    domain = input("\n veuillez donner le nom de domaine: ").strip()
    
    """Demander le nombre de couches"""
    try:
        max_layers = int(input(" Nombre de couches: ").strip())
    except:
        max_layers = 3
    
    """Exploration couche par couche"""
    current_domains = {domain}
    all_resolved = set()
    
    for layer in range(1, max_layers + 1):
        to_resolve = current_domains - all_resolved
        
        if not to_resolve:
            print(f"\n il n'y a plus de domaines à explorer après {layer-1} couche(s)")
            break
        
        all_resolved.update(to_resolve)
        next_domains = resolve_layer(to_resolve, layer, all_resolved)
        current_domains = next_domains
    
    """Résumé"""
    print(f"\n{'='*60}")
    print(f" Total: {len(all_resolved)} domaine(s) exploré(s)")
    print(f"{'='*60}")
    for d in sorted(all_resolved):
        print(f"   • {d}")


if __name__ == "__main__":
    main()


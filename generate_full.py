import sys
import json
import os
import networkx as nx
from collections import defaultdict

# Import export tools from graphify
from graphify.export import to_html

def main():
    json_path = "/root/graph-teee/graphify/data/kubernetes/cluster_state-1.json"
    output_html = "/root/graph-teee/graphify/data/graphify-out/cluster_state-1_full.html"
    
    print(f"Loading {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    G = nx.DiGraph()
    items = data.get("items", [])
    print(f"Found {len(items)} items in cluster state.")
    
    type_to_cid = {}
    namespace_to_cid = {}
    community_labels = {}
    
    def get_cid_for_ns(ns):
        if not ns:
            ns = "cluster-scoped"
        if ns not in namespace_to_cid:
            cid = 100 + len(namespace_to_cid)
            namespace_to_cid[ns] = cid
            community_labels[cid] = f"NS: {ns}"
        return namespace_to_cid[ns]

    # Create nodes for ALL items
    for item in items:
        kind = item.get("kind", "Unknown")
        metadata = item.get("metadata", {})
        name = metadata.get("name", "unnamed")
        ns = metadata.get("namespace", "default")
        
        node_id = f"{kind}_{ns}_{name}"
        
        # Determine color/icon based on kind
        color = "#9E9E9E"
        icon_code = '\uf013' # gear
        if kind == "Pod": color = "#8AC926"; icon_code = '\uf466'
        elif kind == "Service": color = "#1982C4"; icon_code = '\uf085'
        elif kind == "Ingress": color = "#FF595E"; icon_code = '\uf0ac'
        elif kind == "ConfigMap": color = "#FFCA3A"; icon_code = '\uf1c0'
        elif kind == "Secret": color = "#6A4C93"; icon_code = '\uf084'
        elif kind == "Deployment": color = "#F15BB5"; icon_code = '\uf0e8'
        elif kind == "Node": color = "#06D6A0"; icon_code = '\uf233'
        
        G.add_node(node_id,
                   type=kind,
                   label=f"{name}\n({kind})",
                   file_type=f"K8s {kind}",
                   source_file=f"Namespace: {ns}",
                   shape='icon',
                   icon={'face': '"Font Awesome 6 Free"', 'code': icon_code, 'weight': '900', 'color': color},
                   provider="kubernetes",
                   namespace=ns)
                   
        # Edge from Namespace to Item
        ns_id = f"ns_{ns}"
        if not G.has_node(ns_id):
            G.add_node(ns_id, type="Namespace", label=f"{ns}\n(Namespace)", file_type="K8s Namespace", source_file="-",
                       shape='icon', icon={'face': '"Font Awesome 6 Free"', 'code': '\uf07b', 'weight': '900', 'color': "#FFFFFF"},
                       provider="kubernetes", namespace=ns)
            
        G.add_edge(ns_id, node_id, relation="contains")

    # Match Services to Pods
    services = [i for i in items if i.get("kind") == "Service"]
    pods = [i for i in items if i.get("kind") == "Pod"]
    ingresses = [i for i in items if i.get("kind") == "Ingress"]

    for svc in services:
        svc_name = svc["metadata"]["name"]
        svc_ns = svc["metadata"].get("namespace", "default")
        svc_id = f"Service_{svc_ns}_{svc_name}"
        
        selector = svc.get("spec", {}).get("selector", {})
        if selector:
            for p in pods:
                p_ns = p["metadata"].get("namespace", "default")
                if p_ns != svc_ns: continue
                p_labels = p["metadata"].get("labels", {})
                match = all(p_labels.get(k) == v for k, v in selector.items())
                if match:
                    pod_id = f"Pod_{p_ns}_{p['metadata']['name']}"
                    G.add_edge(svc_id, pod_id, relation="selects_pod")

    # Match Ingresses to Services
    for ing in ingresses:
        ing_name = ing["metadata"]["name"]
        ing_ns = ing["metadata"].get("namespace", "default")
        ing_id = f"Ingress_{ing_ns}_{ing_name}"
        
        rules = ing.get("spec", {}).get("rules", [])
        for r in rules:
            for p in r.get("http", {}).get("paths", []):
                backend_svc = p.get("backend", {}).get("service", {}).get("name")
                if backend_svc:
                    svc_id = f"Service_{ing_ns}_{backend_svc}"
                    G.add_edge(ing_id, svc_id, relation="routes_to")

    communities = defaultdict(list)
    for node_id, data in G.nodes(data=True):
        ns = data.get("namespace", "default")
        cid = get_cid_for_ns(ns)
        communities[cid].append(node_id)
        
    print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    
    # Use node_limit=99999999 to prevent restricting the view!
    to_html(G, dict(communities), output_html, community_labels=community_labels, node_limit=99999999)
    print(f"Generated unrestricted graph at: {output_html}")

if __name__ == "__main__":
    main()

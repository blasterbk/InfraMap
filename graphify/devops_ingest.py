import os
import glob
import networkx as nx
from collections import defaultdict

from graphify.linode_ingest import parse_linode
from graphify.bunny_ingest import parse_bunny
from graphify.kubernetes_ingest import parse_kubernetes
def _compute_communities(G):
    type_to_cid = {
        "Server": 0,
        "Region": 1,
        "Environment": 2,
        "MainDomain": 3,
        "SubDomain": 4,
    }
    
    community_labels = {cid: label for label, cid in type_to_cid.items()}
    communities = defaultdict(list)
    namespace_to_cid = {}
    
    for node_id, data in G.nodes(data=True):
        ns = data.get("namespace")
        if ns:
            if ns not in namespace_to_cid:
                cid = len(type_to_cid) + len(namespace_to_cid) + 100
                namespace_to_cid[ns] = cid
                community_labels[cid] = f"NS: {ns}"
            cid = namespace_to_cid[ns]
        else:
            ntype = data.get("type", "Unknown")
            if ntype not in type_to_cid:
                cid = len(type_to_cid)
                type_to_cid[ntype] = cid
                community_labels[cid] = ntype
            else:
                cid = type_to_cid[ntype]
        communities[cid].append(node_id)
        
    G.graph["hyperedges"] = []
    return dict(communities), community_labels


def build_devops_graph(data_dir: str, providers: list[str] = None):
    graphs = {}
    servers_by_ip = {}  # shared dictionary so bunny can find linode IPs if both run
    
    # 1. Infrastructure (Linode + Bunny)
    infra_requested = not providers or "linode" in providers or "bunny" in providers
    if infra_requested:
        G_infra = nx.DiGraph()
        if not providers or "linode" in providers:
            parse_linode(data_dir, G_infra, servers_by_ip)
        if not providers or "bunny" in providers:
            parse_bunny(data_dir, G_infra, servers_by_ip)
            
        if G_infra.number_of_nodes() > 0 or providers:
            communities, community_labels = _compute_communities(G_infra)
            if providers == ["linode"]:
                graphs["graph_linode"] = (G_infra, communities, community_labels)
            elif providers == ["bunny"]:
                graphs["graph_bunny"] = (G_infra, communities, community_labels)
            else:
                graphs["graph_infrastructure"] = (G_infra, communities, community_labels)

    # 2. Kubernetes
    k8s_requested = not providers or "kubernetes" in providers or "k8s" in providers
    if k8s_requested:
        k8s_dir = os.path.join(data_dir, "kubernetes")
        if os.path.exists(k8s_dir):
            cluster_files = sorted([f for f in os.listdir(k8s_dir) if f.endswith(".json")])
            for filename in cluster_files:
                cluster_name = filename.replace('.json', '')
                graph_name = f"graph_k8s_{cluster_name}"
                
                G_k8s = nx.DiGraph()
                parse_kubernetes(data_dir, G_k8s, servers_by_ip, cluster_filename=filename)
                communities, community_labels = _compute_communities(G_k8s)
                graphs[graph_name] = (G_k8s, communities, community_labels)
                
    return graphs

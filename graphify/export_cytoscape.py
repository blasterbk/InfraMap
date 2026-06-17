import json

def to_cytoscape_html(G, out_path):
    elements = []
    
    # K8s-Cluster parent
    elements.append({"data": {"id": "k8s_cluster", "label": "K8s-Cluster"}})
    
    # Namespaces
    namespaces = set()
    for n, data in G.nodes(data=True):
        ns = data.get("namespace")
        if ns:
            namespaces.add(ns)
            
    for ns in namespaces:
        elements.append({"data": {"id": f"parent_{ns}", "label": f"Namespace: {ns}", "parent": "k8s_cluster"}})
        
    for n, data in G.nodes(data=True):
        if data.get("file_type") in ("K8s Namespace", "K8s Cluster"):
            continue
        
        ns = data.get("namespace")
        parent = f"parent_{ns}" if ns else "k8s_cluster"
        label = data.get("label", n).replace("\\n", "\n")
        
        elements.append({
            "data": {
                "id": n,
                "label": label,
                "parent": parent,
            }
        })
        
    for u, v, data in G.edges(data=True):
        if G.nodes[u].get("file_type") in ("K8s Namespace", "K8s Cluster") or \
           G.nodes[v].get("file_type") in ("K8s Namespace", "K8s Cluster"):
            continue
            
        elements.append({
            "data": {
                "id": f"{u}_{v}",
                "source": u,
                "target": v,
                "label": data.get("relation", "")
            }
        })
        
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>K8s Cluster Flowchart</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/dagre@0.8.5/dist/dagre.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1e1e2f; margin: 0; padding: 0; }}
        #cy {{ width: 100vw; height: 100vh; display: block; }}
        #info {{ position: absolute; top: 10px; left: 10px; color: #aaa; font-size: 12px; pointer-events: none; }}
    </style>
</head>
<body>
    <div id="info">Hold Scroll Wheel / Middle Click or Space to pan. Scroll to zoom.</div>
    <div id="cy"></div>
    <script>
        cytoscape.use( cytoscapeDagre );
        
        var elements = {json.dumps(elements)};
        
        var cy = cytoscape({{
            container: document.getElementById('cy'),
            elements: elements,
            style: [
                {{
                    selector: 'node',
                    style: {{
                        'label': 'data(label)',
                        'text-wrap': 'wrap',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'color': '#fff',
                        'background-color': '#4E79A7',
                        'font-size': '12px',
                        'width': 'label',
                        'height': 'label',
                        'padding': '12px',
                        'shape': 'round-rectangle'
                    }}
                }},
                {{
                    selector: ':parent',
                    style: {{
                        'text-valign': 'top',
                        'text-halign': 'center',
                        'background-color': 'rgba(255, 255, 255, 0.03)',
                        'border-color': '#888',
                        'border-width': 2,
                        'border-style': 'solid',
                        'color': '#ccc',
                        'font-size': '16px',
                        'font-weight': 'bold',
                        'padding': '30px',
                        'shape': 'round-rectangle'
                    }}
                }},
                {{
                    selector: 'node[id="k8s_cluster"]',
                    style: {{
                        'border-color': '#06D6A0',
                        'background-color': 'rgba(6, 214, 160, 0.02)',
                        'color': '#06D6A0',
                        'font-size': '20px',
                        'border-width': 3
                    }}
                }},
                {{
                    selector: 'edge',
                    style: {{
                        'width': 2,
                        'line-color': '#555',
                        'target-arrow-color': '#555',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'label': 'data(label)',
                        'font-size': '10px',
                        'color': '#888',
                        'text-background-color': '#1e1e2f',
                        'text-background-opacity': 1,
                        'text-rotation': 'autorotate'
                    }}
                }}
            ],
            layout: {{
                name: 'dagre',
                rankDir: 'LR',
                nodeSep: 60,
                rankSep: 150
            }},
            wheelSensitivity: 0.2
        }});
    </script>
</body>
</html>"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

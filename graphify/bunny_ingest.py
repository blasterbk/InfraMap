import os
import glob
from collections import defaultdict

def parse_bunny(data_dir, G, servers_by_ip):
    bunny_dir = os.path.join(data_dir, 'Bunny')
    if not os.path.exists(bunny_dir):
        return
        
    bind_files = glob.glob(os.path.join(bunny_dir, '*.bind'))
    
    for bind_file in bind_files:
        filename = os.path.basename(bind_file)
        name_parts = filename.split('.')
        if len(name_parts) >= 4 and name_parts[-1] == 'bind' and '-' in name_parts[-2]:
            main_domain = ".".join(name_parts[:-2])
        else:
            main_domain = ".".join(name_parts[:-1]) # Fallback
            
        G.add_node(main_domain, type="MainDomain", label=f"{main_domain}\n(Main Domain)", file_type="Bunny MainDomain", source_file=f"Zone File: {filename}",
                   shape='icon', icon={'face': '"Font Awesome 6 Free"', 'code': '\uf0ac', 'weight': '900', 'color': '#76B7B2'}, provider=f"bunny_{main_domain}")

        domain_ips = defaultdict(list)
        with open(bind_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(';'):
                    continue
                
                line_parts = line.split()
                if len(line_parts) >= 5 and line_parts[3] == 'A':
                    domain = line_parts[0].rstrip('.')
                    target_ip = line_parts[4]
                    if target_ip not in domain_ips[domain]:
                        domain_ips[domain].append(target_ip)
                        
        all_ips = set()
        for ips in domain_ips.values():
            for ip in ips:
                all_ips.add(ip)
                
        for target_ip in all_ips:
            ip_node_id = f"ip_{target_ip}"
            if target_ip in servers_by_ip:
                server_id = servers_by_ip[target_ip]
                G.add_edge(main_domain, server_id, relation="routes_to_server", color="#76B7B2")
            else:
                G.add_node(ip_node_id, type="IP", label=f"{target_ip}\n(IP Address)",
                           color="#ff4444", file_type="External IP", source_file=f"Zone: {main_domain}",
                           shape='icon', icon={'face': '"Font Awesome 6 Free"', 'code': '\uf233', 'weight': '900', 'color': '#ff4444'},
                           provider=f"bunny_{main_domain}")
                G.add_edge(main_domain, ip_node_id, relation="routes_to_ip", color="#76B7B2")

        for domain, ips in domain_ips.items():
            if domain == main_domain:
                continue
                
            node_type = "SubDomain"
            color = '#59A14F'
            label = f"{domain}\n(Sub Domain)"
            
            G.add_node(domain, 
                       type=node_type, 
                       label=label,
                       color=color,
                       file_type=f"Bunny {node_type}",
                       source_file=f"Zone: {main_domain}",
                       shape='icon', icon={'face': '"Font Awesome 6 Free"', 'code': '\uf0ac', 'weight': '900', 'color': color},
                       provider=f"bunny_{main_domain}")
            
            for target_ip in ips:
                if target_ip in servers_by_ip:
                    server_id = servers_by_ip[target_ip]
                    G.add_edge(server_id, domain, relation="hosts_subdomain", color="#59A14F")
                else:
                    ip_node_id = f"ip_{target_ip}"
                    G.add_edge(ip_node_id, domain, relation="hosts_subdomain", color="#59A14F")


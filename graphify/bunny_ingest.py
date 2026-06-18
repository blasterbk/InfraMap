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
                        
        for domain, ips in domain_ips.items():
            is_main = (domain == main_domain)
            node_type = "MainDomain" if is_main else "SubDomain"
            
            ip_str = ", ".join(ips)
            label_ip_str = ip_str if len(ips) <= 2 else f"{ips[0]}, ... (+{len(ips)-1})"
            
            has_valid_target = False
            for target_ip in ips:
                if target_ip in servers_by_ip:
                    linode_server = servers_by_ip[target_ip]
                    G.add_edge(domain, linode_server, relation="routes_traffic_to")
                    has_valid_target = True
            
            color = '#76B7B2' if is_main else '#59A14F'
            
            is_orphaned = not has_valid_target
            if is_orphaned:
                color = '#ff4444' # RED!
                label = f"⚠️ {domain}\n(ORPHANED)"
            else:
                label = f"{domain}\n({label_ip_str})"
            
            G.add_node(domain, 
                       type=node_type, 
                       ip=ip_str,
                       label=label,
                       color=color, # Override color
                       file_type=f"Bunny {node_type}",
                       source_file=f"Target IPs: {ip_str} | Zone: {main_domain}",
                       shape='icon', icon={'face': '"Font Awesome 6 Free"', 'code': '\uf0ac', 'weight': '900', 'color': color},
                       provider=f"bunny_{main_domain}")
            
            if not is_main:
                G.add_edge(domain, main_domain, relation="subdomain_of")


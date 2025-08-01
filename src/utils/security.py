import ipaddress
import re
import validators
from typing import Dict, Any

class SecurityValidator:
    """Validateur de sécurité pour les arguments des outils réseau"""
    
    BLOCKED_DOMAINS = {
        'localhost', '127.0.0.1', '::1',
        '0.0.0.0', '255.255.255.255'
    }
    
    PRIVATE_RANGES = [
        ipaddress.IPv4Network('10.0.0.0/8'),
        ipaddress.IPv4Network('172.16.0.0/12'),
        ipaddress.IPv4Network('192.168.0.0/16'),
        ipaddress.IPv4Network('127.0.0.0/8')
    ]
    
    def validate_arguments(self, tool_name: str, args: Dict[str, Any]) -> bool:
        """Valide les arguments selon l'outil"""
        try:
            if tool_name == "ping":
                return self._validate_ping_args(args)
            elif tool_name == "traceroute":
                return self._validate_traceroute_args(args)
            elif tool_name == "whois":
                return self._validate_whois_args(args)
            elif tool_name == "nslookup":
                return self._validate_dns_args(args)
            elif tool_name == "nmap":
                return self._validate_nmap_args(args)
            elif tool_name == "curl":
                return self._validate_curl_args(args)
            else:
                return True
                
        except Exception:
            return False
    
    def _validate_ping_args(self, args: Dict[str, Any]) -> bool:
        host = args.get("host", "")
        count = args.get("count", 4)
        timeout = args.get("timeout", 5)
        
        return (
            validate_host(host) and
            1 <= count <= 10 and
            1 <= timeout <= 30
        )
    
    def _validate_traceroute_args(self, args: Dict[str, Any]) -> bool:
        host = args.get("host", "")
        max_hops = args.get("max_hops", 15)
        
        return (
            validate_host(host) and
            1 <= max_hops <= 25
        )
    
    def _validate_whois_args(self, args: Dict[str, Any]) -> bool:
        target = args.get("target", "")
        return validate_domain_or_ip(target)
    
    def _validate_dns_args(self, args: Dict[str, Any]) -> bool:
        domain = args.get("domain", "")
        record_type = args.get("record_type", "A")
        
        valid_types = ["A", "AAAA", "MX", "NS", "CNAME", "TXT", "SOA", "PTR"]
        
        return (
            validate_host(domain) and
            record_type in valid_types
        )
    
    def _validate_nmap_args(self, args: Dict[str, Any]) -> bool:
        host = args.get("host", "")
        ports = args.get("ports", "")
        
        if not validate_host(host):
            return False
        
        if ports:
            return self._validate_port_specification(ports)
        
        return True
    
    def _validate_port_specification(self, ports: str) -> bool:
        """Valide la spécification des ports pour nmap"""
        port_pattern = r'^(\d+(-\d+)?)(,\d+(-\d+)?)*$'
        
        if not re.match(port_pattern, ports):
            return False
        
        for part in ports.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                if not (1 <= start <= 65535 and 1 <= end <= 65535 and start <= end):
                    return False
                if end - start > 1000:
                    return False
            else:
                port = int(part)
                if not (1 <= port <= 65535):
                    return False
        
        return True
    
    def _validate_curl_args(self, args: Dict[str, Any]) -> bool:
        url = args.get("url", "")
        
        if not validators.url(url):
            return False
        
        parsed_url = validators.url(url, public=True)
        return parsed_url is not False

def validate_host(host: str) -> bool:
    """Valide un nom d'hôte ou une adresse IP"""
    if not host or len(host) > 255:
        return False
    
    if host.lower() in SecurityValidator.BLOCKED_DOMAINS:
        return False
    
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass
    
    return validators.domain(host) or validators.url(f"http://{host}")

def validate_domain_or_ip(target: str) -> bool:
    """Valide un domaine ou une IP pour whois"""
    return validate_host(target)
import re
from typing import Dict, Any, List

def parse_ping_output(raw_output: str, host: str) -> Dict[str, Any]:
    """Parse la sortie brute de ping et retourne un dictionnaire structuré"""
    result = {
        "host": host,
        "success": False,
        "packets_sent": 0,
        "packets_received": 0,
        "packet_loss": 100,
        "times": None,
        "individual_pings": [],
        "error": None
    }
    
    try:
        lines = raw_output.strip().split('\n')
        
        # Parse individual ping results
        ping_pattern = r'.*time[=<](\d+(?:\.\d+)?).*ms'
        timeout_pattern = r'(timeout|no answer|request timeout)'
        
        for line in lines:
            if re.search(ping_pattern, line, re.IGNORECASE):
                match = re.search(ping_pattern, line, re.IGNORECASE)
                if match:
                    time_ms = float(match.group(1))
                    result["individual_pings"].append({
                        "success": True,
                        "time": time_ms,
                        "error": None
                    })
            elif re.search(timeout_pattern, line, re.IGNORECASE):
                result["individual_pings"].append({
                    "success": False,
                    "time": None,
                    "error": "timeout"
                })
        
        # Parse summary statistics
        stats_line = None
        for line in lines:
            if 'packets transmitted' in line.lower() or 'packets sent' in line.lower():
                stats_line = line
                break
        
        if stats_line:
            # Pattern for different OS formats
            patterns = [
                r'(\d+) packets transmitted, (\d+) (?:packets )?received, (\d+(?:\.\d+)?)% packet loss',
                r'(\d+) packets sent, (\d+) packets received, (\d+(?:\.\d+)?)% packet loss',
                r'Packets: Sent = (\d+), Received = (\d+), Lost = \d+ \((\d+)% loss\)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, stats_line, re.IGNORECASE)
                if match:
                    result["packets_sent"] = int(match.group(1))
                    result["packets_received"] = int(match.group(2))
                    result["packet_loss"] = float(match.group(3))
                    break
        
        # Parse timing statistics
        time_line = None
        for line in lines:
            if 'min/avg/max' in line.lower() or 'minimum/maximum/average' in line.lower():
                time_line = line
                break
        
        if time_line:
            time_pattern = r'(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)'
            match = re.search(time_pattern, time_line)
            if match:
                result["times"] = {
                    "min": float(match.group(1)),
                    "avg": float(match.group(2)),
                    "max": float(match.group(3))
                }
        
        # Determine success
        result["success"] = result["packets_received"] > 0
        
        if not result["success"] and not result["individual_pings"]:
            result["error"] = "No response received"
            
    except Exception as e:
        result["error"] = f"Failed to parse ping output: {str(e)}"
    
    return result

def parse_traceroute_output(raw_output: str, host: str) -> Dict[str, Any]:
    """Parse la sortie brute de traceroute"""
    result = {
        "host": host,
        "success": False,
        "hops": [],
        "error": None
    }
    
    try:
        lines = raw_output.strip().split('\n')
        
        # Skip header lines
        data_lines = []
        for line in lines:
            if re.match(r'^\s*\d+', line):
                data_lines.append(line)
        
        for line in data_lines:
            hop_match = re.match(r'^\s*(\d+)', line)
            if hop_match:
                hop_num = int(hop_match.group(1))
                
                # Extract IP/hostname and times
                ip_pattern = r'([^\s]+(?:\.[^\s]+)*)\s+\(([^)]+)\)'
                time_pattern = r'(\d+(?:\.\d+)?)\s*ms'
                
                hop_info = {
                    "number": hop_num,
                    "host": None,
                    "ip": None,
                    "times": []
                }
                
                # Try to find hostname and IP
                ip_match = re.search(ip_pattern, line)
                if ip_match:
                    hop_info["host"] = ip_match.group(1)
                    hop_info["ip"] = ip_match.group(2)
                else:
                    # Look for just IP
                    ip_only = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if ip_only:
                        hop_info["ip"] = ip_only.group(1)
                
                # Extract all timing values
                times = re.findall(time_pattern, line)
                hop_info["times"] = [float(t) for t in times]
                
                # Check for timeouts
                if '*' in line:
                    hop_info["timeout"] = True
                
                result["hops"].append(hop_info)
        
        result["success"] = len(result["hops"]) > 0
        
    except Exception as e:
        result["error"] = f"Failed to parse traceroute output: {str(e)}"
    
    return result
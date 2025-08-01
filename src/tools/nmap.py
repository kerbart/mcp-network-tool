import asyncio
import subprocess
import socket
from typing import Dict, Any, List
from ..utils.security import validate_host

class NmapTool:
    """Outil de scan de ports sécurisé avec nmap et fallback Python"""
    
    async def execute(self, args: Dict[str, Any]) -> str:
        host = args.get("host", "").strip()
        ports = args.get("ports", "80,443,22,21,25,53,110,143,993,995")
        scan_type = args.get("scan_type", "connect")
        
        if not validate_host(host):
            raise ValueError(f"Hôte invalide: {host}")
        
        port_list = self._parse_ports(ports)
        if not port_list:
            raise ValueError(f"Spécification de ports invalide: {ports}")
        
        try:
            result = await self._nmap_scan(host, port_list, scan_type)
            if result:
                return result
        except Exception as e:
            pass
        
        return await self._python_port_scan(host, port_list)
    
    def _parse_ports(self, ports: str) -> List[int]:
        """Parse la spécification des ports"""
        port_list = []
        
        try:
            for part in ports.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    if start <= end and start > 0 and end <= 65535:
                        port_list.extend(range(start, min(end + 1, start + 1001)))
                else:
                    port = int(part)
                    if 1 <= port <= 65535:
                        port_list.append(port)
            
            return sorted(list(set(port_list)))[:100]
            
        except ValueError:
            return []
    
    async def _nmap_scan(self, host: str, ports: List[int], scan_type: str) -> str:
        """Utilise nmap pour le scan de ports"""
        port_spec = ",".join(map(str, ports))
        
        cmd = ["nmap", "-p", port_spec]
        
        if scan_type == "syn":
            cmd.append("-sS")
        elif scan_type == "tcp":
            cmd.append("-sT")
        else:
            cmd.append("-sT")
        
        cmd.extend(["-T4", "--max-retries", "2", host])
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            timeout_duration = min(len(ports) * 2 + 30, 300)
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_duration
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode()
                if "command not found" in error_msg.lower():
                    raise Exception("nmap non disponible")
                return f"Erreur nmap: {error_msg}"
            
            return self._format_nmap_output(stdout.decode(), host)
            
        except FileNotFoundError:
            raise Exception("nmap non disponible")
        except asyncio.TimeoutError:
            return f"Timeout lors du scan nmap de {host}"
    
    async def _python_port_scan(self, host: str, ports: List[int]) -> str:
        """Scan de ports basique en Python (fallback)"""
        results = []
        
        for port in ports[:50]:
            try:
                future = asyncio.open_connection(host, port)
                reader, writer = await asyncio.wait_for(future, timeout=3)
                writer.close()
                await writer.wait_closed()
                results.append((port, "open"))
            except (ConnectionRefusedError, OSError, asyncio.TimeoutError):
                results.append((port, "closed"))
            except Exception:
                results.append((port, "filtered"))
        
        return self._format_python_scan_results(host, results)
    
    def _format_nmap_output(self, raw_output: str, host: str) -> str:
        """Formate la sortie nmap"""
        lines = raw_output.strip().split('\n')
        
        output = [f"🔍 Scan de ports pour {host}:"]
        
        open_ports = []
        closed_count = 0
        filtered_count = 0
        
        in_port_section = False
        
        for line in lines:
            line = line.strip()
            
            if "PORT" in line and "STATE" in line:
                in_port_section = True
                continue
            
            if in_port_section and line:
                if "/" in line and ("open" in line or "closed" in line or "filtered" in line):
                    parts = line.split()
                    if len(parts) >= 2:
                        port_info = parts[0]
                        state = parts[1]
                        service = parts[2] if len(parts) > 2 else "unknown"
                        
                        if state == "open":
                            open_ports.append(f"   ✅ {port_info} - {service}")
                        elif state == "closed":
                            closed_count += 1
                        elif state == "filtered":
                            filtered_count += 1
        
        if open_ports:
            output.append("📂 Ports ouverts:")
            output.extend(open_ports)
        else:
            output.append("❌ Aucun port ouvert détecté")
        
        if closed_count > 0:
            output.append(f"🔒 {closed_count} ports fermés")
        
        if filtered_count > 0:
            output.append(f"🛡️  {filtered_count} ports filtrés")
        
        return "\n".join(output)
    
    def _format_python_scan_results(self, host: str, results: List[tuple]) -> str:
        """Formate les résultats du scan Python"""
        output = [f"🔍 Scan de ports pour {host} (scan basique):"]
        
        open_ports = []
        closed_count = 0
        filtered_count = 0
        
        for port, state in results:
            if state == "open":
                service = self._get_service_name(port)
                open_ports.append(f"   ✅ {port}/tcp - {service}")
            elif state == "closed":
                closed_count += 1
            else:
                filtered_count += 1
        
        if open_ports:
            output.append("📂 Ports ouverts:")
            output.extend(open_ports)
        else:
            output.append("❌ Aucun port ouvert détecté")
        
        if closed_count > 0:
            output.append(f"🔒 {closed_count} ports fermés")
        
        if filtered_count > 0:
            output.append(f"🛡️  {filtered_count} ports filtrés")
        
        return "\n".join(output)
    
    def _get_service_name(self, port: int) -> str:
        """Retourne le nom de service connu pour un port"""
        common_ports = {
            21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
            80: "http", 110: "pop3", 143: "imap", 443: "https", 993: "imaps",
            995: "pop3s", 3389: "rdp", 5432: "postgresql", 3306: "mysql"
        }
        return common_ports.get(port, "unknown")
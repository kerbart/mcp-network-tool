import asyncio
import subprocess
import psutil
from typing import Dict, Any, List
import socket

class NetstatTool:
    """Outil netstat avec psutil et fallback système"""
    
    async def execute(self, args: Dict[str, Any]) -> str:
        protocol = args.get("protocol", "all").lower()
        state = args.get("state", "all").lower()
        
        try:
            result = await self._psutil_netstat(protocol, state)
            if result:
                return result
        except Exception as e:
            pass
        
        return await self._system_netstat(protocol, state)
    
    async def _psutil_netstat(self, protocol: str, state: str) -> str:
        """Utilise psutil pour obtenir les connexions réseau"""
        loop = asyncio.get_event_loop()
        
        def get_connections():
            kind = 'inet'
            if protocol == "tcp":
                kind = 'tcp'
            elif protocol == "udp":
                kind = 'udp'
            
            connections = psutil.net_connections(kind=kind)
            return connections
        
        try:
            connections = await loop.run_in_executor(None, get_connections)
            return self._format_psutil_connections(connections, protocol, state)
            
        except Exception as e:
            raise Exception(f"Erreur psutil: {str(e)}")
    
    async def _system_netstat(self, protocol: str, state: str) -> str:
        """Utilise netstat système en fallback"""
        cmd = ["netstat", "-n"]
        
        if protocol == "tcp":
            cmd.append("-t")
        elif protocol == "udp":
            cmd.append("-u")
        else:
            cmd.extend(["-t", "-u"])
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=30
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode()
                if "command not found" in error_msg.lower():
                    return "Commande netstat non disponible sur ce système"
                return f"Erreur netstat: {error_msg}"
            
            return self._format_netstat_output(stdout.decode(), protocol, state)
            
        except FileNotFoundError:
            return "Commande netstat non disponible sur ce système"
        except asyncio.TimeoutError:
            return "Timeout lors de l'exécution de netstat"
    
    def _format_psutil_connections(self, connections: List, protocol: str, state: str) -> str:
        """Formate les connexions psutil"""
        output = [f"🌐 Connexions réseau actives:"]
        
        tcp_connections = []
        udp_connections = []
        listening_count = 0
        established_count = 0
        
        for conn in connections:
            conn_type = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
            local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "unknown"
            remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "*:*"
            conn_status = conn.status if hasattr(conn, 'status') else "unknown"
            
            # Filtrage par état
            if state != "all":
                if state == "listening" and conn_status != "LISTEN":
                    continue
                elif state == "established" and conn_status != "ESTABLISHED":
                    continue
                elif state == "time_wait" and conn_status != "TIME_WAIT":
                    continue
            
            # Compteurs
            if conn_status == "LISTEN":
                listening_count += 1
            elif conn_status == "ESTABLISHED":
                established_count += 1
            
            conn_info = {
                "type": conn_type,
                "local": local_addr,
                "remote": remote_addr,
                "status": conn_status,
                "pid": conn.pid if hasattr(conn, 'pid') else None
            }
            
            if conn_type == "TCP":
                tcp_connections.append(conn_info)
            else:
                udp_connections.append(conn_info)
        
        # Affichage selon le protocole demandé
        if protocol == "all" or protocol == "tcp":
            if tcp_connections:
                output.append(f"📡 Connexions TCP ({len(tcp_connections)}):")
                for conn in tcp_connections[:20]:
                    status_icon = self._get_status_icon(conn["status"])
                    pid_info = f" (PID: {conn['pid']})" if conn['pid'] else ""
                    output.append(f"   {status_icon} {conn['local']} -> {conn['remote']} [{conn['status']}]{pid_info}")
        
        if protocol == "all" or protocol == "udp":
            if udp_connections:
                output.append(f"📻 Connexions UDP ({len(udp_connections)}):")
                for conn in udp_connections[:20]:
                    pid_info = f" (PID: {conn['pid']})" if conn['pid'] else ""
                    output.append(f"   📡 {conn['local']} -> {conn['remote']}{pid_info}")
        
        # Résumé
        output.append("📊 Résumé:")
        output.append(f"   🎧 En écoute: {listening_count}")
        output.append(f"   🔗 Établies: {established_count}")
        output.append(f"   📈 Total: {len(connections)}")
        
        return "\n".join(output)
    
    def _format_netstat_output(self, raw_output: str, protocol: str, state: str) -> str:
        """Formate la sortie netstat brute"""
        lines = raw_output.strip().split('\n')
        
        output = [f"🌐 Connexions réseau actives:"]
        
        tcp_connections = []
        udp_connections = []
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('Active') or line.startswith('Proto'):
                continue
            
            parts = line.split()
            if len(parts) >= 4:
                proto = parts[0].upper()
                local_addr = parts[3] if len(parts) > 3 else parts[1]
                remote_addr = parts[4] if len(parts) > 4 else "*:*"
                conn_status = parts[5] if len(parts) > 5 else "unknown"
                
                # Filtrage par état
                if state != "all":
                    if state == "listening" and conn_status != "LISTEN":
                        continue
                    elif state == "established" and conn_status != "ESTABLISHED":
                        continue
                    elif state == "time_wait" and conn_status != "TIME_WAIT":
                        continue
                
                conn_info = {
                    "type": proto,
                    "local": local_addr,
                    "remote": remote_addr,
                    "status": conn_status
                }
                
                if proto == "TCP":
                    tcp_connections.append(conn_info)
                elif proto == "UDP":
                    udp_connections.append(conn_info)
        
        # Affichage
        if protocol == "all" or protocol == "tcp":
            if tcp_connections:
                output.append(f"📡 Connexions TCP ({len(tcp_connections)}):")
                for conn in tcp_connections[:20]:
                    status_icon = self._get_status_icon(conn["status"])
                    output.append(f"   {status_icon} {conn['local']} -> {conn['remote']} [{conn['status']}]")
        
        if protocol == "all" or protocol == "udp":
            if udp_connections:
                output.append(f"📻 Connexions UDP ({len(udp_connections)}):")
                for conn in udp_connections[:20]:
                    output.append(f"   📡 {conn['local']} -> {conn['remote']}")
        
        return "\n".join(output)
    
    def _get_status_icon(self, status: str) -> str:
        """Retourne une icône selon le statut de connexion"""
        status_icons = {
            "ESTABLISHED": "🔗",
            "LISTEN": "🎧",
            "TIME_WAIT": "⏳",
            "CLOSE_WAIT": "⏸️",
            "FIN_WAIT1": "🔚",
            "FIN_WAIT2": "🔚",
            "SYN_SENT": "📤",
            "SYN_RECV": "📥"
        }
        return status_icons.get(status, "📡")
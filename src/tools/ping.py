import asyncio
import subprocess
import json
import re
from typing import Dict, Any
from ..utils.security import validate_host
from ..utils.parsers import parse_ping_output

class PingTool:
    """Outil de ping avec parsing intelligent des résultats"""
    
    async def execute(self, args: Dict[str, Any]) -> str:
        host = args.get("host", "").strip()
        count = min(args.get("count", 4), 10)
        timeout = min(args.get("timeout", 5), 30)
        
        if not validate_host(host):
            raise ValueError(f"Hôte invalide: {host}")
        
        try:
            cmd = self._build_ping_command(host, count, timeout)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout + 10
            )
            
            if process.returncode != 0 and stderr:
                return f"Erreur ping: {stderr.decode()}"
            
            raw_output = stdout.decode()
            parsed_results = parse_ping_output(raw_output, host)
            
            return self._format_ping_results(parsed_results)
            
        except asyncio.TimeoutError:
            return f"Timeout lors du ping vers {host}"
        except Exception as e:
            return f"Erreur lors du ping: {str(e)}"
    
    def _build_ping_command(self, host: str, count: int, timeout: int) -> list:
        """Construit la commande ping selon l'OS"""
        import platform
        
        if platform.system().lower() == "windows":
            return ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
        else:
            return ["ping", "-c", str(count), "-W", str(timeout), host]
    
    def _format_ping_results(self, results: Dict[str, Any]) -> str:
        """Formate les résultats de ping de manière lisible"""
        if not results.get("success"):
            return f"❌ Ping échoué vers {results.get('host', 'inconnu')}: {results.get('error', 'Erreur inconnue')}"
        
        output = [
            f"🏓 Ping vers {results['host']} - Résultats:",
            f"📊 Paquets: {results['packets_sent']} envoyés, {results['packets_received']} reçus, {results['packet_loss']}% de perte",
        ]
        
        if results.get('times'):
            times = results['times']
            output.extend([
                f"⏱️  Temps de réponse:",
                f"   • Minimum: {times['min']}ms",
                f"   • Maximum: {times['max']}ms", 
                f"   • Moyenne: {times['avg']}ms"
            ])
        
        if results.get('individual_pings'):
            output.append("📋 Détail des pings:")
            for i, ping in enumerate(results['individual_pings'][:5], 1):
                status = "✅" if ping['success'] else "❌"
                output.append(f"   {i}. {status} {ping['time']}ms" + (f" - {ping['error']}" if not ping['success'] else ""))
        
        return "\n".join(output)
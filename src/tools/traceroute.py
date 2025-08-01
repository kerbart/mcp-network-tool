import asyncio
import subprocess
import platform
from typing import Dict, Any
from ..utils.security import validate_host
from ..utils.parsers import parse_traceroute_output

class TracerouteTool:
    """Outil de traceroute avec parsing intelligent des résultats"""
    
    async def execute(self, args: Dict[str, Any]) -> str:
        host = args.get("host", "").strip()
        max_hops = min(args.get("max_hops", 15), 25)
        
        if not validate_host(host):
            raise ValueError(f"Hôte invalide: {host}")
        
        try:
            cmd = self._build_traceroute_command(host, max_hops)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            timeout_duration = max_hops * 5 + 30
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_duration
            )
            
            if process.returncode != 0 and stderr:
                error_msg = stderr.decode()
                if "command not found" in error_msg.lower() or "not recognized" in error_msg.lower():
                    return f"Commande traceroute non disponible sur ce système"
                return f"Erreur traceroute: {error_msg}"
            
            raw_output = stdout.decode()
            parsed_results = parse_traceroute_output(raw_output, host)
            
            return self._format_traceroute_results(parsed_results)
            
        except asyncio.TimeoutError:
            return f"Timeout lors du traceroute vers {host}"
        except Exception as e:
            return f"Erreur lors du traceroute: {str(e)}"
    
    def _build_traceroute_command(self, host: str, max_hops: int) -> list:
        """Construit la commande traceroute selon l'OS"""
        system = platform.system().lower()
        
        if system == "windows":
            return ["tracert", "-h", str(max_hops), host]
        elif system == "darwin":
            return ["traceroute", "-m", str(max_hops), host]
        else:
            return ["traceroute", "-m", str(max_hops), host]
    
    def _format_traceroute_results(self, results: Dict[str, Any]) -> str:
        """Formate les résultats de traceroute de manière lisible"""
        if not results.get("success"):
            return f"❌ Traceroute échoué vers {results.get('host', 'inconnu')}: {results.get('error', 'Erreur inconnue')}"
        
        output = [
            f"🛣️  Traceroute vers {results['host']}:",
            ""
        ]
        
        if not results.get("hops"):
            return f"❌ Aucun saut trouvé vers {results['host']}"
        
        for hop in results["hops"]:
            hop_line = f"{hop['number']:2d}. "
            
            if hop.get("timeout"):
                hop_line += "* * * (timeout)"
            else:
                if hop.get("host"):
                    hop_line += f"{hop['host']} "
                
                if hop.get("ip"):
                    hop_line += f"({hop['ip']}) "
                
                if hop.get("times") and hop["times"]:
                    times_str = " ".join([f"{t:.1f}ms" for t in hop["times"]])
                    hop_line += times_str
                else:
                    hop_line += "* * *"
            
            output.append(hop_line)
        
        return "\n".join(output)
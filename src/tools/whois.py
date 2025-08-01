import asyncio
import subprocess
import whois as python_whois
from typing import Dict, Any
from ..utils.security import validate_domain_or_ip

class WhoisTool:
    """Outil whois avec fallback et parsing amélioré"""
    
    async def execute(self, args: Dict[str, Any]) -> str:
        target = args.get("target", "").strip()
        
        if not validate_domain_or_ip(target):
            raise ValueError(f"Cible invalide: {target}")
        
        try:
            try:
                result = await self._whois_python(target)
                if result:
                    return result
            except:
                pass
            
            return await self._whois_system(target)
            
        except Exception as e:
            return f"Erreur lors du whois: {str(e)}"
    
    async def _whois_python(self, target: str) -> str:
        """Utilise python-whois"""
        loop = asyncio.get_event_loop()
        
        def run_whois():
            return python_whois.whois(target)
        
        whois_data = await loop.run_in_executor(None, run_whois)
        return self._format_whois_data(whois_data, target)
    
    async def _whois_system(self, target: str) -> str:
        """Utilise la commande whois système"""
        try:
            process = await asyncio.create_subprocess_exec(
                "whois", target,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30
            )
            
            if process.returncode != 0:
                return f"Erreur whois: {stderr.decode()}"
            
            return self._format_raw_whois(stdout.decode(), target)
            
        except FileNotFoundError:
            return "Commande whois non disponible sur ce système"
        except asyncio.TimeoutError:
            return f"Timeout lors du whois pour {target}"
    
    def _format_whois_data(self, data: Any, target: str) -> str:
        """Formate les données whois structurées"""
        if not data:
            return f"Aucune donnée whois trouvée pour {target}"
        
        output = [f"🔍 Informations whois pour {target}:"]
        
        if hasattr(data, 'domain_name') and data.domain_name:
            output.append(f"📝 Domaine: {data.domain_name}")
        
        if hasattr(data, 'registrar') and data.registrar:
            output.append(f"🏢 Registrar: {data.registrar}")
        
        if hasattr(data, 'creation_date') and data.creation_date:
            output.append(f"📅 Création: {data.creation_date}")
        
        if hasattr(data, 'expiration_date') and data.expiration_date:
            output.append(f"⏰ Expiration: {data.expiration_date}")
        
        if hasattr(data, 'name_servers') and data.name_servers:
            output.append(f"🌐 Serveurs DNS: {', '.join(data.name_servers[:3])}")
        
        return "\n".join(output)
    
    def _format_raw_whois(self, raw_data: str, target: str) -> str:
        """Formate les données whois brutes"""
        lines = raw_data.strip().split('\n')
        important_lines = []
        
        keywords = [
            'domain name', 'registrar', 'creation date', 'expiry date',
            'name server', 'admin', 'tech', 'status', 'updated date'
        ]
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in keywords) and not line.startswith('#'):
                important_lines.append(line)
        
        if not important_lines:
            return f"Données whois brutes pour {target}:\n{raw_data[:1000]}..."
        
        output = [f"🔍 Informations whois pour {target}:"]
        output.extend(important_lines[:20])
        
        return "\n".join(output)
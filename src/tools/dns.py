import asyncio
import subprocess
import dns.resolver
import dns.exception
from typing import Dict, Any, List
from ..utils.security import validate_host

class DNSTool:
    """Outil DNS pour nslookup et dig avec dnspython"""
    
    async def execute(self, args: Dict[str, Any]) -> str:
        domain = args.get("domain", "").strip()
        record_type = args.get("record_type", "A").upper()
        
        if not validate_host(domain):
            raise ValueError(f"Domaine invalide: {domain}")
        
        try:
            result = await self._dns_lookup_python(domain, record_type)
            if result:
                return result
        except Exception as e:
            pass
        
        try:
            return await self._dns_lookup_system(domain, record_type)
        except Exception as e:
            return f"Erreur lors de la résolution DNS: {str(e)}"
    
    async def _dns_lookup_python(self, domain: str, record_type: str) -> str:
        """Utilise dnspython pour la résolution DNS"""
        loop = asyncio.get_event_loop()
        
        def perform_lookup():
            resolver = dns.resolver.Resolver()
            resolver.timeout = 10
            resolver.lifetime = 30
            
            try:
                answers = resolver.resolve(domain, record_type)
                return list(answers)
            except dns.resolver.NXDOMAIN:
                raise Exception(f"Domaine {domain} non trouvé")
            except dns.resolver.NoAnswer:
                raise Exception(f"Aucune réponse pour {record_type} {domain}")
            except dns.resolver.Timeout:
                raise Exception(f"Timeout lors de la résolution de {domain}")
            except Exception as e:
                raise Exception(f"Erreur DNS: {str(e)}")
        
        try:
            answers = await loop.run_in_executor(None, perform_lookup)
            return self._format_dns_results(domain, record_type, answers)
        except Exception as e:
            raise e
    
    async def _dns_lookup_system(self, domain: str, record_type: str) -> str:
        """Utilise nslookup système en fallback"""
        try:
            process = await asyncio.create_subprocess_exec(
                "nslookup", "-type=" + record_type, domain,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30
            )
            
            if process.returncode != 0:
                return f"Erreur nslookup: {stderr.decode()}"
            
            return self._format_raw_dns_output(stdout.decode(), domain, record_type)
            
        except FileNotFoundError:
            return "Commande nslookup non disponible sur ce système"
        except asyncio.TimeoutError:
            return f"Timeout lors de la résolution DNS pour {domain}"
    
    def _format_dns_results(self, domain: str, record_type: str, answers: List) -> str:
        """Formate les résultats DNS structurés"""
        output = [f"🌐 Résolution DNS pour {domain} (type {record_type}):"]
        
        if not answers:
            return f"❌ Aucun enregistrement {record_type} trouvé pour {domain}"
        
        for answer in answers:
            if record_type == "A":
                output.append(f"📍 Adresse IPv4: {answer.address}")
            
            elif record_type == "AAAA":
                output.append(f"📍 Adresse IPv6: {answer.address}")
            
            elif record_type == "MX":
                output.append(f"📧 Serveur mail: {answer.exchange} (priorité: {answer.preference})")
            
            elif record_type == "NS":
                output.append(f"🌐 Serveur de noms: {answer.target}")
            
            elif record_type == "CNAME":
                output.append(f"🔗 Alias: {answer.target}")
            
            elif record_type == "TXT":
                txt_data = " ".join([part.decode() if isinstance(part, bytes) else str(part) for part in answer.strings])
                output.append(f"📝 Texte: {txt_data}")
            
            elif record_type == "SOA":
                output.append(f"⚙️  SOA: {answer.mname} {answer.rname}")
                output.append(f"   Serial: {answer.serial}")
                output.append(f"   Refresh: {answer.refresh}s")
                output.append(f"   Retry: {answer.retry}s")
                output.append(f"   Expire: {answer.expire}s")
                output.append(f"   Minimum: {answer.minimum}s")
            
            else:
                output.append(f"📋 {record_type}: {str(answer)}")
        
        return "\n".join(output)
    
    def _format_raw_dns_output(self, raw_output: str, domain: str, record_type: str) -> str:
        """Formate la sortie brute de nslookup"""
        lines = raw_output.strip().split('\n')
        
        output = [f"🌐 Résolution DNS pour {domain} (type {record_type}):"]
        
        in_answer_section = False
        for line in lines:
            line = line.strip()
            
            if "Non-authoritative answer:" in line:
                in_answer_section = True
                continue
            
            if in_answer_section and line and not line.startswith("***"):
                if "Address:" in line or "AAAA address:" in line:
                    ip = line.split("Address:")[-1].strip()
                    output.append(f"📍 Adresse IP: {ip}")
                elif "mail exchanger" in line:
                    output.append(f"📧 {line}")
                elif "nameserver" in line:
                    output.append(f"🌐 {line}")
                elif line and not line.startswith("Name:"):
                    output.append(f"📋 {line}")
        
        if len(output) == 1:
            output.append("❌ Aucun résultat trouvé")
        
        return "\n".join(output)
import asyncio
import subprocess
import requests
from typing import Dict, Any
from ..utils.security import SecurityValidator

class CurlTool:
    """Outil HTTP avec curl et fallback requests"""
    
    async def execute(self, args: Dict[str, Any]) -> str:
        url = args.get("url", "").strip()
        method = args.get("method", "GET").upper()
        include_headers = args.get("headers", True)
        follow_redirects = args.get("follow_redirects", True)
        
        validator = SecurityValidator()
        if not validator._validate_curl_args(args):
            raise ValueError(f"URL invalide ou non autorisée: {url}")
        
        try:
            result = await self._curl_command(url, method, include_headers, follow_redirects)
            if result:
                return result
        except Exception as e:
            pass
        
        return await self._requests_fallback(url, method, include_headers, follow_redirects)
    
    async def _curl_command(self, url: str, method: str, include_headers: bool, follow_redirects: bool) -> str:
        """Utilise curl pour effectuer la requête HTTP"""
        cmd = ["curl", "-s"]
        
        if include_headers:
            cmd.append("-i")
        
        if follow_redirects:
            cmd.append("-L")
        
        cmd.extend(["-X", method])
        cmd.extend(["--max-time", "30"])
        cmd.extend(["--connect-timeout", "10"])
        cmd.extend(["-w", "\\n\\nHTTP Stats:\\nTime Total: %{time_total}s\\nTime Connect: %{time_connect}s\\nTime SSL: %{time_appconnect}s\\nSize Downloaded: %{size_download} bytes\\nSpeed: %{speed_download} bytes/s\\nHTTP Code: %{http_code}"])
        cmd.append(url)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=35
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode()
                if "command not found" in error_msg.lower():
                    raise Exception("curl non disponible")
                return f"Erreur curl: {error_msg}"
            
            return self._format_curl_output(stdout.decode(), url, method)
            
        except FileNotFoundError:
            raise Exception("curl non disponible")
        except asyncio.TimeoutError:
            return f"Timeout lors de la requête curl vers {url}"
    
    async def _requests_fallback(self, url: str, method: str, include_headers: bool, follow_redirects: bool) -> str:
        """Utilise requests en fallback"""
        loop = asyncio.get_event_loop()
        
        def make_request():
            session = requests.Session()
            session.max_redirects = 5 if follow_redirects else 0
            
            headers = {
                'User-Agent': 'MCP-Network-Tools/1.0'
            }
            
            response = session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=(10, 30),
                allow_redirects=follow_redirects,
                stream=False
            )
            
            return response
        
        try:
            response = await loop.run_in_executor(None, make_request)
            return self._format_requests_output(response, url, method, include_headers)
            
        except Exception as e:
            return f"Erreur lors de la requête HTTP: {str(e)}"
    
    def _format_curl_output(self, raw_output: str, url: str, method: str) -> str:
        """Formate la sortie curl"""
        parts = raw_output.split("\\n\\nHTTP Stats:")
        
        response_part = parts[0] if parts else raw_output
        stats_part = parts[1] if len(parts) > 1 else ""
        
        output = [f"🌐 Requête {method} vers {url}:"]
        
        if response_part:
            lines = response_part.split('\n')
            
            headers_section = []
            body_section = []
            in_body = False
            
            for line in lines:
                if not in_body and (line.startswith('HTTP/') or ':' in line):
                    headers_section.append(line)
                elif line == '' and not in_body:
                    in_body = True
                elif in_body:
                    body_section.append(line)
            
            if headers_section:
                output.append("📋 Headers de réponse:")
                for header in headers_section[:10]:
                    if header.strip():
                        output.append(f"   {header}")
            
            if body_section:
                body_content = '\n'.join(body_section)
                if len(body_content) > 1000:
                    body_content = body_content[:1000] + "..."
                
                output.append("📄 Contenu de la réponse:")
                output.append(body_content)
        
        if stats_part:
            output.append("📊 Statistiques:")
            stats_lines = stats_part.split('\\n')
            for stat in stats_lines:
                if stat.strip():
                    output.append(f"   {stat}")
        
        return "\n".join(output)
    
    def _format_requests_output(self, response, url: str, method: str, include_headers: bool) -> str:
        """Formate la sortie requests"""
        output = [f"🌐 Requête {method} vers {url}:"]
        
        output.append(f"📊 Code de statut: {response.status_code} {response.reason}")
        
        if include_headers and response.headers:
            output.append("📋 Headers de réponse:")
            for key, value in list(response.headers.items())[:10]:
                output.append(f"   {key}: {value}")
        
        try:
            content = response.text
            if len(content) > 1000:
                content = content[:1000] + "..."
            
            output.append("📄 Contenu de la réponse:")
            output.append(content)
            
        except Exception:
            output.append("📄 Contenu binaire ou non décodable")
        
        output.append("📊 Statistiques:")
        output.append(f"   Taille: {len(response.content)} bytes")
        output.append(f"   URL finale: {response.url}")
        
        if hasattr(response, 'elapsed'):
            output.append(f"   Temps de réponse: {response.elapsed.total_seconds():.3f}s")
        
        return "\n".join(output)
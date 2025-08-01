#!/usr/bin/env python3
"""
Serveur MCP Network Tools avec support HTTP et stdio
Compatible avec Claude Desktop et Claude Code via transport HTTP
"""

import asyncio
import argparse
import logging
import sys
import os
from typing import Any, Sequence

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
    ServerCapabilities
)

# Imports pour HTTP
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    import uvicorn
    from pydantic import BaseModel
    import json
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False

from src.tools.ping import PingTool
from src.tools.traceroute import TracerouteTool
from src.tools.whois import WhoisTool
from src.tools.dns import DNSTool
from src.tools.nmap import NmapTool
from src.tools.curl import CurlTool
from src.tools.netstat import NetstatTool
from src.utils.security import SecurityValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-network-tools")

# Créer le serveur MCP
server = Server("network-tools")

# Initialiser les outils
tools = {
    "ping": PingTool(),
    "traceroute": TracerouteTool(),
    "whois": WhoisTool(),
    "nslookup": DNSTool(),
    "dig": DNSTool(),
    "nmap": NmapTool(),
    "curl": CurlTool(),
    "netstat": NetstatTool()
}

security_validator = SecurityValidator()

# Modèles Pydantic pour l'API HTTP
class ToolRequest(BaseModel):
    arguments: dict = {}

class ToolResponse(BaseModel):
    success: bool
    result: str | None = None
    error: str | None = None

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Liste tous les outils réseau disponibles"""
    return [
        Tool(
            name="ping",
            description="Test de connectivité et mesure de latence vers un hôte",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Nom d'hôte ou adresse IP à pinger"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Nombre de paquets à envoyer (défaut: 4, max: 10)",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 4
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout en secondes (défaut: 5, max: 30)",
                        "minimum": 1,
                        "maximum": 30,
                        "default": 5
                    }
                },
                "required": ["host"]
            }
        ),
        Tool(
            name="traceroute",
            description="Trace la route réseau vers un hôte de destination",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Nom d'hôte ou adresse IP de destination"
                    },
                    "max_hops": {
                        "type": "integer",
                        "description": "Nombre maximum de sauts (défaut: 15, max: 25)",
                        "minimum": 1,
                        "maximum": 25,
                        "default": 15
                    }
                },
                "required": ["host"]
            }
        ),
        Tool(
            name="whois",
            description="Récupère les informations whois d'un domaine ou d'une IP",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Nom de domaine ou adresse IP"
                    }
                },
                "required": ["target"]
            }
        ),
        Tool(
            name="nslookup",
            description="Effectue des requêtes DNS pour un domaine",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Nom de domaine à résoudre"
                    },
                    "record_type": {
                        "type": "string",
                        "description": "Type d'enregistrement DNS (A, AAAA, MX, NS, etc.)",
                        "enum": ["A", "AAAA", "MX", "NS", "CNAME", "TXT", "SOA", "PTR"],
                        "default": "A"
                    }
                },
                "required": ["domain"]
            }
        ),
        Tool(
            name="nmap",
            description="Scan de ports basique et sécurisé",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Hôte à scanner"
                    },
                    "ports": {
                        "type": "string",
                        "description": "Ports à scanner (ex: '80,443,22' ou '1-1000')",
                        "default": "80,443,22,21,25,53,110,143,993,995"
                    },
                    "scan_type": {
                        "type": "string",
                        "description": "Type de scan",
                        "enum": ["tcp", "syn", "connect"],
                        "default": "connect"
                    }
                },
                "required": ["host"]
            }
        ),
        Tool(
            name="curl",
            description="Effectue des requêtes HTTP avec informations détaillées",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL à interroger"
                    },
                    "method": {
                        "type": "string",
                        "description": "Méthode HTTP",
                        "enum": ["GET", "POST", "HEAD", "OPTIONS"],
                        "default": "GET"
                    },
                    "headers": {
                        "type": "boolean",
                        "description": "Inclure les headers de réponse",
                        "default": True
                    },
                    "follow_redirects": {
                        "type": "boolean",
                        "description": "Suivre les redirections",
                        "default": True
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="netstat",
            description="Affiche les connexions réseau actives",
            inputSchema={
                "type": "object",
                "properties": {
                    "protocol": {
                        "type": "string",
                        "description": "Protocole à filtrer",
                        "enum": ["tcp", "udp", "all"],
                        "default": "all"
                    },
                    "state": {
                        "type": "string",
                        "description": "État des connexions à afficher",
                        "enum": ["all", "established", "listening", "time_wait"],
                        "default": "all"
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> Sequence[TextContent]:
    """Exécute l'outil réseau demandé"""
    try:
        if name not in tools:
            return [TextContent(
                type="text",
                text=f"Outil inconnu: {name}"
            )]

        if not security_validator.validate_arguments(name, arguments or {}):
            return [TextContent(
                type="text",
                text="Arguments invalides ou potentiellement dangereux"
            )]

        tool = tools[name]
        result = await tool.execute(arguments or {})
        
        return [TextContent(
            type="text",
            text=result
        )]
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Erreur: {str(e)}"
        )]

def create_http_app() -> FastAPI:
    """Crée l'application FastAPI pour le serveur HTTP MCP"""
    app = FastAPI(
        title="MCP Network Tools Server",
        description="Serveur MCP pour outils de diagnostic réseau",
        version="1.0.0"
    )
    
    # MCP Protocol endpoints
    @app.post("/")
    async def handle_mcp_request(request_data: dict):
        """Handle MCP protocol requests"""
        try:
            method = request_data.get("method")
            params = request_data.get("params", {})
            request_id = request_data.get("id")
            
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {
                                "listChanged": False
                            }
                        },
                        "serverInfo": {
                            "name": "network-tools",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "tools/list":
                tools_list = await handle_list_tools()
                mcp_tools = []
                for tool in tools_list:
                    mcp_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    })
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": mcp_tools
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name not in tools:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }
                
                if not security_validator.validate_arguments(tool_name, arguments):
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "Invalid or potentially dangerous arguments"
                        }
                    }
                
                try:
                    tool = tools[tool_name]
                    result = await tool.execute(arguments)
                    
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": result
                                }
                            ]
                        }
                    }
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": str(e)
                        }
                    }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"MCP request handling error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32603,
                    "message": "Internal error"
                }
            }
    
    @app.get("/")
    async def root():
        return JSONResponse({
            "name": "MCP Network Tools Server",
            "version": "1.0.0",
            "description": "Serveur MCP HTTP pour outils de diagnostic réseau",
            "protocol": "MCP over HTTP",
            "endpoints": {
                "POST /": "MCP protocol endpoint",
                "GET /": "Server information",
                "GET /health": "Health check",
                "GET /tools": "List all available tools",
                "POST /tools/{tool_name}": "Execute a tool",
            }
        })
    
    
    @app.get("/tools")
    async def list_tools_http():
        """Liste tous les outils disponibles via HTTP"""
        try:
            tools_list = await handle_list_tools()
            tools_info = {}
            
            for tool in tools_list:
                tools_info[tool.name] = {
                    "description": tool.description,
                    "schema": tool.inputSchema
                }
            
            return JSONResponse({
                "success": True,
                "tools": tools_info
            })
        except Exception as e:
            logger.error(f"Erreur lors de la liste des outils: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/tools/{tool_name}")
    async def execute_tool_http(tool_name: str, request: ToolRequest):
        """Exécute un outil réseau via HTTP"""
        try:
            if tool_name not in tools:
                raise HTTPException(status_code=404, detail=f"Outil inconnu: {tool_name}")
            
            # Validation de sécurité
            if not security_validator.validate_arguments(tool_name, request.arguments):
                raise HTTPException(status_code=400, detail="Arguments invalides ou potentiellement dangereux")
            
            # Exécuter l'outil
            tool = tools[tool_name]
            result = await tool.execute(request.arguments)
            
            return JSONResponse({
                "success": True,
                "tool": tool_name,
                "result": result
            })
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de {tool_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/health")
    async def health_check():
        """Vérification de santé du serveur"""
        return JSONResponse({
            "status": "healthy",
            "server": "mcp-network-tools-http",
            "version": "1.0.0"
        })
    
    
    return app

async def main():
    """Point d'entrée principal du serveur MCP"""
    parser = argparse.ArgumentParser(description="Network Tools MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio",
                       help="Transport à utiliser (stdio ou http)")
    parser.add_argument("--host", default="0.0.0.0",
                       help="Adresse d'écoute pour le mode HTTP")
    parser.add_argument("--port", type=int, default=8000,
                       help="Port d'écoute pour le mode HTTP")
    
    args = parser.parse_args()
    
    if args.transport == "stdio":
        # Mode stdio (compatible avec claude mcp add)
        logger.info("Démarrage du serveur MCP Network Tools en mode stdio...")
        try:
            async with stdio_server() as (read_stream, write_stream):
                logger.info("Serveur MCP initialisé avec succès")
                await server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="network-tools",
                        server_version="1.0.0",
                        capabilities=ServerCapabilities(
                            tools={"listChanged": False}
                        )
                    )
                )
        except Exception as e:
            logger.error(f"Erreur du serveur stdio: {e}")
            raise
    
    elif args.transport == "http":
        # Mode HTTP (compatible avec claude mcp add --transport http)
        if not HTTP_AVAILABLE:
            logger.error("Les dépendances HTTP ne sont pas installées.")
            logger.error("Installez avec: pip install uvicorn fastapi")
            sys.exit(1)
        
        logger.info(f"Démarrage du serveur MCP Network Tools en mode HTTP...")
        logger.info(f"Serveur disponible sur http://{args.host}:{args.port}")
        
        try:
            # Créer l'application FastAPI personnalisée
            fastapi_app = create_http_app()
            
            # Configuration Uvicorn
            config = uvicorn.Config(
                fastapi_app,
                host=args.host,
                port=args.port,
                log_level="info"
            )
            
            # Démarrer le serveur
            uvicorn_server = uvicorn.Server(config)
            print(f"🚀 Serveur MCP HTTP démarré sur http://{args.host}:{args.port}")
            await uvicorn_server.serve()
            
        except Exception as e:
            logger.error(f"Erreur du serveur HTTP: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())
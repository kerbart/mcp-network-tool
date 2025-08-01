#!/usr/bin/env python3
"""
Serveur MCP Network Tools
Fournit des outils de diagnostic réseau via MCP
"""

import asyncio
import logging
from typing import Any, Sequence
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR,
    ServerCapabilities
)

from .tools.ping import PingTool
from .tools.traceroute import TracerouteTool
from .tools.whois import WhoisTool
from .tools.dns import DNSTool
from .tools.nmap import NmapTool
from .tools.curl import CurlTool
from .tools.netstat import NetstatTool
from .utils.security import SecurityValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-network-tools")

server = Server("network-tools")

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

async def main():
    """Point d'entrée principal du serveur MCP"""
    try:
        logger.info("Starting MCP Network Tools server...")
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Server initialized successfully")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="network-tools",
                    server_version="1.0.0",
                    capabilities=ServerCapabilities(
                        tools={}
                    )
                )
            )
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
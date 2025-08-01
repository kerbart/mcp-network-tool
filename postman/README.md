# MCP Network Tools - Postman Collection

This directory contains Postman collection and environment files for testing the MCP Network Tools server in HTTP transport mode.

## Files

- `MCP-Network-Tools.postman_collection.json` - Main Postman collection with all network tool endpoints
- `MCP-Network-Tools.postman_environment.json` - Environment variables for easy configuration

## Setup

1. **Import the Collection**
   - Open Postman
   - Click "Import" button
   - Select `MCP-Network-Tools.postman_collection.json`

2. **Import the Environment**
   - In Postman, click "Import" button
   - Select `MCP-Network-Tools.postman_environment.json`
   - Set this environment as active (top-right dropdown)

3. **Start the MCP Server in HTTP Transport Mode**
   ```bash
   # Start the server with HTTP transport on port 3000
   python -m mcp run src/server.py --transport http --port 3000
   ```

## Available Requests

### Core MCP Operations
- **Initialize MCP Server** - Initialize the MCP connection
- **List Available Tools** - Get all available network diagnostic tools

### Network Diagnostic Tools
- **Ping Tool** - Test connectivity and measure latency
- **Traceroute Tool** - Trace network route to destination
- **Whois Tool** - Get domain/IP registration information
- **DNS Lookup (nslookup)** - Perform DNS resolution with different record types
- **DNS MX Records** - Get mail exchange records specifically
- **Nmap Port Scan** - Perform secure port scanning
- **HTTP Request (curl)** - Make HTTP GET requests with detailed info
- **HTTP POST Request (curl)** - Make HTTP POST requests
- **Network Connections (netstat)** - Show active network connections
- **Listening Ports (netstat)** - Show listening ports

## Environment Variables

The environment file includes these configurable variables:

- `baseUrl` - Base URL for the MCP server (default: http://localhost:3000)
- `mcpEndpoint` - MCP protocol endpoint (default: /mcp/v1)
- `testHost` - Default host for testing (default: google.com)
- `testUrl` - Default URL for HTTP testing (default: https://httpbin.org)
- `scanHost` - Safe host for port scanning (default: scanme.nmap.org)

## Usage Tips

1. **Start with Initialize** - Always run "Initialize MCP Server" first
2. **List Tools** - Use "List Available Tools" to see all available network diagnostics
3. **Test Safely** - The collection uses safe test hosts like `scanme.nmap.org`
4. **Modify Parameters** - Edit request bodies to test different hosts, ports, or options
5. **Check Responses** - All tools return detailed diagnostic information

## Example Workflow

1. Start the MCP server with HTTP transport
2. Import collection and environment in Postman
3. Run "Initialize MCP Server"
4. Run "List Available Tools" to confirm connection
5. Test individual tools like ping, traceroute, etc.
6. Modify hosts/parameters as needed for your testing

## Security Notes

- The server includes built-in security validation
- Port scanning is limited to safe ranges and known test hosts
- HTTP requests are limited to safe methods (GET, POST, HEAD, OPTIONS)
- All network operations have reasonable timeouts and limits
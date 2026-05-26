# mcp-for-network-engineers

Companion code
for [MCP for Network Engineers: Giving Your AI a Network Toolkit](https://karmatek.io/blog/mcp-for-network-engineers).

A minimal MCP server that gives an AI agent read access to a network — list devices, run show commands, and watch it
reason across multiple routers on its own.

## What's in here

  ```
  inventory.json   # Device inventory (Netmiko connection parameters)
  server.py        # FastMCP server — tools, resources, and a prompt
  ```

The server exposes all three MCP primitives:

- **`list_devices` tool** — returns all devices in the inventory (credentials excluded)
- **`run_command` tool** — runs any show command on a device via SSH
- **`backup_all_configs` tool** — backs up the running config from every device, reporting progress asynchronously
- **`network://inventory` resource** — full inventory as application-managed context for clients that support resources
- **`network://device/{host}` resource template** — parameterized per-device lookup for clients that support resource templates
- **`ospf_audit` prompt** — pre-built OSPF health check workflow for clients that support prompts

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Network devices reachable via SSH (the example uses Cisco CSR1000v in EVE-NG)

## Setup

  ```bash
  git clone git@github.com:Karmatek-Consulting-LLC/mcp-for-network-engineers.git
  cd mcp-for-network-engineers
  uv sync
  ```

Edit `inventory.json` to match your devices:

  ```json
  [
  {
    "host": "172.20.20.1",
    "device_type": "cisco_ios",
    "username": "admin",
    "password": "admin",
    "secret": "admin"
  }
]
  ```

## Running the server

  ```bash
  python server.py
  ```

The server binds to port 8080 and serves the streamable-http transport at `http://localhost:8080/mcp`.

## Connecting a client

Any MCP-compatible client that speaks streamable-http works. The blog post
uses [langchain-mcp-client](https://github.com/guinacio/langchain-mcp-client), a Streamlit app that supports local (
Ollama) and commercial LLM providers.

Point it at:

  ```
  http://localhost:8080/mcp
  ```

For full resources and prompt support, use [MCP Inspector](https://github.com/modelcontextprotocol/inspector) or Claude
Desktop.

## Lab topology

  ```
          ┌─────────────┐
          │  Provider   │
          │   Network   │
          └──┬───┬───┬──┘
             │   │   │
      ┌──────┘   │   └──────┐
      │          │          │
   HQ_CSR    BR1_CSR    BR2_CSR
  172.20.20.1  172.20.21.1  172.20.22.1
      │          │          │
   HQ_SW     BR1_SW     BR2_SW
  ```

OSPF runs between all three sites. The MCP server runs outside the topology, reaching devices over the management
network.
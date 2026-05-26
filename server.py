import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context
from netmiko import ConnectHandler

load_dotenv()

mcp = FastMCP("net-mcp", port=8080)
INVENTORY_FILE = Path(__file__).parent / "inventory.json"


def _load_inventory() -> list[dict]:
    with open(INVENTORY_FILE) as f:
        return json.load(f)


def _get_device(host: str) -> dict | None:
    return next((d for d in _load_inventory() if d["host"] == host), None)


def _run_command(host: str, command: str) -> str:
    device = _get_device(host)
    if not device:
        return f"Device '{host}' not found in inventory."
    with ConnectHandler(**device) as conn:
        return conn.send_command(command)


# Resource: inventory as application-managed context
@mcp.resource("network://inventory")
def get_inventory() -> str:
    """All devices in the network inventory, excluding credentials."""
    devices = [{k: v for k, v in d.items() if k != "password"} for d in _load_inventory()]
    return json.dumps(devices, indent=2)


# Resource template: device lookup by host
@mcp.resource("network://device/{host}")
def get_device_resource(host: str) -> str:
    """Get inventory details for a specific device by IP address."""
    device = _get_device(host)
    if not device:
        return f"Device '{host}' not found in inventory."
    return json.dumps({k: v for k, v in device.items() if k != "password"}, indent=2)


# Tools: model-driven actions
@mcp.tool()
def list_devices() -> list[dict]:
    """List all devices in the network inventory."""
    return [{k: v for k, v in d.items() if k != "password"} for d in _load_inventory()]


@mcp.tool()
def run_command(host: str, command: str) -> str:
    """Run a command on a network device."""
    return _run_command(host, command)


# Prompt: user-invocable workflow template
@mcp.prompt()
def ospf_audit() -> str:
    """Check OSPF adjacency health across all devices in the inventory."""
    return (
        "Use the inventory to find all devices, then check OSPF neighbors on each one. "
        "Report the adjacency state and DR/BDR role for every neighbor relationship. "
        "Flag anything not in FULL state."
    )


# Task example: long-running operation with progress tracking
@mcp.tool()
async def backup_all_configs(ctx: Context) -> str:
    """Backup configurations from all network devices with progress tracking."""
    devices = _load_inventory()
    results = []

    for i, device in enumerate(devices):
        host = device["host"]
        ctx.info(f"Backing up configuration from {host}")
        await ctx.report_progress(i, len(devices))

        try:
            # Simulate async operation
            await asyncio.sleep(0.1)
            config = _run_command(host, "show running-config")
            results.append(f"✓ {host}: {len(config)} bytes")
        except Exception as e:
            results.append(f"✗ {host}: {str(e)}")

    await ctx.report_progress(len(devices), len(devices))
    return "\n".join(results)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

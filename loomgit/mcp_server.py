from mcp.server.fastmcp import FastMCP
from loomgit.agent_tools import search_developer_memory, capture_developer_memory

# Create the MCP server
mcp = FastMCP(
    "loomgit",
    instructions="AI-powered developer context engine - search past decisions, bug fixes, and code changes",
)

# Register tools
mcp.add_tool(search_developer_memory)
mcp.add_tool(capture_developer_memory)

if __name__ == "__main__":
    mcp.run()



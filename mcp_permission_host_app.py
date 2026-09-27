import sys
import json
import gradio as gr
from openai import OpenAI
from mcp_permission_client_base import MCPPermissionClient

class MCPPermissionHostApp(MCPPermissionClient):
    """AI host application with permission enforcement and risk assessment."""

    def __init__(self, server_script: str):
        super().__init__(server_script)
        self.llm_client = OpenAI()
        self.model = "gpt-4o-mini"
        self.conversation_history = []
        self.pending_approval = None
        self.risk_levels = {
            "read_file": "low",
            "write_file": "medium",
            "delete_file": "high",
            "execute_command": "critical"
        }

    async def get_available_tools(self):
        """Get all available tools in OpenAI function calling format with permission info."""
        await self.connect()

        mcp_tools = await self.list_tools()

        openai_tools = []

        for tool in mcp_tools:
            tool_schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or f"Execute {tool.name}",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }

            permission = self.permissions.get(tool.name, "ask")
            risk = self.risk_levels.get(tool.name, "medium")
            tool_schema["function"]["description"] += f" (Permission: {permission}, Risk: {risk})"

            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                schema = tool.inputSchema
                if isinstance(schema, dict):
                    if "properties" in schema:
                        tool_schema["function"]["parameters"]["properties"] = schema["properties"]
                    if "required" in schema and schema["required"]:
                        tool_schema["function"]["parameters"]["required"] = schema["required"]

            openai_tools.append(tool_schema)

        openai_tools.append({
            "type": "function",
            "function": {
                "name": "mcp_list_resources",
                "description": "List all available resources from the MCP server",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        })

        openai_tools.append({
            "type": "function",
            "function": {
                "name": "mcp_read_resource",
                "description": "Read a specific resoure by URI from the MCP server",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "uri": {
                            "type": "string",
                            "description": "The URI of the resource to read (for example, 'file://audit/log')"
                        }
                    },
                    "required": ["uri"]
                }
            }
        })

        #TODO Step 2c: Get Available Tools - Synthetic Prompt Tools
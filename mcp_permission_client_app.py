import sys
import json
import gradio as gr
from mcp_permission_client_base import MCPPermissionClient

class MCPPermissionClientApp(MCPPermissionClient):
    """GUI client application with permission management interface."""

    def __init__(self, server_script: str):
        super().__init__(server_script)
        self.tools_cache = []
        self.prompts_cache = []

    async def gui_list_tools(self):
        """List tools with their permission status for GUI."""
        await self.connect()
        tools = await self.list_tools()

        output = "Available tools:\n\n"
        self.tools_cache = []

        for tool in tools:
            tool_name = tool.name
            permission = self.permissions.get(tool_name, "ask")
            self.tools_cache.append(tool_name)

            output += f"- {tool_name}\n"
            output += f" Permission: {permission.upper()}\n"
            if tool.description:
                output += f" Description: {tool.description}\n"
            output += "\n"

        choices = [f"{name} ({self.permissions.get(name, 'ask')})" for name in self.tools_cache]
        return output, gr.update(choices=choices)

    async def gui_call_tool(self, tool_selection: str, arguments_json: str, approved: bool = False):
        """Call a tool with permission checking for GUI."""
        if not tool_selection:
            return "Please select a tool first"

        tool_name = tool_selection.split(" ("[0])

        try:
            arguments = json.loads(arguments_json) if arguments_json.strip() else {}
        except json.JSONDecodeError as e:
            return f"Invalid JSON in arguments: {str(e)}"
        
        result = await self.call_tool_with_permission(tool_name, arguments, approved=approved)

        if isinstance(result, list) and len(result) > 0:
            content = result[0]
            if hasattr(content, 'text'):
                return content.text
            return str(content)

        return str(result)

    async def gui_list_resources(self):
        """List resources for GUI."""
        await self.connect()
        resources = await self.list_resources()

        output = "Available resources:\n\n"
        for resource in resources:
            output += f"- {resource.uri}\n"
            if resource.name:
                output += f" Name: {resource.name}\n"
            if resource.description:
                output += f" Description: {resource.description}\n"
            output += "\n"

        return output

    async def gui_read_resource(self, uri: str):
        """Read a resource for GUI."""
        if not uri.strip():
            return "Please enter a resource URI"

        await self.connect()
        contents = await self.read_resource(uri)

        if isinstance(contents, list) and len(contents) > 0:
            content = contents[0]
            if hasattr(content, 'text'):
                return content.text
            return str(content)

        return str(contents)

    async def gui_list_prompts(self):
        """List prompts for GUI."""
        await self.connect()
        prompts = await self.list_prompts()

        output = "Avalilable prompts:\n\n"
        self.prompts_cache = []

        for prompt in prompts:
            self.prompts_cache.append(prompt.name)
            output += f"- {prompt.name}\n"
            if prompt.description:
                output += f" Description: {prompt.description}\n"
            if hasattr(prompt, 'arguments') and prompt.arguments:
                args = [arg.name for arg in prompt.arguments]
                output += f" Arguments: {', '.join(args)}\n"
            output += "\n"

        return output, gr.update(choices=self.prompts_cache)

    async def gui_get_prompt(self, prompt_name: str, arguments_json: str):
        """Get a rendered prompt for GUI."""
        if not prompt_name:
            return "Please select a prompt first"

        try:
            arguments = json.loads(arguments_json) if arguments_json.strip() else {}
        except json.JSONDecodeError as e:
            return f"Invalid JSON in arguments: {str(e)}"

        messages = await self.get_prompt(prompt_name, arguments)

        output = f"Prompt: {prompt_name}\n\n"
        for msg in messages:
            role = getattr(msg, 'role', 'unknown')
            content = getattr(msg, 'content', '')
            if hasattr(content, 'text'):
                content = content.text
            output += f"[{role}]: {content}\n\n"

        return output

    async def gui_configure_permission(self, tool_name: str, policy: str):
        """Configure permission for a tool."""
        if not tool_name:
            return "Please enter a tool name"

        if policy not in ["allow", "deny", "ask"]:
            return "Policy must be: allow, deny, or ask"

        self.permissions[tool_name] = policy
        self.save_permissions()

        return f"Permission updated: {tool_name} = {policy}\nPermissions saved to {self.permissions_file}"

    async def gui_view_audit_log(self):
        """View the audit log."""
        if not self.audit_log_file.exists():
            return "No audit log entries yet."

        return self.audit_log_file.read_text()
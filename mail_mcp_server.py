#!/usr/bin/env python3
"""
Mail MCP Server - Enable AI to access macOS Mail emails

Provides four tools:
1. get_email_path - Get file path of a single email
2. get_thread_paths - Get all file paths in an email thread
3. read_email - Parse and read plain text content of a single email
4. read_thread - Parse and read all emails in an entire thread

Run with:
    python3 mail_mcp_server.py
"""

import sys
import json
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from get_email_path import get_email_path as get_single_email_path
from get_thread_paths import get_thread_paths as get_all_thread_paths
from parse_email import parse_email_file

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: mcp library not installed", file=sys.stderr)
    print("Please run: pip install mcp", file=sys.stderr)
    sys.exit(1)


# Create MCP server
app = Server("mail-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools"""
    return [
        Tool(
            name="get_email_path",
            description="Get the absolute path to an email file by RFC Message-ID. "
                       "Message-ID is the unique identifier for an email, formatted like <abc123@example.com>. "
                       "Returns the full path to the email file in the filesystem, which can be used to read email content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "RFC Message-ID, e.g. <abc123@example.com>. Can include or exclude angle brackets."
                    }
                },
                "required": ["message_id"]
            }
        ),
        Tool(
            name="get_thread_paths",
            description="Get file paths of all emails in a thread by Message-ID of any email in the thread. "
                       "An email thread is a group of related emails (such as the original email and all replies). "
                       "Returns a list of paths to all email files in the thread, sorted chronologically, "
                       "useful for analyzing complete email conversations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "RFC Message-ID of any email in the thread."
                    }
                },
                "required": ["message_id"]
            }
        ),
        Tool(
            name="read_email",
            description="Parse and read plain text content of an email by RFC Message-ID. "
                       "Returns structured information including subject, sender, recipient, date, body text, etc., "
                       "enabling AI to analyze email content directly without handling raw .emlx files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "RFC Message-ID, e.g. <abc123@example.com>. Can include or exclude angle brackets."
                    }
                },
                "required": ["message_id"]
            }
        ),
        Tool(
            name="read_thread",
            description="Parse and read all emails in a thread by Message-ID of any email in the thread. "
                       "An email thread is a group of related emails (such as the original email and all replies). "
                       "Returns structured content of all emails in the thread, sorted chronologically, "
                       "enabling AI to analyze complete email conversations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "RFC Message-ID of any email in the thread."
                    }
                },
                "required": ["message_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""

    if name == "get_email_path":
        # Tool 1: Get single email path
        message_id = arguments.get("message_id")

        if not message_id:
            return [TextContent(
                type="text",
                text="Error: Missing message_id parameter"
            )]

        try:
            file_path = get_single_email_path(message_id)

            if file_path:
                result = {
                    "success": True,
                    "message_id": message_id,
                    "file_path": file_path
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]
            else:
                result = {
                    "success": False,
                    "message_id": message_id,
                    "error": "Email file not found",
                    "possible_reasons": [
                        "Message-ID does not exist",
                        "Email file has been deleted",
                        "Email is in a different Mail database version"
                    ]
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]

        except Exception as e:
            result = {
                "success": False,
                "message_id": message_id,
                "error": str(e)
            }
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

    elif name == "get_thread_paths":
        # Tool 2: Get all paths in thread
        message_id = arguments.get("message_id")

        if not message_id:
            return [TextContent(
                type="text",
                text="Error: Missing message_id parameter"
            )]

        try:
            paths = get_all_thread_paths(message_id, include_not_found=False)

            if paths:
                result = {
                    "success": True,
                    "message_id": message_id,
                    "thread_size": len(paths),
                    "file_paths": paths
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]
            else:
                result = {
                    "success": False,
                    "message_id": message_id,
                    "error": "Email thread not found or thread has no email files"
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]

        except Exception as e:
            result = {
                "success": False,
                "message_id": message_id,
                "error": str(e)
            }
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

    elif name == "read_email":
        # Tool 3: Parse and read email content
        message_id = arguments.get("message_id")

        if not message_id:
            return [TextContent(
                type="text",
                text="Error: Missing message_id parameter"
            )]

        try:
            # First get file path
            file_path = get_single_email_path(message_id)

            if not file_path:
                result = {
                    "success": False,
                    "message_id": message_id,
                    "error": "Email file not found"
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]

            # Parse email file
            email_data = parse_email_file(file_path)

            return [TextContent(
                type="text",
                text=json.dumps(email_data, ensure_ascii=False, indent=2)
            )]

        except Exception as e:
            result = {
                "success": False,
                "message_id": message_id,
                "error": str(e)
            }
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

    elif name == "read_thread":
        # Tool 4: Parse and read entire email thread
        message_id = arguments.get("message_id")

        if not message_id:
            return [TextContent(
                type="text",
                text="Error: Missing message_id parameter"
            )]

        try:
            # Get all email paths in thread
            paths = get_all_thread_paths(message_id, include_not_found=False)

            if not paths:
                result = {
                    "success": False,
                    "message_id": message_id,
                    "error": "Email thread not found or thread has no email files"
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]

            # Parse all emails
            emails = []
            for path in paths:
                email_data = parse_email_file(path)
                emails.append(email_data)

            result = {
                "success": True,
                "message_id": message_id,
                "thread_size": len(emails),
                "emails": emails
            }
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        except Exception as e:
            result = {
                "success": False,
                "message_id": message_id,
                "error": str(e)
            }
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

    else:
        return [TextContent(
            type="text",
            text=f"Error: Unknown tool '{name}'"
        )]


async def main():
    """Start MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

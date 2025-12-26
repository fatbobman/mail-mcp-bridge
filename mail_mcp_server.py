#!/usr/bin/env python3
"""
Mail MCP Server - 让 AI 直接访问 macOS Mail 邮件

提供四个工具：
1. get_email_path - 获取单个邮件的文件路径
2. get_thread_paths - 获取邮件线索的所有文件路径
3. read_email - 解析并读取单个邮件的纯文本内容
4. read_thread - 解析并读取整个邮件线索的所有邮件内容

运行方式：
    python3 mail_mcp_server.py
"""

import sys
import json
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from get_email_path import get_email_path as get_single_email_path
from get_thread_paths import get_thread_paths as get_all_thread_paths
from parse_email import parse_email_file

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("错误: 未安装 mcp 库", file=sys.stderr)
    print("请运行: pip install mcp", file=sys.stderr)
    sys.exit(1)


# 创建 MCP 服务器
app = Server("mail-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工具"""
    return [
        Tool(
            name="get_email_path",
            description="通过 RFC Message-ID 获取邮件文件的绝对路径。"
                       "Message-ID 是邮件的唯一标识符，格式如 <abc123@example.com>。"
                       "返回邮件文件在文件系统中的完整路径，可用于读取邮件内容。",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "RFC Message-ID，如 <abc123@example.com>。可以包含或不包含尖括号。"
                    }
                },
                "required": ["message_id"]
            }
        ),
        Tool(
            name="get_thread_paths",
            description="通过邮件线索中任意一封邮件的 Message-ID，获取整个线索中所有邮件的文件路径。"
                       "邮件线索是一组相关的邮件（如原始邮件和所有回复）。"
                       "返回线索中所有邮件文件的路径列表，按时间顺序排列，可用于分析完整的邮件对话。",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "线索中任意一封邮件的 RFC Message-ID。"
                    }
                },
                "required": ["message_id"]
            }
        ),
        Tool(
            name="read_email",
            description="通过 RFC Message-ID 解析并读取邮件的纯文本内容。"
                       "返回邮件的主题、发件人、收件人、日期、正文文本等结构化信息，"
                       "便于 AI 直接分析邮件内容而无需处理原始 .emlx 文件。",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "RFC Message-ID，如 <abc123@example.com>。可以包含或不包含尖括号。"
                    }
                },
                "required": ["message_id"]
            }
        ),
        Tool(
            name="read_thread",
            description="通过邮件线索中任意一封邮件的 Message-ID，解析并读取整个线索的所有邮件内容。"
                       "邮件线索是一组相关的邮件（如原始邮件和所有回复）。"
                       "返回线索中所有邮件的结构化内容，按时间顺序排列，便于 AI 分析完整的邮件对话。",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "线索中任意一封邮件的 RFC Message-ID。"
                    }
                },
                "required": ["message_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""

    if name == "get_email_path":
        # 工具 1: 获取单个邮件路径
        message_id = arguments.get("message_id")

        if not message_id:
            return [TextContent(
                type="text",
                text="错误: 缺少 message_id 参数"
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
                    "error": "未找到对应的邮件文件",
                    "possible_reasons": [
                        "Message-ID 不存在",
                        "邮件文件已被删除",
                        "邮件在其他版本的 Mail 数据库中"
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
        # 工具 2: 获取邮件线索的所有路径
        message_id = arguments.get("message_id")

        if not message_id:
            return [TextContent(
                type="text",
                text="错误: 缺少 message_id 参数"
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
                    "error": "未找到邮件线索或线索中没有邮件文件"
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
        # 工具 3: 解析并读取邮件内容
        message_id = arguments.get("message_id")

        if not message_id:
            return [TextContent(
                type="text",
                text="错误: 缺少 message_id 参数"
            )]

        try:
            # 先获取文件路径
            file_path = get_single_email_path(message_id)

            if not file_path:
                result = {
                    "success": False,
                    "message_id": message_id,
                    "error": "未找到对应的邮件文件"
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]

            # 解析邮件文件
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
        # 工具 4: 解析并读取整个邮件线索
        message_id = arguments.get("message_id")

        if not message_id:
            return [TextContent(
                type="text",
                text="错误: 缺少 message_id 参数"
            )]

        try:
            # 获取线索中所有邮件的路径
            paths = get_all_thread_paths(message_id, include_not_found=False)

            if not paths:
                result = {
                    "success": False,
                    "message_id": message_id,
                    "error": "未找到邮件线索或线索中没有邮件文件"
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]

            # 解析所有邮件
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
            text=f"错误: 未知工具 '{name}'"
        )]


async def main():
    """启动 MCP 服务器"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

#!/usr/bin/env python3
"""
解析 .emlx 邮件文件，提取纯文本内容

专注于纯文本邮件解析，返回结构化数据供 AI 分析
"""

import email
import email.policy
from email.header import decode_header
from pathlib import Path
from typing import Dict, Optional, Any
import base64
import quopri


def decode_header_value(value: str) -> str:
    """
    解码邮件头的编码值（如 =?utf-8?B?...?=）

    Args:
        value: 编码的头值

    Returns:
        解码后的字符串
    """
    if not value:
        return ""

    decoded_parts = []
    for content, encoding in decode_header(value):
        if isinstance(content, bytes):
            if encoding:
                try:
                    decoded_parts.append(content.decode(encoding))
                except (LookupError, UnicodeDecodeError):
                    decoded_parts.append(content.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(content.decode('utf-8', errors='replace'))
        else:
            decoded_parts.append(str(content))

    return ''.join(decoded_parts)


def parse_email_file(file_path: str) -> Dict[str, Any]:
    """
    解析 .emlx 文件，提取纯文本内容

    Args:
        file_path: .emlx 文件的绝对路径

    Returns:
        包含邮件信息的字典：
        {
            "success": True/False,
            "message_id": "...",
            "subject": "...",
            "from": "...",
            "to": "...",
            "date": "...",
            "body_text": "邮件正文",
            "headers": {...},
            "file_path": "..."
        }
    """
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        return {
            "success": False,
            "error": f"文件不存在: {file_path}"
        }

    try:
        # 读取邮件内容
        with open(file_path_obj, 'rb') as f:
            lines = f.readlines()

        # .emlx 文件格式：
        # 第一行：文件大小
        # 第二行开始：邮件原始内容
        # 最后几行：Apple plist 元数据（XML）

        # 跳过第一行（大小信息）
        if len(lines) < 2:
            return {
                "success": False,
                "error": "文件格式无效或为空",
                "file_path": str(file_path)
            }

        # 从第二行开始，找到 plist 开始的位置
        email_lines = []
        for line in lines[1:]:  # 跳过第一行
            line_str = line.decode('utf-8', errors='ignore')
            # 检测 plist 开始标记
            if '<?xml version' in line_str or '<!DOCTYPE plist' in line_str or '<plist version' in line_str:
                break
            email_lines.append(line)

        raw_content = b''.join(email_lines)

        # 解析邮件 - 使用 compat32 处理旧格式，default 处理新格式
        msg = email.message_from_bytes(raw_content, policy=email.policy.compat32)

        # 提取基本头信息
        message_id = msg.get('Message-Id', '')
        subject = decode_header_value(msg.get('Subject', ''))
        from_addr = decode_header_value(msg.get('From', ''))
        to_addr = decode_header_value(msg.get('To', ''))
        date = msg.get('Date', '')

        # 提取所有头信息
        headers = dict(msg.items())

        # 提取正文
        body_text = ""

        if msg.is_multipart():
            # multipart 邮件 - 查找 text/plain 部分
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))

                # 跳过附件
                if 'attachment' in content_disposition:
                    continue

                if content_type == 'text/plain':
                    # 找到纯文本部分
                    payload = part.get_payload(decode=True)
                    if payload:
                        # 尝试解码
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            body_text = payload.decode(charset)
                        except (UnicodeDecodeError, LookupError):
                            # 回退到 utf-8
                            body_text = payload.decode('utf-8', errors='replace')
                    break
        else:
            # 单部分邮件 - 直接提取
            content_type = msg.get_content_type()
            if content_type == 'text/plain':
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    try:
                        body_text = payload.decode(charset)
                    except (UnicodeDecodeError, LookupError):
                        body_text = payload.decode('utf-8', errors='replace')
            else:
                # 非 text/plain，尝试直接获取 payload
                body_text = str(msg.get_payload())

        return {
            "success": True,
            "message_id": message_id,
            "subject": subject,
            "from": from_addr,
            "to": to_addr,
            "date": date,
            "body_text": body_text.strip(),
            "headers": headers,
            "file_path": str(file_path)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"解析失败: {str(e)}",
            "file_path": str(file_path)
        }


def main():
    """命令行测试工具"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python3 parse_email.py <emlx文件路径>")
        print("\n示例:")
        print("  python3 parse_email.py ~/Library/Mail/V10/.../135189.emlx")
        sys.exit(1)

    file_path = sys.argv[1]

    print(f"解析邮件文件: {file_path}\n")

    result = parse_email_file(file_path)

    if result['success']:
        print("✅ 解析成功\n")
        print(f"主题: {result['subject']}")
        print(f"发件人: {result['from']}")
        print(f"收件人: {result['to']}")
        print(f"日期: {result['date']}")
        print(f"Message-ID: {result['message_id']}")
        print("\n" + "="*50)
        print("\n正文内容:")
        print(result['body_text'])
    else:
        print(f"❌ {result['error']}")
        sys.exit(1)


if __name__ == '__main__':
    main()

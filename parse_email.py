#!/usr/bin/env python3
"""
Parse .emlx email files and extract plain text content

Focus on plain text email parsing, return structured data for AI analysis
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
    Decode encoded email header values (e.g. =?utf-8?B?...?=)

    Args:
        value: Encoded header value

    Returns:
        Decoded string
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
    Parse .emlx file and extract plain text content

    Args:
        file_path: Absolute path to .emlx file

    Returns:
        Dictionary containing email information:
        {
            "success": True/False,
            "message_id": "...",
            "subject": "...",
            "from": "...",
            "to": "...",
            "date": "...",
            "body_text": "email body",
            "headers": {...},
            "file_path": "..."
        }
    """
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}"
        }

    try:
        # Read email content
        with open(file_path_obj, 'rb') as f:
            lines = f.readlines()

        # .emlx file format:
        # First line: file size
        # Second line onwards: raw email content
        # Last few lines: Apple plist metadata (XML)

        # Skip first line (size info)
        if len(lines) < 2:
            return {
                "success": False,
                "error": "Invalid file format or empty file",
                "file_path": str(file_path)
            }

        # From second line, find plist start position
        email_lines = []
        for line in lines[1:]:  # Skip first line
            line_str = line.decode('utf-8', errors='ignore')
            # Detect plist start marker
            if '<?xml version' in line_str or '<!DOCTYPE plist' in line_str or '<plist version' in line_str:
                break
            email_lines.append(line)

        raw_content = b''.join(email_lines)

        # Parse email - use compat32 for old format, default for new format
        msg = email.message_from_bytes(raw_content, policy=email.policy.compat32)

        # Extract basic header info
        message_id = msg.get('Message-Id', '')
        subject = decode_header_value(msg.get('Subject', ''))
        from_addr = decode_header_value(msg.get('From', ''))
        to_addr = decode_header_value(msg.get('To', ''))
        date = msg.get('Date', '')

        # Extract all headers
        headers = dict(msg.items())

        # Extract body
        body_text = ""

        if msg.is_multipart():
            # multipart email - find text/plain part
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))

                # Skip attachments
                if 'attachment' in content_disposition:
                    continue

                if content_type == 'text/plain':
                    # Found plain text part
                    payload = part.get_payload(decode=True)
                    if payload:
                        # Try to decode
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            body_text = payload.decode(charset)
                        except (UnicodeDecodeError, LookupError):
                            # Fallback to utf-8
                            body_text = payload.decode('utf-8', errors='replace')
                    break
        else:
            # Single part email - extract directly
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
                # Non text/plain, try to get payload directly
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
            "error": f"Parse failed: {str(e)}",
            "file_path": str(file_path)
        }


def main():
    """Command line test tool"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 parse_email.py <emlx_file_path>")
        print("\nExample:")
        print("  python3 parse_email.py ~/Library/Mail/V10/.../135189.emlx")
        sys.exit(1)

    file_path = sys.argv[1]

    print(f"Parsing email file: {file_path}\n")

    result = parse_email_file(file_path)

    if result['success']:
        print("✅ Parse successful\n")
        print(f"Subject: {result['subject']}")
        print(f"From: {result['from']}")
        print(f"To: {result['to']}")
        print(f"Date: {result['date']}")
        print(f"Message-ID: {result['message_id']}")
        print("\n" + "="*50)
        print("\nBody content:")
        print(result['body_text'])
    else:
        print(f"❌ {result['error']}")
        sys.exit(1)


if __name__ == '__main__':
    main()

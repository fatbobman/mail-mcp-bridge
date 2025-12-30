#!/usr/bin/env python3
"""
Extract attachments from .emlx files and save to a temporary directory

Supports extracting specific attachments from emails for AI analysis
"""

import email
import email.policy
from email.header import decode_header
from pathlib import Path
from typing import Dict, List, Any, Optional
import os
import shutil


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


def get_attachment_base_dir() -> str:
    """
    Get the base directory for saving attachments

    Reads from MAIL_ATTACHMENT_PATH environment variable (defaults to /tmp),
    then appends 'mail-mcp-attachments' subdirectory.

    Returns:
        Full directory path (e.g., /tmp/mail-mcp-attachments)
    """
    base_temp = os.environ.get('MAIL_ATTACHMENT_PATH', '/tmp')
    return os.path.join(base_temp, 'mail-mcp-attachments')


def extract_attachments(
    file_path: str,
    message_id: str,
    filenames: List[str],
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract specific attachments from an .emlx file

    Args:
        file_path: Absolute path to .emlx file
        message_id: RFC Message-ID (used for creating subdirectory)
        filenames: List of attachment filenames to extract
        output_dir: Optional override for base output directory

    Returns:
        Dictionary containing:
        {
            "success": True/False,
            "base_dir": "...",
            "message_dir": "...",
            "extracted": [
                {
                    "filename": "...",
                    "path": "...",
                    "mime_type": "...",
                    "size_bytes": 12345
                }
            ],
            "not_found": ["..."],
            "error": "..." (if failed)
        }
    """
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}"
        }

    if not filenames:
        return {
            "success": False,
            "error": "No filenames specified for extraction"
        }

    try:
        # Read email content
        with open(file_path_obj, 'rb') as f:
            lines = f.readlines()

        # Parse .emlx format
        if len(lines) < 2:
            return {
                "success": False,
                "error": "Invalid file format or empty file"
            }

        # Extract email content (skip size line and plist metadata)
        email_lines = []
        for line in lines[1:]:
            line_str = line.decode('utf-8', errors='ignore')
            if '<?xml version' in line_str or '<!DOCTYPE plist' in line_str or '<plist version' in line_str:
                break
            email_lines.append(line)

        raw_content = b''.join(email_lines)
        msg = email.message_from_bytes(raw_content, policy=email.policy.compat32)

        # Create output directory structure
        base_dir = output_dir or get_attachment_base_dir()
        # Clean message_id for use as directory name (remove angle brackets)
        clean_message_id = message_id.strip('<>')
        message_dir = Path(base_dir) / clean_message_id
        message_dir.mkdir(parents=True, exist_ok=True)

        # Track extraction results
        extracted = []
        not_found = []
        filenames_set = set(filenames)

        # Walk through MIME parts and extract attachments
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition', ''))
            filename = part.get_filename()

            # Check if this is an attachment we're looking for
            is_attachment = (
                'attachment' in content_disposition or
                (filename and content_type not in ['text/plain', 'text/html'])
            )

            if is_attachment and filename:
                # Decode filename if encoded
                decoded_filename = decode_header_value(filename)

                # Check if this filename is in our requested list
                if decoded_filename in filenames_set:
                    # Get attachment payload
                    payload = part.get_payload(decode=True)

                    # If payload is empty or too small, try to find in Attachments directory
                    if not payload or len(payload) < 100:
                        # Try to find attachment in Mail's file system
                        # The attachment is usually in: /path/to/.../Data/{X}/{Y}/{Z}/Attachments/{message_number}/{attachment_id}/{filename}
                        # Path structure: .../Data/{X}/{Y}/{Z}/Messages/{number}.partial.emlx
                        try:
                            messages_dir = file_path_obj.parent
                            attachments_dir = messages_dir.parent / "Attachments"
                            message_num = file_path_obj.stem.replace('.partial', '')

                            # Search in attachment subdirectories
                            if attachments_dir.exists():
                                # Search for the file in any subdirectory
                                for att_dir in attachments_dir.iterdir():
                                    if att_dir.is_dir() and att_dir.name == message_num:
                                        for sub_dir in att_dir.iterdir():
                                            if sub_dir.is_dir():
                                                # Try exact match first
                                                potential_file = sub_dir / decoded_filename
                                                if potential_file.exists():
                                                    # Read from file system
                                                    payload = potential_file.read_bytes()
                                                    break

                                                # Try fuzzy match (Mail replaces / with _ in filenames)
                                                # and other special characters
                                                if not payload:
                                                    # Try different variations
                                                    alt_filename = decoded_filename.replace('/', '_').replace('\\', '_')
                                                    potential_file = sub_dir / alt_filename
                                                    if potential_file.exists():
                                                        payload = potential_file.read_bytes()
                                                        break
                        except Exception:
                            pass  # Fall through to empty payload handling

                    if payload:
                        # Save to file
                        # Sanitize filename for filesystem (replace problematic characters)
                        safe_filename = decoded_filename.replace('/', '_').replace('\\', '_').replace(':', '_')
                        output_path = message_dir / safe_filename
                        with open(output_path, 'wb') as f:
                            f.write(payload)

                        extracted.append({
                            "filename": decoded_filename,  # Report original filename
                            "safe_filename": safe_filename,  # Actual filesystem name
                            "path": str(output_path),
                            "mime_type": content_type,
                            "size_bytes": len(payload)
                        })

                        # Remove from set to track what we've found
                        filenames_set.discard(decoded_filename)

        # Any remaining filenames in the set were not found
        not_found = list(filenames_set)

        return {
            "success": True,
            "base_dir": base_dir,
            "message_dir": str(message_dir),
            "extracted": extracted,
            "not_found": not_found
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Extraction failed: {str(e)}"
        }


def main():
    """Command line test tool"""
    import sys

    if len(sys.argv) < 4:
        print("Usage: python3 extract_attachments.py <emlx_file> <message_id> <filename1> [filename2 ...]")
        print("\nExample:")
        print("  python3 extract_attachments.py ~/Library/Mail/V10/.../email.emlx \\<msg@example.com\\> report.pdf")
        print("\nEnvironment Variables:")
        print("  MAIL_ATTACHMENT_PATH  Base directory for attachments (default: /tmp/mail-mcp-attachments)")
        sys.exit(1)

    emlx_file = sys.argv[1]
    message_id = sys.argv[2]
    filenames = sys.argv[3:]

    print(f"Extracting attachments from: {emlx_file}")
    print(f"Message-ID: {message_id}")
    print(f"Requested files: {', '.join(filenames)}\n")

    result = extract_attachments(emlx_file, message_id, filenames)

    if result['success']:
        print(f"✅ Extraction successful\n")
        print(f"Base directory: {result['base_dir']}")
        print(f"Message directory: {result['message_dir']}")

        if result['extracted']:
            print(f"\n📦 Extracted ({len(result['extracted'])}):")
            for item in result['extracted']:
                print(f"  ✓ {item['filename']}")
                print(f"    Path: {item['path']}")
                print(f"    Type: {item['mime_type']}")
                print(f"    Size: {item['size_bytes']:,} bytes")

        if result['not_found']:
            print(f"\n❌ Not found ({len(result['not_found'])}):")
            for filename in result['not_found']:
                print(f"  - {filename}")
    else:
        print(f"❌ {result['error']}")
        sys.exit(1)


if __name__ == '__main__':
    main()

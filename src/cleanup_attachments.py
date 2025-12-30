#!/usr/bin/env python3
"""
Clean up temporary attachment directories created by extract_attachments

Provides functionality to remove attachment directories for specific messages
"""

import os
from pathlib import Path
from typing import Dict, List, Any


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


def cleanup_attachments(message_ids: List[str], base_dir: str = None) -> Dict[str, Any]:
    """
    Remove attachment directories for specified message IDs

    Args:
        message_ids: List of RFC Message-IDs to clean up
        base_dir: Optional override for base directory

    Returns:
        Dictionary containing:
        {
            "success": True/False,
            "base_dir": "...",
            "cleaned": [
                {
                    "message_id": "...",
                    "path": "...",
                    "files_removed": 3,
                    "size_freed": 12345
                }
            ],
            "not_found": ["..."],
            "error": "..." (if failed)
        }
    """
    base_dir = base_dir or get_attachment_base_dir()
    base_path = Path(base_dir)

    if not base_path.exists():
        return {
            "success": True,
            "base_dir": base_dir,
            "cleaned": [],
            "not_found": message_ids,
            "note": "Base directory does not exist"
        }

    cleaned = []
    not_found = []

    for message_id in message_ids:
        # Clean message_id for use as directory name (remove angle brackets)
        clean_message_id = message_id.strip('<>')
        message_dir = base_path / clean_message_id

        if message_dir.exists() and message_dir.is_dir():
            # Calculate size before deletion
            total_size = 0
            file_count = 0
            for item in message_dir.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
                    file_count += 1

            # Remove directory
            try:
                import shutil
                shutil.rmtree(message_dir)

                cleaned.append({
                    "message_id": message_id,
                    "path": str(message_dir),
                    "files_removed": file_count,
                    "size_freed": total_size
                })
            except Exception as e:
                return {
                    "success": False,
                    "base_dir": base_dir,
                    "error": f"Failed to remove {message_dir}: {str(e)}"
                }
        else:
            not_found.append(message_id)

    return {
        "success": True,
        "base_dir": base_dir,
        "cleaned": cleaned,
        "not_found": not_found
    }


def main():
    """Command line test tool"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 cleanup_attachments.py <message_id1> [message_id2 ...]")
        print("\nExample:")
        print("  python3 cleanup_attachments.py \\<msg@example.com\\>")
        print("\nEnvironment Variables:")
        print("  MAIL_ATTACHMENT_PATH  Base directory for attachments (default: /tmp/mail-mcp-attachments)")
        sys.exit(1)

    message_ids = sys.argv[1:]

    print(f"Cleaning up attachments for {len(message_ids)} message(s)...\n")

    result = cleanup_attachments(message_ids)

    if result['success']:
        print(f"✅ Cleanup successful\n")
        print(f"Base directory: {result['base_dir']}")

        if result['cleaned']:
            print(f"\n🗑️  Cleaned ({len(result['cleaned'])}):")
            for item in result['cleaned']:
                print(f"  ✓ {item['message_id']}")
                print(f"    Path: {item['path']}")
                print(f"    Files removed: {item['files_removed']}")
                print(f"    Space freed: {item['size_freed']:,} bytes ({item['size_freed'] / 1024:.1f} KB)")

        if result.get('note'):
            print(f"\nℹ️  {result['note']}")

        if result['not_found']:
            print(f"\n⚠️  Not found ({len(result['not_found'])}):")
            for message_id in result['not_found']:
                print(f"  - {message_id}")
    else:
        print(f"❌ {result['error']}")
        sys.exit(1)


if __name__ == '__main__':
    main()

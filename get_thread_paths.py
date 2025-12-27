#!/usr/bin/env python3
"""
Get file paths of all emails in a thread

Usage:
    python3 get_thread_paths.py "<message-id@domain.com>"

Or import as module:
    from get_thread_paths import get_thread_paths
    paths = get_thread_paths("<message-id@domain.com>")
"""

import sqlite3
import sys
from pathlib import Path
from get_email_path import get_email_path

# Mail database path
MAIL_DB_PATH = Path.home() / "Library/Mail/V10/MailData/Envelope Index"


def get_conversation_id(message_id):
    """
    Get conversation_id by Message-ID

    Args:
        message_id: RFC Message-ID

    Returns:
        int: conversation_id, or None if not found
    """
    if not message_id.startswith('<'):
        message_id = f'<{message_id}>'

    if not MAIL_DB_PATH.exists():
        raise FileNotFoundError(f"Mail database not found: {MAIL_DB_PATH}")

    conn = sqlite3.connect(str(MAIL_DB_PATH))
    cursor = conn.cursor()

    try:
        query = """
        SELECT m.conversation_id
        FROM messages m
        LEFT JOIN message_global_data mgd ON m.global_message_id = mgd.ROWID
        WHERE mgd.message_id_header = ?
        """
        cursor.execute(query, (message_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()


def get_thread_message_ids(conversation_id):
    """
    Get all Message-IDs for a given conversation_id

    Args:
        conversation_id: Conversation ID

    Returns:
        list: Message-ID list, sorted by time
    """
    if not MAIL_DB_PATH.exists():
        raise FileNotFoundError(f"Mail database not found: {MAIL_DB_PATH}")

    conn = sqlite3.connect(str(MAIL_DB_PATH))
    cursor = conn.cursor()

    try:
        query = """
        SELECT mgd.message_id_header
        FROM messages m
        LEFT JOIN message_global_data mgd ON m.global_message_id = mgd.ROWID
        WHERE m.conversation_id = ?
        ORDER BY m.date_sent ASC
        """

        cursor.execute(query, (conversation_id,))
        results = cursor.fetchall()

        return [row[0] for row in results if row[0]]

    finally:
        conn.close()


def get_thread_paths(message_id, include_not_found=False):
    """
    Get file paths of all emails in a thread

    Args:
        message_id: Message-ID of any email in the thread
        include_not_found: Whether to include emails without files (returns None)

    Returns:
        list: File path list, sorted by email sent time
    """
    # 1. Get conversation_id
    conversation_id = get_conversation_id(message_id)

    if not conversation_id:
        return []

    # 2. Get all Message-IDs in the thread
    message_ids = get_thread_message_ids(conversation_id)

    if not message_ids:
        return []

    # 3. Get file path for each email
    paths = []
    for msg_id in message_ids:
        file_path = get_email_path(msg_id)

        if file_path:
            paths.append(file_path)
        elif include_not_found:
            paths.append(None)

    return paths


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 get_thread_paths.py \"<message-id@domain.com>\"")
        print("\nExample:")
        print("  python3 get_thread_paths.py \"<abc123@example.com>\"")
        sys.exit(1)

    message_id = sys.argv[1]

    # Ensure includes angle brackets
    if not message_id.startswith('<'):
        message_id = f'<{message_id}>'

    print(f"Looking up email thread: {message_id}\n")

    try:
        # First get conversation_id
        conversation_id = get_conversation_id(message_id)

        if not conversation_id:
            print(f"❌ Message-ID not found: {message_id}")
            return 1

        print(f"Found Conversation ID: {conversation_id}")

        # Get all Message-IDs
        message_ids = get_thread_message_ids(conversation_id)
        print(f"Thread contains {len(message_ids)} emails\n")

        # Get all file paths
        paths = get_thread_paths(message_id, include_not_found=True)

        print("=" * 80)
        print(f"📧 Email Thread File Paths (Conversation ID: {conversation_id})")
        print("=" * 80)

        found_count = 0
        for i, (msg_id, path) in enumerate(zip(message_ids, paths), 1):
            print(f"\n[{i}] Message-ID: {msg_id}")
            if path:
                print(f"    Path: {path}")
                found_count += 1
            else:
                print(f"    Path: ❌ File not found")

        print("\n" + "=" * 80)
        print(f"✅ Found {found_count}/{len(message_ids)} email files")
        print("=" * 80)

        # Output plain path list (for script processing)
        if found_count > 0:
            print(f"\n📝 File path list (for scripts):")
            for path in paths:
                if path:
                    print(path)

        return 0

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

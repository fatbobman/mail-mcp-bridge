#!/usr/bin/env python3
"""
Get email file path by Message-ID

Usage:
    python3 get_email_path.py "<message-id@domain.com>"

Or import as module:
    from get_email_path import get_email_path
    file_path = get_email_path("<message-id@domain.com>")
"""

import sqlite3
import sys
import subprocess
from pathlib import Path

# Mail database path
MAIL_DB_PATH = Path.home() / "Library/Mail/V10/MailData/Envelope Index"
MAIL_V10_PATH = Path.home() / "Library/Mail/V10"


def get_email_path(message_id):
    """
    Get email file path by RFC Message-ID

    Args:
        message_id: RFC Message-ID, e.g. <abc@example.com>

    Returns:
        str: Absolute path to email file, or None if not found
    """
    # Ensure Message-ID includes angle brackets
    if not message_id.startswith('<'):
        message_id = f'<{message_id}>'

    if not MAIL_DB_PATH.exists():
        raise FileNotFoundError(f"Mail database not found: {MAIL_DB_PATH}")

    # Connect to database
    conn = sqlite3.connect(str(MAIL_DB_PATH))
    cursor = conn.cursor()

    try:
        # Query email info - KEY: use ROWID, not remote_id
        query = """
        SELECT
            m.ROWID as message_rowid,
            mb.url as mailbox_url
        FROM messages m
        LEFT JOIN message_global_data mgd ON m.global_message_id = mgd.ROWID
        LEFT JOIN mailboxes mb ON m.mailbox = mb.ROWID
        WHERE mgd.message_id_header = ?
        """

        cursor.execute(query, (message_id,))
        result = cursor.fetchone()

        if not result:
            return None

        message_rowid, mailbox_url = result

        if not message_rowid or not mailbox_url:
            return None

        # Parse mailbox URL
        # Format: imap://ACCOUNT-UUID/MAILBOX-PATH
        if not mailbox_url.startswith('imap://'):
            return None

        import urllib.parse
        parts = mailbox_url.replace('imap://', '').split('/', 1)
        account_uuid = parts[0]
        mailbox_path = urllib.parse.unquote(parts[1]) if len(parts) > 1 else ''

        # Build mailbox directory path
        mbox_path = MAIL_V10_PATH / account_uuid

        for part in mailbox_path.split('/'):
            if part:
                mbox_path = mbox_path / f"{part}.mbox"

        # Find .emlx file - use ROWID, not remote_id
        if mbox_path.exists():
            # Use find command to locate file
            result = subprocess.run(
                ['find', str(mbox_path), '-name', f'{message_rowid}*.emlx'],
                capture_output=True,
                text=True,
                timeout=10
            )

            files = [f for f in result.stdout.strip().split('\n') if f]
            if files:
                return files[0]

        return None

    finally:
        conn.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 get_email_path.py \"<message-id@domain.com>\"")
        print("\nExample:")
        print("  python3 get_email_path.py \"<abc123@example.com>\"")
        sys.exit(1)

    message_id = sys.argv[1]

    print(f"Looking up Message-ID: {message_id}")

    try:
        file_path = get_email_path(message_id)

        if file_path:
            print(f"\n✅ Found email file:")
            print(file_path)
            return 0
        else:
            print(f"\n❌ Email file not found")
            print("Possible reasons:")
            print("  1. Message-ID does not exist")
            print("  2. Email file has been deleted")
            print("  3. Email is in a different Mail database version")
            return 1

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease check:")
        print("  1. Mail database version is V10")
        print(f"  2. Run: ls ~/Library/Mail/")
        return 1
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

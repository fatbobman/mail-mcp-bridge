#!/usr/bin/env python3
"""
通过 Message-ID 获取邮件文件路径

用法：
    python3 get_email_path.py "<message-id@domain.com>"

或作为模块导入：
    from get_email_path import get_email_path
    file_path = get_email_path("<message-id@domain.com>")
"""

import sqlite3
import sys
import subprocess
from pathlib import Path

# Mail 数据库路径
MAIL_DB_PATH = Path.home() / "Library/Mail/V10/MailData/Envelope Index"
MAIL_V10_PATH = Path.home() / "Library/Mail/V10"


def get_email_path(message_id):
    """
    通过 RFC Message-ID 获取邮件文件路径

    Args:
        message_id: RFC Message-ID，如 <abc@example.com>

    Returns:
        str: 邮件文件的绝对路径，如果找不到返回 None
    """
    # 确保 Message-ID 包含尖括号
    if not message_id.startswith('<'):
        message_id = f'<{message_id}>'

    if not MAIL_DB_PATH.exists():
        raise FileNotFoundError(f"Mail 数据库不存在: {MAIL_DB_PATH}")

    # 连接数据库
    conn = sqlite3.connect(str(MAIL_DB_PATH))
    cursor = conn.cursor()

    try:
        # 查询邮件信息 - 关键：使用 ROWID，不是 remote_id
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

        # 解析 mailbox URL
        # 格式: imap://ACCOUNT-UUID/MAILBOX-PATH
        if not mailbox_url.startswith('imap://'):
            return None

        import urllib.parse
        parts = mailbox_url.replace('imap://', '').split('/', 1)
        account_uuid = parts[0]
        mailbox_path = urllib.parse.unquote(parts[1]) if len(parts) > 1 else ''

        # 构建邮箱目录路径
        mbox_path = MAIL_V10_PATH / account_uuid

        for part in mailbox_path.split('/'):
            if part:
                mbox_path = mbox_path / f"{part}.mbox"

        # 查找 .emlx 文件 - 使用 ROWID，不是 remote_id
        if mbox_path.exists():
            # 使用 find 命令查找文件
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
        print("用法: python3 get_email_path.py \"<message-id@domain.com>\"")
        print("\n示例:")
        print("  python3 get_email_path.py \"<abc123@example.com>\"")
        sys.exit(1)

    message_id = sys.argv[1]

    print(f"查找 Message-ID: {message_id}")

    try:
        file_path = get_email_path(message_id)

        if file_path:
            print(f"\n✅ 找到邮件文件:")
            print(file_path)
            return 0
        else:
            print(f"\n❌ 未找到对应的邮件文件")
            print("可能原因:")
            print("  1. Message-ID 不存在")
            print("  2. 邮件文件已被删除")
            print("  3. 邮件在其他版本的 Mail 数据库中")
            return 1

    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        print("\n请检查:")
        print("  1. Mail 数据库版本是否为 V10")
        print(f"  2. 运行: ls ~/Library/Mail/")
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

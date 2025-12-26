#!/usr/bin/env python3
"""
获取邮件线索中所有邮件的文件路径

用法：
    python3 get_thread_paths.py "<message-id@domain.com>"

或作为模块导入：
    from get_thread_paths import get_thread_paths
    paths = get_thread_paths("<message-id@domain.com>")
"""

import sqlite3
import sys
from pathlib import Path
from get_email_path import get_email_path

# Mail 数据库路径
MAIL_DB_PATH = Path.home() / "Library/Mail/V10/MailData/Envelope Index"


def get_conversation_id(message_id):
    """
    通过 Message-ID 获取 conversation_id

    Args:
        message_id: RFC Message-ID

    Returns:
        int: conversation_id，如果找不到返回 None
    """
    if not message_id.startswith('<'):
        message_id = f'<{message_id}>'

    if not MAIL_DB_PATH.exists():
        raise FileNotFoundError(f"Mail 数据库不存在: {MAIL_DB_PATH}")

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
    获取指定 conversation_id 的所有邮件的 Message-ID

    Args:
        conversation_id: 对话 ID

    Returns:
        list: Message-ID 列表，按时间排序
    """
    if not MAIL_DB_PATH.exists():
        raise FileNotFoundError(f"Mail 数据库不存在: {MAIL_DB_PATH}")

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
    获取邮件线索中所有邮件的文件路径

    Args:
        message_id: 线索中任意一封邮件的 Message-ID
        include_not_found: 是否包含未找到文件的邮件（返回 None）

    Returns:
        list: 文件路径列表，按邮件发送时间排序
    """
    # 1. 获取 conversation_id
    conversation_id = get_conversation_id(message_id)

    if not conversation_id:
        return []

    # 2. 获取线索中所有邮件的 Message-ID
    message_ids = get_thread_message_ids(conversation_id)

    if not message_ids:
        return []

    # 3. 获取每个邮件的文件路径
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
        print("用法: python3 get_thread_paths.py \"<message-id@domain.com>\"")
        print("\n示例:")
        print("  python3 get_thread_paths.py \"<abc123@example.com>\"")
        sys.exit(1)

    message_id = sys.argv[1]

    # 确保包含尖括号
    if not message_id.startswith('<'):
        message_id = f'<{message_id}>'

    print(f"查找邮件线索: {message_id}\n")

    try:
        # 先获取 conversation_id
        conversation_id = get_conversation_id(message_id)

        if not conversation_id:
            print(f"❌ 未找到 Message-ID: {message_id}")
            return 1

        print(f"找到 Conversation ID: {conversation_id}")

        # 获取所有邮件的 Message-ID
        message_ids = get_thread_message_ids(conversation_id)
        print(f"线索包含 {len(message_ids)} 封邮件\n")

        # 获取所有文件路径
        paths = get_thread_paths(message_id, include_not_found=True)

        print("=" * 80)
        print(f"📧 邮件线索文件路径 (Conversation ID: {conversation_id})")
        print("=" * 80)

        found_count = 0
        for i, (msg_id, path) in enumerate(zip(message_ids, paths), 1):
            print(f"\n[{i}] Message-ID: {msg_id}")
            if path:
                print(f"    路径: {path}")
                found_count += 1
            else:
                print(f"    路径: ❌ 未找到文件")

        print("\n" + "=" * 80)
        print(f"✅ 找到 {found_count}/{len(message_ids)} 个邮件文件")
        print("=" * 80)

        # 输出纯路径列表（便于脚本处理）
        if found_count > 0:
            print(f"\n📝 文件路径列表（可用于脚本）：")
            for path in paths:
                if path:
                    print(path)

        return 0

    except FileNotFoundError as e:
        print(f"❌ 错误: {e}")
        return 1
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
